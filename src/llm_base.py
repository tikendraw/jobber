import asyncio
import os
from abc import ABC, abstractmethod
from base64 import b64encode
from pathlib import Path
from typing import Any, Dict, List, Optional, OrderedDict, Union


class TimedSemaphore:
    """Rate limiting semaphore that replenishes at fixed intervals"""
    def __init__(self, limit: int, interval: float = 60.0):
        self.limit = limit
        self.interval = interval
        self._semaphore = asyncio.Semaphore(limit)
        self._replenish_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    async def _replenish(self):
        try:
            while not self._stop_event.is_set():
                await asyncio.sleep(self.interval)
                for _ in range(self.limit):
                    try:
                        self._semaphore.release()
                    except ValueError:
                        break
        except asyncio.CancelledError:
            pass

    def start(self):
        if self._replenish_task is None:
            self._stop_event.clear()
            self._replenish_task = asyncio.create_task(self._replenish())

    def stop(self):
        if self._replenish_task:
            self._stop_event.set()
            self._replenish_task.cancel()
            self._replenish_task = None

    async def acquire(self):
        await self._semaphore.acquire()

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class LLMBase(ABC):
    """Base class for LLM-based operations with rate limiting and model fallback"""
    
    def __init__(self, model_list: list[str], requests_per_minute: int = 15):
        """Initialize with model fallbacks and rate limiting
        
        Args:
            model_list (list[str]): List of model names to try in order
            requests_per_minute (int): Maximum requests per minute per model
        """
        from litellm import acompletion, completion
        
        self.model_list = model_list
        self._completion = completion
        self._acompletion = acompletion
        
        # Create rate limiters for each model
        self._model_semaphores: Dict[str, TimedSemaphore] = OrderedDict()
        for model in model_list:
            semaphore = TimedSemaphore(limit=requests_per_minute, interval=60.0)
            semaphore.start()
            self._model_semaphores[model] = semaphore

    @abstractmethod
    def _format_prompt(self, *args, **kwargs) -> str:
        """Format the prompt template with provided information"""
        pass

    @abstractmethod
    async def _process_response(self, response: Any, *args, **kwargs) -> Any:
        """Process the LLM response into desired format"""
        pass

    def _encode_image_to_base64(self, image_path: str) -> str:
        """Convert image to base64 string"""
        with open(image_path, "rb") as image_file:
            return b64encode(image_file.read()).decode('utf-8')

    def _format_vision_messages(self, text_content: str, image_paths: List[str]) -> List[Dict]:
        """Format messages for vision models including images"""
        messages = []
        
        # Add text content
        content = [{"type": "text", "text": text_content}]
        
        # Add images
        for image_path in image_paths:
            if image_path.startswith("data:image"):  # Already base64
                image_url = image_path
            else:  # File path
                base64_image = self._encode_image_to_base64(image_path)
                image_url = f"data:image/jpeg;base64,{base64_image}"
                
            content.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })
            
        messages.append({"role": "user", "content": content})
        return messages

    async def _execute_with_fallback(self, 
                                   prompt: str,
                                   temperature: float = 0.7,
                                   image_paths: List[str] = None,
                                   *args,
                                   **kwargs) -> Any:
        """Execute LLM call with fallback support and rate limiting"""
        for model in self.model_list:
            try:
                async with self._model_semaphores[model]:
                    if image_paths:
                        messages = self._format_vision_messages(prompt, image_paths)
                    else:
                        messages = [{"role": "user", "content": prompt}]
                        
                    response = await self._acompletion(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        response_format=kwargs.pop("response_format", None),
                    )
                    
                    try:
                        return await self._process_response(response, *args, **kwargs)
                    except Exception as e:
                        if model == self.model_list[-1]:
                            raise Exception(f"Failed to process response with all models. Error: {str(e)}")
                        continue

            except Exception as e:
                if model == self.model_list[-1]:
                    raise Exception(f"All models failed. Last error: {str(e)}")
                continue

    def execute_sync(self, *args, **kwargs) -> Any:
        """Synchronous wrapper for LLM execution"""
        return asyncio.run(self._execute_with_fallback(*args, **kwargs))

    def __del__(self):
        """Cleanup rate limiters"""
        for semaphore in self._model_semaphores.values():
            semaphore.stop() 