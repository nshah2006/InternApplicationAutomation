"""
GitHub integration endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.db.database import get_db
from app.models.db.user import User
from app.models.db.github_connection import GitHubConnection, GitHubRepo
from app.services.github_service import GitHubService
from app.dependencies import get_current_user

router = APIRouter(prefix="/github", tags=["github"])


class LinkGitHubRequest(BaseModel):
    """Request model for linking GitHub account."""
    access_token: str = Field(..., description="GitHub OAuth access token")


class LinkGitHubResponse(BaseModel):
    """Response model for linking GitHub account."""
    success: bool
    message: str
    github_username: Optional[str] = None
    connection_id: Optional[int] = None


class RepoResponse(BaseModel):
    """Response model for repository data."""
    repo_id: int
    full_name: str
    name: str
    description: Optional[str]
    url: Optional[str]
    homepage: Optional[str]
    language: Optional[str]
    stars_count: int
    forks_count: int
    watchers_count: int
    readme_summary: Optional[str]
    readme_url: Optional[str]
    is_selected: bool
    created_at: Optional[str]
    updated_at: Optional[str]


class SelectReposRequest(BaseModel):
    """Request model for selecting repositories."""
    repo_ids: List[int] = Field(..., description="List of repository IDs to select")


class SelectReposResponse(BaseModel):
    """Response model for selecting repositories."""
    success: bool
    message: str
    selected_count: int


@router.post("/link", response_model=LinkGitHubResponse)
async def link_github_account(
    request: LinkGitHubRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Link GitHub account to user profile.
    
    Args:
        request: LinkGitHubRequest with access token
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        LinkGitHubResponse with connection details
    """
    try:
        # Initialize GitHub service
        github_service = GitHubService(request.access_token)
        
        # Get user info from GitHub
        user_info = github_service.get_user_info()
        github_username = user_info.get("login")
        github_user_id = str(user_info.get("id"))
        github_email = user_info.get("email")
        github_avatar_url = user_info.get("avatar_url")
        
        # Check if connection already exists
        existing_connection = db.query(GitHubConnection).filter(
            GitHubConnection.user_id == current_user.id
        ).first()
        
        if existing_connection:
            # Update existing connection
            existing_connection.access_token = request.access_token
            existing_connection.github_username = github_username
            existing_connection.github_user_id = github_user_id
            existing_connection.github_email = github_email
            existing_connection.github_avatar_url = github_avatar_url
            existing_connection.is_active = True
            existing_connection.updated_at = datetime.utcnow()
            connection = existing_connection
        else:
            # Create new connection
            connection = GitHubConnection(
                user_id=current_user.id,
                access_token=request.access_token,
                github_username=github_username,
                github_user_id=github_user_id,
                github_email=github_email,
                github_avatar_url=github_avatar_url,
                scopes="public_repo,read:user"  # Read-only scopes
            )
            db.add(connection)
        
        db.commit()
        db.refresh(connection)
        
        return LinkGitHubResponse(
            success=True,
            message="GitHub account linked successfully",
            github_username=github_username,
            connection_id=connection.id
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Failed to link GitHub account: {str(e)}"
        )


