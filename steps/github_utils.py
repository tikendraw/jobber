# steps/github_utils.py
import json
import os
import subprocess
from curses import REPORT_MOUSE_POSITION
from datetime import datetime
from pprint import pprint
from typing import Dict, List, Optional, TypedDict

import requests
from github_obj import Repository


def get_github_repos(username):
    """Fetches a list of a user's GitHub repositories."""
    url = f"https://api.github.com/users/{username}/repos"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        repos = response.json()
        return repos
    except requests.exceptions.RequestException as e:
        print(f"Error fetching repos: {e}")
        return None


def clone_or_pull_repo(repo_url, repo_name, local_repo_dir):
    """Clones a repository if it doesn't exist locally or pulls changes."""
    repo_path = os.path.join(local_repo_dir, repo_name)

    if not os.path.exists(repo_path):
        print(f"Cloning {repo_name}...")
        try:
             subprocess.run(["git", "clone", repo_url, repo_path], check=True, capture_output=True, text=True)
             print(f"Cloned {repo_name} successfully.")
        except subprocess.CalledProcessError as e:
             print(f"Error cloning {repo_name}: {e.stderr}")
             return False
    else:
        print(f"Checking for updates in {repo_name}...")
        try:
            # Fetch changes
            fetch_result = subprocess.run(["git", "fetch"], cwd=repo_path, check=True, capture_output=True, text=True)
            # Get the number of commits in local and remote
            local_commits_result = subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=repo_path, check=True, capture_output=True, text=True)
            remote_commits_result = subprocess.run(["git", "rev-list", "--count", "@{u}"], cwd=repo_path, check=True, capture_output=True, text=True)

            local_commits = int(local_commits_result.stdout.strip())
            remote_commits = int(remote_commits_result.stdout.strip())
            if local_commits < remote_commits:
                pull_result = subprocess.run(["git", "pull"], cwd=repo_path, check=True, capture_output=True, text=True)
                print(f"Pulled changes for {repo_name}. {pull_result.stdout}")
            else:
                print(f"No updates for {repo_name}.")
        except subprocess.CalledProcessError as e:
            print(f"Error pulling {repo_name}: {e.stderr}")
            return False
    return True

def pull_readme(repo_url, repo_name, local_repo_dir):
    """Clones a repository if it doesn't exist locally or pulls the README.md file."""
    repo_path = os.path.join(local_repo_dir, repo_name)

    if not os.path.exists(repo_path):
        print(f"Cloning {repo_name}...")
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, repo_path], 
                check=True, capture_output=True, text=True
            )
            print(f"Cloned {repo_name} successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error cloning {repo_name}: {e.stderr}")
            return False
    else:
        print(f"Updating README.md for {repo_name}...")
        try:
            # Fetch updates from the remote repository
            subprocess.run(["git", "fetch", "origin"], cwd=repo_path, check=True, capture_output=True, text=True)
            # Pull only the README.md file from the main branch
            subprocess.run(["git", "checkout", "origin/main", "README.md"], cwd=repo_path, check=True, capture_output=True, text=True)
            print(f"Updated README.md for {repo_name}.")
        except subprocess.CalledProcessError as e:
            print(f"Error updating README.md for {repo_name}: {e.stderr}")
            return False
    
    readme_path = os.path.join(repo_path, "README.md")
    if os.path.exists(readme_path):
        print(f"README.md is available for {repo_name}.")
    else:
        print(f"No README.md found in {repo_name}.")
    
    return True

def main(username, local_repo_dir="repos", n_repos:int=None):
    """Main function to list, clone, or pull repos."""
    repos = get_github_repos(username)

    if not repos:
        print("No Repositories Found or Error Fetching Repos")
        return
    if not os.path.exists(local_repo_dir):
        os.makedirs(local_repo_dir)
    
    print(len(repos))
    print(type(repos))
    print(type(repos[0]))
    # pprint(repos, indent=4)

    repos = repos if n_repos is None else repos[:n_repos]
    print('len repose new: ', len(repos))
    for repo in repos:
        repo = Repository(**repo)

        pprint(repo.model_dump(), indent=4)
        repo_name = repo.name
        repo_url =  repo.clone_url
        print(f"Repo: {repo_name}")
        print("URL: ",repo_url)
        # break

        # # break
        # pull_readme(repo_url, repo_name, local_repo_dir)


if __name__ == "__main__":
    username = "tikendraw" # Replace with the desired username
    main(username, n_repos=2)