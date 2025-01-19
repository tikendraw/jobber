import os

from dotenv import load_dotenv
from langchain.llms.base import LLM
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders.github import GithubFileLoader
from langchain_google_genai import ChatGoogleGenerativeAI


class GitHubProjectSummarizer:
    def __init__(self, llm:LLM, github_access_token:str=None):
        
        self.access_token = github_access_token or os.environ.get('GITHUB_ACCESS_TOKEN') 
        if not self.access_token:
            raise ValueError("GITHUB_ACCESS_TOKEN is not set in the environment file. or passed as an argument.")


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


    @staticmethod
    def file_filter(file: str, allowed_extensions: list) -> bool:
        """Filter function to select files based on allowed extensions."""
        return any(file.endswith(ext) for ext in allowed_extensions)

    def load_project_files(self, repo: str, creator: str, allowed_extensions: list, include_prs: bool = False):
        """Load files from a GitHub repository."""
        loader = GithubFileLoader(
            access_token=self.access_token,
            repo=repo,
            creator=creator,
            include_prs=include_prs,
            file_filter=lambda file: self.file_filter(file, allowed_extensions),
        )
        return loader.load()

    def format_project_content(self, documents) -> str:
        """Combine project content into a single formatted string."""
        all_texts = ''
        for doc in documents:
            all_texts += '---------------------\n'
            all_texts += f"filename: {doc.metadata['path']}\n\n"
            all_texts += f"{doc.page_content}\n\n"
        return all_texts

    def summarize(self, project_content: str) -> str:
        """Generate a summary of the project using an LLM."""
        return self.chain.invoke({"project_str": project_content})

    def summarize_repository(self, repo: str, creator: str, allowed_extensions: list=['.md','.py']) -> str:
        """Main function to summarize a GitHub repository."""
        documents = self.load_project_files(repo=repo, creator=creator, allowed_extensions=allowed_extensions)
        project_content = self.format_project_content(documents)
        return self.summarize(project_content)
    
    
    def summarize_multiple_repositories(self, repos: list, allowed_extensions: list = ['.md', '.py']) -> list:
        """Summarize multiple repositories and return a list of dictionaries."""
        summaries = []
        for repo_data in repos:
            try:
                repo_name = repo_data.get("repo")
                creator = repo_data.get("creator")
                if not repo_name or not creator:
                    raise ValueError("Each repository entry must contain 'repo' and 'creator' keys.")

                summary = self.summarize_repository(repo=repo_name, creator=creator, allowed_extensions=allowed_extensions)
                summaries.append({"repo": repo_name, "summary": summary})
            except Exception as e:
                summaries.append({"repo": repo_data.get("repo", "Unknown"), "summary": f"Error: {e}"})
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
