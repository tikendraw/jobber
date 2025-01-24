import asyncio
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar

class TimedSemaphore:
    """
    A semaphore that automatically replenishes its resources at a specified interval.
    
    Allows controlling the rate of operations by limiting the number of acquisitions 
    within a given time interval.
    """
    def __init__(self, limit: int, interval: float = 60.0):
        """
        Initialize the TimedSemaphore.
        
        Args:
            limit (int): Maximum number of resources available in each interval.
            interval (float, optional): Time interval in seconds. Defaults to 60 seconds.
        """
        self.limit = limit
        self.interval = interval
        self._semaphore = asyncio.Semaphore(limit)
        self._replenish_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    async def _replenish(self) -> None:
        """
        Continuously replenish the semaphore resources at the specified interval.
        """
        try:
            while not self._stop_event.is_set():
                await asyncio.sleep(self.interval)
                
                # Release resources up to the limit
                for _ in range(self.limit):
                    try:
                        self._semaphore.release()
                    except ValueError:
                        # Ignore if the semaphore is already at its maximum
                        break
        except asyncio.CancelledError:
            # Handle task cancellation gracefully
            pass

    def start(self) -> None:
        """
        Start the replenishment task.
        """
        if self._replenish_task is None:
            self._stop_event.clear()
            self._replenish_task = asyncio.create_task(self._replenish())

    def stop(self) -> None:
        """
        Stop the replenishment task.
        """
        if self._replenish_task:
            self._stop_event.set()
            self._replenish_task.cancel()
            self._replenish_task = None

    async def acquire(self) -> None:
        """
        Acquire a resource from the semaphore.
        
        Blocks if no resources are available.
        """
        await self._semaphore.acquire()

    async def __aenter__(self) -> 'TimedSemaphore':
        """
        Context manager entry point for async with statement.
        
        Returns:
            TimedSemaphore: The semaphore instance.
        """
        await self.acquire()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Context manager exit point. 
        
        In this implementation, we don't need to release the semaphore 
        as the rate limiting handles it automatically.
        """
        pass


class LiteLLMProjectSummarizer:
    def __init__(self, model_list: list[str], requests_per_minute: int = 15):
        """Initialize with a list of model names for fallback
        Args:
            model_list (list[str]): List of model names to try in order (e.g. ["gpt-4", "claude-3-sonnet"])
            requests_per_minute (int): Maximum number of requests per minute per model
        """
        from litellm import acompletion, completion
        
        self.model_list = model_list
        self._completion = completion
        self._acompletion = acompletion
        
        # Create a timed semaphore for each model
        self._model_semaphores: Dict[str, TimedSemaphore] = {}
        for model in model_list:
            semaphore = TimedSemaphore(limit=requests_per_minute, interval=60.0)
            semaphore.start()
            self._model_semaphores[model] = semaphore

        self.prompt_template = """
You are an advanced AI specializing in analyzing software and Data Science Project repositories. Your task is to thoroughly examine the contents of a GitHub project, including its README and relevant code files, to generate a detailed summary that:
About the project: Provides a concise overview of the project's purpose, goals, and objectives. 
README Insights: Extracts and contextualizes critical information from the README file, including the purpose, usage instructions, and contributors.
Problem Statement: Explains the primary problem or challenge the project aims to address. Highlight the unique aspects of the solution.

Technology Stack: Clearly identifies the technologies, frameworks, libraries, and languages used in the project. 

Core Strengths: Describes the notable features, innovative design choices, and any areas where the project excels. Include its architecture and design patterns if identifiable, How is this project helpful/good. How does it solves problem.

Key Features: List the project's most compelling functionalities or aspects that make it stand out, particularly in a professional context, such as an interview setting.

Code Analysis: Delves into the codebase to identify best practices, complexity levels

Abstractive Summarization: Provide a concise, yet comprehensive summary of the project, without being overly verbose, like ,e.g. uses cache for faster ops, and how it solves the problem.
Praise the project: just do it. 

Instructions: 
* Use markdown
* Use repo name as markdown heading
* rest of the content here

(Write/boast as professional, throw techwords and words that are used in resumes.)

The output should be in a polished, professional markdown format, suitable for documentation or as a concise presentation.
project--
{project_str}
"""

    def _format_prompt(self, project_str: str) -> str:
        return self.prompt_template.format(project_str=project_str)

    def summarize_repository(self, repo_content: str) -> str:
        """Synchronously summarize a GitHub repository with fallback support and rate limiting."""
        for model in self.model_list:
            try:
                # Synchronously acquire the semaphore
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self._model_semaphores[model].acquire())

                try:
                    response = self._completion(
                        model=model,
                        messages=[{"role": "user", "content": self._format_prompt(repo_content)}],
                        temperature=0.7
                    )
                    return response.choices[0].message.content
                except Exception as completion_error:
                    if model == self.model_list[-1]:  # If this was the last model to try
                        raise Exception(f"All models failed. Last error: {str(completion_error)}")
                    continue  # Try next model if this one failed
            except Exception as semaphore_error:
                if model == self.model_list[-1]:  # If this was the last model to try
                    raise Exception(f"Semaphore error: {str(semaphore_error)}")
                continue  # Try next model if semaphore acquisition failed

    async def asummarize_repository(self, repo_content: str) -> str:
        """Asynchronously summarize a GitHub repository with fallback support and rate limiting."""
        for model in self.model_list:
            try:
                # Asynchronously acquire the semaphore
                await self._model_semaphores[model].acquire()

                try:
                    response = await self._acompletion(
                        model=model,
                        messages=[{"role": "user", "content": self._format_prompt(repo_content)}],
                        temperature=0.7
                    )
                    return response.choices[0].message.content
                except Exception as completion_error:
                    if model == self.model_list[-1]:  # If this was the last model to try
                        raise Exception(f"All models failed. Last error: {str(completion_error)}")
                    continue  # Try next model if this one failed
            except Exception as semaphore_error:
                if model == self.model_list[-1]:  # If this was the last model to try
                    raise Exception(f"Semaphore error: {str(semaphore_error)}")
                continue  # Try next model if semaphore acquisition failed

    def summarize_multiple_repositories(self, repos: list) -> list:
        """Synchronously summarize multiple repositories with fallback support.
        Args:
            repos (list): A list of repo_contents
        Returns:
            list: A list of dictionaries with 'repo_name' and 'summary'
        """
        summaries = []
        for n, repo_content in enumerate(repos, 1):
            try:
                summary = self.summarize_repository(repo_content=repo_content)
                summaries.append({"repo_name": n, "summary": summary})
            except Exception as e:
                summaries.append({"repo_name": n, "summary": f"Error: {e}"})
        return summaries

    async def asummarize_multiple_repositories(self, repos: list) -> list:
        """Asynchronously summarize multiple repositories with fallback support.
        Args:
            repos (list): A list of repo_contents
        Returns:
            list: A list of dictionaries with 'repo_name' and 'summary'
        """
        summaries = []
        for n, repo_content in enumerate(repos, 1):
            try:
                summary = await self.asummarize_repository(repo_content=repo_content)
                summaries.append({"repo_name": n, "summary": summary})
            except Exception as e:
                summaries.append({"repo_name": n, "summary": f"Error: {e}"})
        return summaries

    def __del__(self):
        """Ensure semaphores are stopped when the object is deleted."""
        for semaphore in self._model_semaphores.values():
            semaphore.stop()