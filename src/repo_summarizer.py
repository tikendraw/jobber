import asyncio
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar

from src.llm_base import LLMBase, TimedSemaphore


class LiteLLMProjectSummarizer(LLMBase):
    def __init__(self, model_list: list[str], requests_per_minute: int = 15):
        super().__init__(model_list, requests_per_minute)
        
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
        """Format the prompt with project content"""
        return self.prompt_template.format(project_str=project_str)

    async def _process_response(self, response: Any, *args, **kwargs) -> str:
        """Process LLM response into summary"""
        return response.choices[0].message.content

    async def summarize_repository(self, repo_content: str) -> str:
        """Summarize a single repository asynchronously"""
        prompt = self._format_prompt(repo_content)
        return await self._execute_with_fallback(prompt=prompt)

    def summarize_repository_sync(self, repo_content: str) -> str:
        """Synchronous version of repository summarization"""
        return self.execute_sync(
            prompt=self._format_prompt(repo_content)
        )

    async def summarize_multiple_repositories(self, repos: list) -> list:
        """Summarize multiple repositories asynchronously"""
        summaries = []
        for n, repo_content in enumerate(repos, 1):
            try:
                summary = await self.summarize_repository(repo_content)
                summaries.append({"repo_num": n, "summary": summary})
            except Exception as e:
                summaries.append({"repo_num": n, "summary": f"Error: {e}"})
        return summaries

    def summarize_multiple_repositories_sync(self, repos: list) -> list:
        """Synchronous version of multiple repository summarization"""
        return self.execute_sync(
            self.summarize_multiple_repositories,
            repos
        )

    def __del__(self):
        """Ensure semaphores are stopped when the object is deleted."""
        for semaphore in self._model_semaphores.values():
            semaphore.stop()