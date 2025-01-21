import os

from dotenv import load_dotenv
from langchain.llms.base import LLM
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders.github import GithubFileLoader
from langchain_google_genai import ChatGoogleGenerativeAI


class GitHubProjectSummarizer:
    def __init__(self, llm:LLM):
        
        self.llm=llm
        github_project_summarizer = """
You are an advanced AI specializing in analyzing software and Data Science Project repositories. Your task is to thoroughly examine the contents of a GitHub project, including its README and relevant code files, to generate a detailed summary that:

Technology Stack: Clearly identifies the technologies, frameworks, libraries, and languages used in the project. Specify their versions if available.

Problem Statement: Explains the primary problem or challenge the project aims to address. Highlight the unique aspects of the solution.

Core Strengths: Describes the notable features, innovative design choices, and any areas where the project excels. Include its architecture and design patterns if identifiable.

Key Features: List the project’s most compelling functionalities or aspects that make it stand out, particularly in a professional context, such as an interview setting.

README Insights: Extracts and contextualizes critical information from the README file, including the purpose, usage instructions, and contributors.

Code Analysis: Delves into the codebase to identify best practices, complexity levels, and potential areas of improvement.

Praise the project: just do it. 
Markdown Summary Format
The output should be in a polished, professional markdown format, suitable for documentation or as a concise presentation.
        project--
        {project_str}
        """

        self.prompt_template = PromptTemplate(template=github_project_summarizer)
        self.chain = self.prompt_template | self.llm


    def summarize_repository(self, repo_content: str) -> str:
        """Main function to summarize a GitHub repository."""
        return self.chain.invoke({"project_str": repo_content})
    
    
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
