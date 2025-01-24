# src/github_utils.py
import asyncio
import base64
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Union

import httpx
from pydantic import BaseModel


class Owner(BaseModel):
    login: Optional[str] = None
    id: Optional[int] = None
    node_id: Optional[str] = None
    avatar_url: Optional[str] = None
    gravatar_id: Optional[str] = None
    url: Optional[str] = None
    html_url: Optional[str] = None
    followers_url: Optional[str] = None
    following_url: Optional[str] = None
    gists_url: Optional[str] = None
    starred_url: Optional[str] = None
    subscriptions_url: Optional[str] = None
    organizations_url: Optional[str] = None
    repos_url: Optional[str] = None
    events_url: Optional[str] = None
    received_events_url: Optional[str] = None
    type: Optional[str] = None
    site_admin: Optional[bool] = None


class Permissions(BaseModel):
    admin: Optional[bool] = None
    maintain: Optional[bool] = None
    push: Optional[bool] = None
    triage: Optional[bool] = None
    pull: Optional[bool] = None


class Repository(BaseModel):
    id: Optional[int] = None
    node_id: Optional[str] = None
    name: Optional[str] = None
    full_name: Optional[str] = None
    private: Optional[bool] = None
    owner: Optional[Owner] = None
    html_url: Optional[str] = None
    description: Optional[str] = None
    fork: Optional[bool] = None
    url: Optional[str] = None
    forks_url: Optional[str] = None
    keys_url: Optional[str] = None
    collaborators_url: Optional[str] = None
    teams_url: Optional[str] = None
    hooks_url: Optional[str] = None
    issue_events_url: Optional[str] = None
    events_url: Optional[str] = None
    assignees_url: Optional[str] = None
    branches_url: Optional[str] = None
    tags_url: Optional[str] = None
    blobs_url: Optional[str] = None
    git_tags_url: Optional[str] = None
    git_refs_url: Optional[str] = None
    trees_url: Optional[str] = None
    statuses_url: Optional[str] = None
    languages_url: Optional[str] = None
    stargazers_url: Optional[str] = None
    contributors_url: Optional[str] = None
    subscribers_url: Optional[str] = None
    subscription_url: Optional[str] = None
    commits_url: Optional[str] = None
    git_commits_url: Optional[str] = None
    comments_url: Optional[str] = None
    issue_comment_url: Optional[str] = None
    contents_url: Optional[str] = None
    compare_url: Optional[str] = None
    merges_url: Optional[str] = None
    archive_url: Optional[str] = None
    downloads_url: Optional[str] = None
    issues_url: Optional[str] = None
    pulls_url: Optional[str] = None
    milestones_url: Optional[str] = None
    notifications_url: Optional[str] = None
    labels_url: Optional[str] = None
    releases_url: Optional[str] = None
    deployments_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    pushed_at: Optional[str] = None
    git_url: Optional[str] = None
    ssh_url: Optional[str] = None
    clone_url: Optional[str] = None
    svn_url: Optional[str] = None
    homepage: Optional[str] = None
    size: Optional[int] = None
    stargazers_count: Optional[int] = None
    watchers_count: Optional[int] = None
    language: Optional[str] = None
    has_issues: Optional[bool] = None
    has_projects: Optional[bool] = None
    has_downloads: Optional[bool] = None
    has_wiki: Optional[bool] = None
    has_pages: Optional[bool] = None
    has_discussions: Optional[bool] = None
    forks_count: Optional[int] = None
    mirror_url: Optional[str] = None
    archived: Optional[bool] = None
    disabled: Optional[bool] = None
    open_issues_count: Optional[int] = None
    license: Optional[Dict[str, Optional[str]]] = None
    allow_forking: Optional[bool] = None
    is_template: Optional[bool] = None
    web_commit_signoff_required: Optional[bool] = None
    topics: Optional[List[str]] = None
    visibility: Optional[str] = None
    forks: Optional[int] = None
    open_issues: Optional[int] = None
    watchers: Optional[int] = None
    default_branch: Optional[str] = None
    permissions: Optional[Permissions] = None

    class Config:
        from_attributes = True


def get_all_repos(username: str, access_token: str) -> list[Repository]:
    repos= []
    page = 1
    per_page = 100
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    while True:
        url = f"https://api.github.com/users/{username}/repos"
        params = {"per_page": per_page, "page": page}
        response = httpx.get(url, headers=headers, params=params)
        response_data: dict = response.json()

        if response.status_code != 200:
            raise Exception(
                f'Error fetching repositories: {response_data.get("message", "Unknown error")}'
            )

        if not response_data:
            break

        repos.extend(response_data)
        page += 1

    return [Repository(**repo) for repo in repos]