@router.get("/repos", response_model=List[RepoResponse])
async def get_repositories(
    include_private: bool = Query(False, description="Include private repositories"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's GitHub repositories with README summaries.
    
    Args:
        include_private: Whether to include private repos
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of repositories with README summaries
    """
    # Get GitHub connection
    connection = db.query(GitHubConnection).filter(
        GitHubConnection.user_id == current_user.id,
        GitHubConnection.is_active == True
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=404,
            detail="GitHub account not linked. Please link your GitHub account first."
        )
    
    try:
        # Initialize GitHub service
        github_service = GitHubService(connection.access_token)
        
        # Fetch repos with READMEs
        repos_data = github_service.fetch_repos_with_readmes(
            username=connection.github_username,
            include_private=include_private
        )
        
        # Update or create repo records in database
        repo_responses = []
        for repo_data in repos_data:
            # Check if repo exists
            existing_repo = db.query(GitHubRepo).filter(
                GitHubRepo.repo_id == repo_data["repo_id"]
            ).first()
            
            if existing_repo:
                # Update existing repo
                existing_repo.full_name = repo_data["full_name"]
                existing_repo.name = repo_data["name"]
                existing_repo.description = repo_data.get("description")
                existing_repo.url = repo_data.get("url")
                existing_repo.homepage = repo_data.get("homepage")
                existing_repo.language = repo_data.get("language")
                existing_repo.stars_count = repo_data.get("stars_count", 0)
                existing_repo.forks_count = repo_data.get("forks_count", 0)
                existing_repo.watchers_count = repo_data.get("watchers_count", 0)
                existing_repo.readme_content = repo_data.get("readme_content")
                existing_repo.readme_summary = repo_data.get("readme_summary")
                existing_repo.readme_fetched_at = datetime.utcnow()
                existing_repo.metadata = repo_data.get("metadata", {})
                repo = existing_repo
            else:
                # Create new repo
                repo = GitHubRepo(
                    github_connection_id=connection.id,
                    repo_id=repo_data["repo_id"],
                    full_name=repo_data["full_name"],
                    name=repo_data["name"],
                    description=repo_data.get("description"),
                    url=repo_data.get("url"),
                    homepage=repo_data.get("homepage"),
                    language=repo_data.get("language"),
                    stars_count=repo_data.get("stars_count", 0),
                    forks_count=repo_data.get("forks_count", 0),
                    watchers_count=repo_data.get("watchers_count", 0),
                    readme_content=repo_data.get("readme_content"),
                    readme_summary=repo_data.get("readme_summary"),
                    readme_fetched_at=datetime.utcnow(),
                    metadata=repo_data.get("metadata", {})
                )
                db.add(repo)
            
            db.flush()
            
            repo_responses.append(RepoResponse(
                repo_id=repo.repo_id,
                full_name=repo.full_name,
                name=repo.name,
                description=repo.description,
                url=repo.url,
                homepage=repo.homepage,
                language=repo.language,
                stars_count=repo.stars_count,
                forks_count=repo.forks_count,
                watchers_count=repo.watchers_count,
                readme_summary=repo.readme_summary,
                readme_url=repo.url + "/blob/" + repo_data.get("default_branch", "main") + "/README.md" if repo.url else None,
                is_selected=repo.is_selected,
                created_at=repo.created_at.isoformat() if repo.created_at else None,
                updated_at=repo.updated_at.isoformat() if repo.updated_at else None
            ))
        
        # Update last synced timestamp
        connection.last_synced_at = datetime.utcnow()
        db.commit()
        
        return repo_responses
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch repositories: {str(e)}"
        )


@router.post("/repos/select", response_model=SelectReposResponse)
async def select_repositories(
    request: SelectReposRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Select repositories as projects.
    
    Args:
        request: SelectReposRequest with list of repo IDs
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        SelectReposResponse with selection status
    """
    # Get GitHub connection
    connection = db.query(GitHubConnection).filter(
        GitHubConnection.user_id == current_user.id,
        GitHubConnection.is_active == True
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=404,
            detail="GitHub account not linked"
        )
    
    # Get repos belonging to this connection
    repos = db.query(GitHubRepo).filter(
        GitHubRepo.github_connection_id == connection.id,
        GitHubRepo.repo_id.in_(request.repo_ids)
    ).all()
    
    if len(repos) != len(request.repo_ids):
        raise HTTPException(
            status_code=400,
            detail="Some repository IDs not found"
        )
    
    # Deselect all repos first
    db.query(GitHubRepo).filter(
        GitHubRepo.github_connection_id == connection.id
    ).update({"is_selected": False, "selected_at": None})
    
    # Select requested repos
    selected_count = 0
    for repo in repos:
        repo.is_selected = True
        repo.selected_at = datetime.utcnow()
        selected_count += 1
    
    db.commit()
    
    return SelectReposResponse(
        success=True,
        message=f"Selected {selected_count} repositories",
        selected_count=selected_count
    )


@router.get("/repos/selected", response_model=List[RepoResponse])
async def get_selected_repositories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get selected repositories.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of selected repositories
    """
    # Get GitHub connection
    connection = db.query(GitHubConnection).filter(
        GitHubConnection.user_id == current_user.id,
        GitHubConnection.is_active == True
    ).first()
    
    if not connection:
        return []
    
    # Get selected repos
    repos = db.query(GitHubRepo).filter(
        GitHubRepo.github_connection_id == connection.id,
        GitHubRepo.is_selected == True
    ).all()
    
    return [
        RepoResponse(
            repo_id=repo.repo_id,
            full_name=repo.full_name,
            name=repo.name,
            description=repo.description,
            url=repo.url,
            homepage=repo.homepage,
            language=repo.language,
            stars_count=repo.stars_count,
            forks_count=repo.forks_count,
            watchers_count=repo.watchers_count,
            readme_summary=repo.readme_summary,
            readme_url=repo.url + "/blob/main/README.md" if repo.url else None,
            is_selected=repo.is_selected,
            created_at=repo.created_at.isoformat() if repo.created_at else None,
            updated_at=repo.updated_at.isoformat() if repo.updated_at else None
        )
        for repo in repos
    ]


@router.delete("/unlink")
async def unlink_github_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unlink GitHub account.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    connection = db.query(GitHubConnection).filter(
        GitHubConnection.user_id == current_user.id
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=404,
            detail="GitHub account not linked"
        )
    
    connection.is_active = False
    db.commit()
    
    return {"success": True, "message": "GitHub account unlinked successfully"}

