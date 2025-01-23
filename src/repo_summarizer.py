import os
import time
from collections import defaultdict
from typing import Any, Callable, Dict

from dotenv import load_dotenv
from langchain.llms.base import LLM
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders.github import GithubFileLoader
from langchain_google_genai import ChatGoogleGenerativeAI


class ModelRateLimiter:
    def __init__(self, requests_per_minute: int = 15):
        self.requests_per_minute = requests_per_minute
        self.interval = 60.0 / requests_per_minute  # Time between requests in seconds
        self.last_request_time: Dict[str, float] = defaultdict(float)
        self.request_counts: Dict[str, int] = defaultdict(int)
        self.window_start: Dict[str, float] = defaultdict(float)

    def _wait_if_needed(self, model: str) -> None:
        current_time = time.time()
        
        # Reset window if a minute has passed
        if current_time - self.window_start[model] >= 60:
            self.request_counts[model] = 0
            self.window_start[model] = current_time

        # Check if we've hit the rate limit
        if self.request_counts[model] >= self.requests_per_minute:
            wait_time = 60 - (current_time - self.window_start[model])
            if wait_time > 0:
                time.sleep(wait_time)
                self.request_counts[model] = 0
                self.window_start[model] = time.time()
        
        # Ensure minimum interval between requests
        elapsed = current_time - self.last_request_time[model]
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)

    def wrap_sync(self, func: Callable, model: str) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            self._wait_if_needed(model)
            try:
                result = func(*args, **kwargs)
                self.last_request_time[model] = time.time()
                self.request_counts[model] += 1
                return result
            except Exception as e:
                raise e
        return wrapper

    async def wrap_async(self, func: Callable, model: str) -> Callable:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            self._wait_if_needed(model)
            try:
                result = await func(*args, **kwargs)
                self.last_request_time[model] = time.time()
                self.request_counts[model] += 1
                return result
            except Exception as e:
                raise e
        return wrapper


class GitHubProjectSummarizer:
    def __init__(self, llm:LLM):
        
        self.llm=llm
        github_project_summarizer = """
You are an advanced AI specializing in analyzing software and Data Science Project repositories. Your task is to thoroughly examine the contents of a GitHub project, including its README and relevant code files, to generate a detailed summary that:

Technology Stack: Clearly identifies the technologies, frameworks, libraries, and languages used in the project. 

Problem Statement: Explains the primary problem or challenge the project aims to address. Highlight the unique aspects of the solution.

Core Strengths: Describes the notable features, innovative design choices, and any areas where the project excels. Include its architecture and design patterns if identifiable.

Key Features: List the project's most compelling functionalities or aspects that make it stand out, particularly in a professional context, such as an interview setting.

README Insights: Extracts and contextualizes critical information from the README file, including the purpose, usage instructions, and contributors.

Code Analysis: Delves into the codebase to identify best practices, complexity levels

Praise the project: just do it. 

Instructions: 
* Use markdown
* Use repo name as markdown heading
* rest of the content here

(Write/boast as a bigmouth)

The output should be in a polished, professional markdown format, suitable for documentation or as a concise presentation.
project--\n
{project_str}

        """

        self.prompt_template = PromptTemplate(template=github_project_summarizer)
        self.chain = self.prompt_template | self.llm


    def summarize_repository(self, repo_content: str) -> str:
        """Main function to summarize a GitHub repository."""
        return self.chain.invoke({"project_str": repo_content})

    async def asummarize_repository(self, repo_content: str) -> str:
        """Main function to summarize a GitHub repository."""
        return await self.chain.ainvoke({"project_str": repo_content})
    
    
    def summarize_multiple_repositories(self, repos: list) -> list:
        """Summarize multiple repositories and return a list of dictionaries.
        Args:
            repos (list): A list of repo_contents
        Returns:
            list: A list of dictionaries with 'repo'
        """
        summaries = []
        for n,repo_content in enumerate(repos,1):
            try:

                summary = self.summarize_repository(repo_content=repo_content)
                summaries.append({"repo_name": repo_name, "summary": summary})
            except Exception as e:
                summaries.append({"repo_name": n, "summary": f"Error: {e}"})
        return summaries



