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
        You are an expert code summarizer. Analyze the project to summarize its technology stack, 
        the problem it solves, its strengths, and features that could impress an interviewer. 
        Incorporate insights from README and code files. Provide a polished and detailed markdown summary.

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
            repos (list): A list of dict of repositories, each containing 'repo_name' and 'repo_content' keys.
            allowed_extensions (list): A list of file extensions to include in the summary.
        Returns:
            list: A list of dictionaries with 'repo'
        """
        summaries = []
        for repo_data in repos:
            try:
                repo_name = repo_data.get("repo_name")
                repo_content = repo_data.get("repo_content")
                if not repo_name or not repo_content:
                    raise ValueError("Each repository entry must contain 'repo' and 'creator' keys.")

                summary = self.summarize_repository(repo_content=repo_content)
                summaries.append({"repo_name": repo_name, "summary": summary})
            except Exception as e:
                summaries.append({"repo_name": repo_data.get("repo_name"), "summary": f"Error: {e}"})
        return summaries


# Usage example
if __name__ == "__main__":
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-8b")
    summarizer = GitHubProjectSummarizer(llm=llm)

    repo_name = 'tikendraw/cli-ai'
    repo_creator = 'tikendraw'
    allowed_extensions = ['.md', '.py']  

    repos_to_summarize = [
        {"repo": "tikendraw/cli-ai", "creator": "tikendraw"},
        {"repo": "tikendraw/funcyou", "creator": "tikendraw"},
    ]


    try:
        summaries = summarizer.summarize_multiple_repositories(repos=repos_to_summarize, allowed_extensions=allowed_extensions)
        for summary in summaries:
            print(f"Repository: {summary['repo']}")
            print(f"Summary: {summary['summary']}\n")
            print('--------------\n')
    except Exception as e:
        print(f"Error: {e}")
