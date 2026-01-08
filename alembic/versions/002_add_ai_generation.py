"""Add AI generation table

Revision ID: 002_add_ai_generation
Revises: 001_initial
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_ai_generation'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ai_generations table
    op.create_table(
        'ai_generations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        
        # Foreign keys
        sa.Column('resume_profile_id', sa.Integer(), nullable=False),
        sa.Column('form_schema_id', sa.Integer(), nullable=True),
        
        # Input data
        sa.Column('job_description', sa.Text(), nullable=False),
        sa.Column('normalized_resume_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        
        # Field context
        sa.Column('field_name', sa.String(length=255), nullable=True),
        sa.Column('field_type', sa.String(length=50), nullable=True),
        
        # AI generation metadata
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('prompt_template', sa.Text(), nullable=True),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=True, server_default=sa.text('0.7')),
        sa.Column('max_tokens', sa.Integer(), nullable=True, server_default=sa.text('1000')),
        
        # AI response
        sa.Column('generated_text', sa.Text(), nullable=False),
        sa.Column('raw_response', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        
        # Usage tracking
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('cost_estimate', sa.Float(), nullable=True),
        
        # Approval workflow
        sa.Column('is_approved', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_text', sa.Text(), nullable=True),
        
        # User feedback
        sa.Column('user_feedback', sa.Text(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        
        # Notes
        sa.Column('notes', sa.Text(), nullable=True),
        
        sa.ForeignKeyConstraint(['resume_profile_id'], ['resume_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['form_schema_id'], ['form_schemas.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_generations_id'), 'ai_generations', ['id'], unique=False)
    op.create_index(op.f('ix_ai_generations_resume_profile_id'), 'ai_generations', ['resume_profile_id'], unique=False)
    op.create_index(op.f('ix_ai_generations_form_schema_id'), 'ai_generations', ['form_schema_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ai_generations_form_schema_id'), table_name='ai_generations')
    op.drop_index(op.f('ix_ai_generations_resume_profile_id'), table_name='ai_generations')
    op.drop_index(op.f('ix_ai_generations_id'), table_name='ai_generations')
    op.drop_table('ai_generations')
