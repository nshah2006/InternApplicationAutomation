"""
GitHub API service for fetching repositories and READMEs.
"""

import os
import requests
import base64
from typing import List, Dict, Optional, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# GitHub API base URL
GITHUB_API_BASE = "https://api.github.com"


class GitHubService:
    """
    Service for interacting with GitHub API.
    
    Provides read-only access to user repositories and README files.
    """
    
    def __init__(self, access_token: str):
        """
        Initialize GitHub service with access token.
        
        Args:
            access_token: GitHub OAuth access token
        """
        self.access_token = access_token
        self.headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Resume-Automation-App"
        }
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get authenticated user information.
        
        Returns:
            Dictionary with user information
        """
        response = requests.get(
            f"{GITHUB_API_BASE}/user",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_repositories(
        self,
        username: Optional[str] = None,
        include_private: bool = False,
        sort: str = "updated",
        per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get user's repositories.
        
        Args:
            username: GitHub username (if None, uses authenticated user)
            include_private: Whether to include private repos
            sort: Sort order (updated, created, pushed, full_name)
            per_page: Number of repos per page (max 100)
            
        Returns:
            List of repository dictionaries
        """
        if username:
            url = f"{GITHUB_API_BASE}/users/{username}/repos"
        else:
            url = f"{GITHUB_API_BASE}/user/repos"
            if include_private:
                url += "?affiliation=owner,collaborator"
        
        params = {
            "sort": sort,
            "per_page": min(per_page, 100),
            "type": "all" if include_private else "public"
        }
        
        repos = []
        page = 1
        
        while True:
            params["page"] = page
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            page_repos = response.json()
            if not page_repos:
                break
            
            repos.extend(page_repos)
            
            # Check if there are more pages
            if len(page_repos) < params["per_page"]:
                break
            
            page += 1
        
        return repos
    
    def get_repository_readme(
        self,
        owner: str,
        repo: str,
        branch: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get repository README content.
        
        Args:
            owner: Repository owner username
            repo: Repository name
            branch: Branch name (defaults to default branch)
            
        Returns:
            Dictionary with README content and metadata, or None if not found
        """
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/readme"
        params = {}
        if branch:
            params["ref"] = branch
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            readme_data = response.json()
            
            # Decode base64 content
            content = base64.b64decode(readme_data["content"]).decode("utf-8")
            
            return {
                "content": content,
                "encoding": readme_data.get("encoding", "base64"),
                "name": readme_data.get("name", "README.md"),
                "path": readme_data.get("path", "README.md"),
                "sha": readme_data.get("sha"),
                "size": readme_data.get("size", 0),
                "url": readme_data.get("html_url")
            }
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    def get_repository_details(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get detailed repository information.
        
        Args:
            owner: Repository owner username
            repo: Repository name
            
        Returns:
            Dictionary with repository details
        """
        response = requests.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def normalize_repo_data(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize GitHub repository data to our format.
        
        Args:
            repo_data: Raw GitHub API repository data
            
        Returns:
            Normalized repository dictionary
        """
        return {
            "repo_id": repo_data["id"],
            "full_name": repo_data["full_name"],
            "name": repo_data["name"],
            "description": repo_data.get("description"),
            "url": repo_data.get("html_url"),
            "homepage": repo_data.get("homepage"),
            "language": repo_data.get("language"),
            "stars_count": repo_data.get("stargazers_count", 0),
            "forks_count": repo_data.get("forks_count", 0),
            "watchers_count": repo_data.get("watchers_count", 0),
            "created_at": repo_data.get("created_at"),
            "updated_at": repo_data.get("updated_at"),
            "pushed_at": repo_data.get("pushed_at"),
            "is_private": repo_data.get("private", False),
            "is_fork": repo_data.get("fork", False),
            "default_branch": repo_data.get("default_branch", "main"),
            "topics": repo_data.get("topics", []),
            "license": repo_data.get("license", {}).get("name") if repo_data.get("license") else None,
            "metadata": {
                "archived": repo_data.get("archived", False),
                "disabled": repo_data.get("disabled", False),
                "has_issues": repo_data.get("has_issues", False),
                "has_projects": repo_data.get("has_projects", False),
                "has_wiki": repo_data.get("has_wiki", False),
                "has_pages": repo_data.get("has_pages", False),
            }
        }
    
    def fetch_repos_with_readmes(
        self,
        username: Optional[str] = None,
        include_private: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Fetch repositories with their README summaries.
        
        Args:
            username: GitHub username (if None, uses authenticated user)
            include_private: Whether to include private repos
            
        Returns:
            List of repositories with README summaries
        """
        repos = self.get_repositories(username=username, include_private=include_private)
        normalized_repos = []
        
        for repo in repos:
            normalized = self.normalize_repo_data(repo)
            
            # Fetch README
            owner, repo_name = normalized["full_name"].split("/", 1)
            readme_data = self.get_repository_readme(owner, repo_name)
            
            if readme_data:
                normalized["readme_content"] = readme_data["content"]
                # Create summary (first 500 characters)
                normalized["readme_summary"] = readme_data["content"][:500] + "..." if len(readme_data["content"]) > 500 else readme_data["content"]
                normalized["readme_url"] = readme_data.get("url")
            else:
                normalized["readme_content"] = None
                normalized["readme_summary"] = None
                normalized["readme_url"] = None
            
            normalized_repos.append(normalized)
        
        return normalized_repos