# Usage example
if __name__ == "__main__":
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-8b")
    summarizer = GitHubProjectSummarizer(llm=llm)

    repo_name = 'tikendraw/cli-ai'
    repo_creator = 'tikendraw'
    allowed_extensions = ['.md', '.py']  

    repos_to_summarize = [
    ]


    try:
        summaries = summarizer.summarize_multiple_repositories(repos=repos_to_summarize, allowed_extensions=allowed_extensions)
        for summary in summaries:
            print(f"Repository: {summary['repo']}")
            print(f"Summary: {summary['summary']}\n")
            print('--------------\n')
    except Exception as e:
        print(f"Error: {e}")

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
        self.rate_limiter = ModelRateLimiter(requests_per_minute=requests_per_minute)
        
        self.prompt_template = """
You are an advanced AI specializing in analyzing software and Data Science Project repositories. Your task is to thoroughly examine the contents of a GitHub project, including its README and relevant code files, to generate a detailed summary that:

Technology Stack: Clearly identifies the technologies, frameworks, libraries, and languages used in the project. 

Problem Statement: Explains the primary problem or challenge the project aims to address. Highlight the unique aspects of the solution.

Core Strengths: Describes the notable features, innovative design choices, and any areas where the project excels. Include its architecture and design patterns if identifiable, How is this project helpful/good. How does it solves problem.

Key Features: List the project's most compelling functionalities or aspects that make it stand out, particularly in a professional context, such as an interview setting.

README Insights: Extracts and contextualizes critical information from the README file, including the purpose, usage instructions, and contributors.

Code Analysis: Delves into the codebase to identify best practices, complexity levels


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
        """Synchronously summarize a GitHub repository with fallback support."""
        for model in self.model_list:
            try:
                wrapped_completion = self.rate_limiter.wrap_sync(self._completion, model)
                response = wrapped_completion(
                    model=model,
                    messages=[{"role": "user", "content": self._format_prompt(repo_content)}],
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e:
                if model == self.model_list[-1]:  # If this was the last model to try
                    raise Exception(f"All models failed. Last error: {str(e)}")
                continue  # Try next model if this one failed

    async def asummarize_repository(self, repo_content: str) -> str:
        """Asynchronously summarize a GitHub repository with fallback support."""
        for model in self.model_list:
            try:
                wrapped_acompletion = await self.rate_limiter.wrap_async(self._acompletion, model)
                response = await wrapped_acompletion(
                    model=model,
                    messages=[{"role": "user", "content": self._format_prompt(repo_content)}],
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e:
                if model == self.model_list[-1]:  # If this was the last model to try
                    raise Exception(f"All models failed. Last error: {str(e)}")
                continue  # Try next model if this one failed

    def summarize_multiple_repositories(self, repos: list) -> list:
        """Summarize multiple repositories synchronously with fallback support.
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
        """Summarize multiple repositories asynchronously with fallback support.
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


# Usage example for LiteLLM version
if __name__ == "__main__":
    # Original example
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-8b")
    summarizer = GitHubProjectSummarizer(llm=llm)

    # New LiteLLM example
    model_list = ["gpt-4", "claude-3-sonnet", "gemini-pro"]  # Fallback order
    litellm_summarizer = LiteLLMProjectSummarizer(model_list=model_list)

    repo_name = 'tikendraw/cli-ai'
    repo_creator = 'tikendraw'
    allowed_extensions = ['.md', '.py']

    repos_to_summarize = []

    try:
        # Using the LiteLLM version
        summaries = litellm_summarizer.summarize_multiple_repositories(repos=repos_to_summarize)
        for summary in summaries:
            print(f"Repository: {summary['repo_name']}")
            print(f"Summary: {summary['summary']}\n")
            print('--------------\n')
    except Exception as e:
        print(f"Error: {e}")