def file_filter(file: str, allowed_extensions: list) -> bool:
    """Filter function to select files based on allowed extensions."""
    return any(file.endswith(ext) for ext in allowed_extensions)


async def fetch_file_content(client: httpx.AsyncClient, file_url: str, headers: dict):
    """
    Fetch the content of a single file asynchronously.
    """
    try:
        response = await client.get(file_url, headers=headers)
        response.raise_for_status()
        file_data: dict = response.json()
        if file_data.get("encoding") == "base64":
            return base64.b64decode(file_data["content"]).decode("utf-8")
    except Exception as e:
        print(f"Failed to fetch file: {file_url}. Error: {e}")
    return None


async def get_repository_files_async(
    username:str,
    repo_name:str,
    branch:str,
    access_token:str,
    allowed_extensions:set=None,
    excluded_extensions:set=None,
):
    """
    Retrieve all files and their contents for a specific branch in a repository using asynchronous requests.
    """
    headers = {"Authorization": f"token {access_token}"}
    base_url = f"https://api.github.com/repos/{username}/{repo_name}"

    async with httpx.AsyncClient() as client:
        # Step 1: Get the SHA of the branch
        branch_url = f"{base_url}/branches/{branch}"
        branch_response = await client.get(branch_url, headers=headers, timeout=10.5)
        branch_response.raise_for_status()
        branch_data = branch_response.json()
        tree_sha = branch_data["commit"]["commit"]["tree"]["sha"]

        # Step 2: Get the tree recursively
        tree_url = f"{base_url}/git/trees/{tree_sha}?recursive=1"
        tree_response = await client.get(tree_url, headers=headers, timeout=10.5)
        tree_response.raise_for_status()
        tree_data = tree_response.json()

        # Step 3: Fetch file contents asynchronously
        files_content = {}
        tasks = []
        for item in tree_data.get("tree", []):
            if item["type"] == "blob":  # Ensure it's a file
                file_extension = os.path.splitext(item["path"])[1].lower()
                if allowed_extensions and file_extension not in allowed_extensions:
                    continue
                if excluded_extensions and file_extension in excluded_extensions:
                    continue

                file_url = f"{base_url}/contents/{item['path']}?ref={branch}"
                tasks.append(
                    (item["path"], fetch_file_content(client, file_url, headers))
                )

        # Run tasks concurrently
        results = await asyncio.gather(
            *[task[1] for task in tasks], return_exceptions=True
        )
        for idx, result in enumerate(results):
            if result is not None:
                files_content[tasks[idx][0]] = result

    return files_content


async def save_repository_files_async(
    username: str,
    repo_name: str,
    branch: str,
    access_token: str,
    save_dir: Union[str, Path],
    allowed_extensions: Optional[set] = None,
    excluded_extensions: Optional[set] = None,
) -> str:
    """
    Asynchronously fetch and save files from a GitHub repository.

    Args:
        username (str): GitHub username
        repo_name (str): Name of the repository
        branch (str): Branch name to fetch from
        access_token (str): GitHub access token
        save_dir (Union[str, Path]): Directory to save the files
        allowed_extensions (Optional[set]): Set of allowed file extensions
        excluded_extensions (Optional[set]): Set of file extensions to exclude

    Returns:
        str: Absolute path to the saved repository directory
    """
    print(f"Fetching files for repository: {repo_name}")
    files_content = await get_repository_files_async(
        username,
        repo_name,
        branch,
        access_token,
        allowed_extensions,
        excluded_extensions,
    )

    # Define the save directory path
    if isinstance(save_dir, str):
        save_dir = Path(save_dir)
    elif not isinstance(save_dir, Path):
        raise ValueError("save_dir must be a string or a Path object.")

    repo_save_path: Path = save_dir / repo_name

    # Save each file to the local directory
    for file_path, content in files_content.items():
        local_file_path: Path = repo_save_path / file_path
        local_file_path.parent.mkdir(
            parents=True, exist_ok=True
        )  # Ensure parent directories exist
        try:
            local_file_path.write_text(content)  # Write file content to disk
            print(f"File saved at {local_file_path.absolute().as_posix()}")
        except Exception as e:
            print(f"Failed to save file: {file_path}. Error: {e}")

    print(f"Repository {repo_name} saved successfully in {repo_save_path.absolute().as_posix()}")
    return repo_save_path


