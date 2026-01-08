"""Add GitHub integration tables

Revision ID: 003_add_github_integration
Revises: 002_add_ai_generation
Create Date: 2024-01-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_github_integration'
down_revision = '002_add_ai_generation'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create github_connections table
    op.create_table(
        'github_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('access_token', sa.String(length=512), nullable=False),
        sa.Column('token_type', sa.String(length=50), nullable=True),
        sa.Column('github_username', sa.String(length=255), nullable=False),
        sa.Column('github_user_id', sa.String(length=255), nullable=False),
        sa.Column('github_email', sa.String(length=255), nullable=True),
        sa.Column('github_avatar_url', sa.String(length=512), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scopes', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_github_connections_id'), 'github_connections', ['id'], unique=False)
    op.create_index(op.f('ix_github_connections_user_id'), 'github_connections', ['user_id'], unique=True)
    
    # Create github_repos table
    op.create_table(
        'github_repos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('github_connection_id', sa.Integer(), nullable=False),
        sa.Column('repo_id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.String(length=512), nullable=True),
        sa.Column('homepage', sa.String(length=512), nullable=True),
        sa.Column('language', sa.String(length=100), nullable=True),
        sa.Column('stars_count', sa.Integer(), nullable=True),
        sa.Column('forks_count', sa.Integer(), nullable=True),
        sa.Column('watchers_count', sa.Integer(), nullable=True),
        sa.Column('readme_content', sa.Text(), nullable=True),
        sa.Column('readme_summary', sa.Text(), nullable=True),
        sa.Column('readme_fetched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_selected', sa.Boolean(), nullable=True),
        sa.Column('selected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['github_connection_id'], ['github_connections.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('repo_id')
    )
    op.create_index(op.f('ix_github_repos_id'), 'github_repos', ['id'], unique=False)
    op.create_index(op.f('ix_github_repos_github_connection_id'), 'github_repos', ['github_connection_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_github_repos_github_connection_id'), table_name='github_repos')
    op.drop_index(op.f('ix_github_repos_id'), table_name='github_repos')
    op.drop_table('github_repos')
    op.drop_index(op.f('ix_github_connections_user_id'), table_name='github_connections')
    op.drop_index(op.f('ix_github_connections_id'), table_name='github_connections')
    op.drop_table('github_connections')

