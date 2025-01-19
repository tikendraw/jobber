# src/github_utils.py
import os
from typing import Dict, List, Optional

import requests
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


def get_all_repos(username: str, token: str) -> list[Repository]:
    repos = []
    page = 1
    per_page = 100
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    while True:
        url = f'https://api.github.com/users/{username}/repos'
        params = {'per_page': per_page, 'page': page}
        response = requests.get(url, headers=headers, params=params)
        response_data = response.json()

        if response.status_code != 200:
            raise Exception(f'Error fetching repositories: {response_data.get("message", "Unknown error")}')

        if not response_data:
            break

        repos.extend(response_data)
        page += 1

    
    return [Repository(**repo) for repo in repos]




if __name__ == "__main__":
    # Replace with your Github App credentials and initial refresh token if you have it
    ACCESS_TOKEN = os.environ.get("GITHUB_ACCESS_TOKEN")
    USERNAME='tikendraw'

    repositories = get_all_repos(username=USERNAME, token=ACCESS_TOKEN)
    print(f'Total repositories fetched: {len(repositories)}')
    for repo in repositories:
        print(repo.name)
        print(repo.clone_url)
    