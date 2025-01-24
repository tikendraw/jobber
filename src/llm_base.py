import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional


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
        self._model_semaphores: Dict[str, TimedSemaphore] = {}
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

    async def _execute_with_fallback(self, 
                                   prompt: str,
                                   temperature: float = 0.7,
                                   *args,
                                   **kwargs) -> Any:
        """Execute LLM call with fallback support and rate limiting"""
        for model in self.model_list:
            try:
                async with self._model_semaphores[model]:
                    response = await self._acompletion(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature
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