async def process_all_repositories(
    repos: List[Dict[str, str]],
    access_token: str,
    save_dir: str,
    allowed_extensions: set = {".py", ".md"},
    excluded_extensions: set = {".pkl", ".pt", ".h5", ".ipynb"},
) -> List[Path]:
    """
    Process all repositories concurrently.

    Args:
        repos (list): List of dictionaries with repository details. {"username": "username", "repo_name": "repo_name", "branch": "branch"}
        access_token (str): GitHub access token.
        save_dir (str): Directory to save the files.
        allowed_extensions (set): Set of allowed file extensions. ['.py', '.md', 'txt']
        excluded_extensions (set): Set of excluded file extensions. ['.pkl', '.pt', '.csv', '.joblib', '.ipynb', '.h5', '.jpg', '.png']
    Returns:
        List[str]: List of paths to saved repositories.
    """

    async def process_repository(repo: Dict[str, str]) -> str:
        return await save_repository_files_async(
            username=repo["username"],
            repo_name=repo["repo_name"],
            branch=repo["branch"],
            access_token=access_token,
            save_dir=save_dir,
            allowed_extensions=allowed_extensions,
            excluded_extensions=excluded_extensions,
        )

    tasks = [process_repository(repo) for repo in repos]
    return await asyncio.gather(*tasks)


async def process_user_repositories(
    username: str,
    access_token: str,
    save_dir: str,
    repo_filter: Callable[[Repository], bool] = None,
    allowed_extensions: set = {".py", ".md"},
    excluded_extensions: set = {".pkl", ".pt", ".h5", ".ipynb"},
) ->List[Path]:
    """
    Fetch, filter, and save repositories for a user.

    Args:
        username (str): GitHub username.
        token (str): GitHub access token.
        save_dir (str): Directory to save the files.
        repo_filter (callable): A callable that takes a `Repository` and returns a boolean to filter repos.
        allowed_extensions (set): Allowed file extensions for filtering files.
        excluded_extensions (set): Excluded file extensions for filtering files.

    Returns:
        List[Path]: List of paths to saved repositories.
    """
    # Step 1: Get all repositories for the user
    print(f"Fetching repositories for user: {username}")
    all_repositories = get_all_repos(username, access_token)

    if repo_filter:
        # Step 2: Filter repositories using the provided callable
        filtered_repos = list(filter(repo_filter, all_repositories))
        print(f"Filtered {len(filtered_repos)} repositories for user {username}.")
    else:
        filtered_repos = all_repositories

    # Step 3: Create the list of repositories to process
    repos_to_process = [
        {
            "username": repo.owner.login,
            "repo_name": repo.name,
            "branch": repo.default_branch or "main",
        }
        for repo in filtered_repos
    ]

    # Step 4: Process and save files for the filtered repositories
    print("Starting to process filtered repositories...")
    saved_paths = await process_all_repositories(
        repos_to_process,
        access_token=access_token,
        save_dir=save_dir,
        allowed_extensions=allowed_extensions,
        excluded_extensions=excluded_extensions,
    )

    return saved_paths


def filter_out_forked_and_private_repos(repo: Repository) -> bool:
    """
    Filter function to exclude forked and private repositories.

    Args:
        repo (Repository): A Repository object.

    Returns:
        bool: True if the repository is not forked and not private, False otherwise.
    """
    return not repo.fork and not repo.private


# if __name__ == "__main__":
#     # Replace with your Github App credentials and initial refresh token if you have it
#     ACCESS_TOKEN = os.environ.get("GITHUB_ACCESS_TOKEN")
#     USERNAME='tikendraw'
#     repo_name='Amazon-review-sentiment-analysis'
#     # File type filtering
#     allowed_extensions = {'.py', '.md', '.txt'}
#     excluded_extensions = {'.pkl', '.pt', '.csv', '.joblib', '.ipynb', '.h5', '.jpg', '.png'}

#     # GitHub repositories to process

#     # repos = get_all_repos(USERNAME, ACCESS_TOKEN)
#     # from pprint import pprint
#     # for repo in repos:
#     #     pprint(repo, indent=4)


#     # repos =    [
#     #     {"username": "tikendraw", "repo_name": "Amazon-review-sentiment-analysis", "branch": "main"},
#     #     {"username": "tikendraw", "repo_name": "cli-ai", "branch": "main"},
#     #     {"username": "tikendraw", "repo_name": "jobber", "branch": "main"},
#     #     {"username": "tikendraw", "repo_name": "groq-on", "branch": "main"},
#     # ]

#     # # Call the function to process repositories
#     # ss = asyncio.run(process_all_repositories(repos, ACCESS_TOKEN, save_dir='oladelete',allowed_extensions=allowed_extensions, excluded_extensions=excluded_extensions))
#     # print(f'ss: {ss}')
#     # a = get_all_repos(USERNAME, ACCESS_TOKEN)
#     # print(len(a))
#     # for i in a:
#     #     # print(i)
#     #     print(i.name)
#     #     print(i.clone_url)
#     #     print(i.default_branch)
#     #     print('------')
