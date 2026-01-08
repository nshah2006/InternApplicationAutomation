"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create resume_profiles table
    op.create_table(
        'resume_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=10), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('parsed_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('normalized_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resume_profiles_id'), 'resume_profiles', ['id'], unique=False)
    
    # Create form_schemas table
    op.create_table(
        'form_schemas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('platform', sa.String(length=50), nullable=True),
        sa.Column('schema_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('total_fields', sa.Integer(), nullable=True),
        sa.Column('mapped_fields', sa.Integer(), nullable=True),
        sa.Column('ignored_fields', sa.Integer(), nullable=True),
        sa.Column('unmapped_fields', sa.Integer(), nullable=True),
        sa.Column('schema_version', sa.String(length=20), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_form_schemas_id'), 'form_schemas', ['id'], unique=False)
    op.create_index(op.f('ix_form_schemas_url'), 'form_schemas', ['url'], unique=False)
    
    # Create approved_mappings table
    op.create_table(
        'approved_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resume_profile_id', sa.Integer(), nullable=False),
        sa.Column('form_schema_id', sa.Integer(), nullable=False),
        sa.Column('mappings', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('total_mappings', sa.Integer(), nullable=True),
        sa.Column('exact_matches', sa.Integer(), nullable=True),
        sa.Column('fuzzy_matches', sa.Integer(), nullable=True),
        sa.Column('manual_mappings', sa.Integer(), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['form_schema_id'], ['form_schemas.id'], ),
        sa.ForeignKeyConstraint(['resume_profile_id'], ['resume_profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_approved_mappings_id'), 'approved_mappings', ['id'], unique=False)
    op.create_index(op.f('ix_approved_mappings_resume_profile_id'), 'approved_mappings', ['resume_profile_id'], unique=False)
    op.create_index(op.f('ix_approved_mappings_form_schema_id'), 'approved_mappings', ['form_schema_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_approved_mappings_form_schema_id'), table_name='approved_mappings')
    op.drop_index(op.f('ix_approved_mappings_resume_profile_id'), table_name='approved_mappings')
    op.drop_index(op.f('ix_approved_mappings_id'), table_name='approved_mappings')
    op.drop_table('approved_mappings')
    op.drop_index(op.f('ix_form_schemas_url'), table_name='form_schemas')
    op.drop_index(op.f('ix_form_schemas_id'), table_name='form_schemas')
    op.drop_table('form_schemas')
    op.drop_index(op.f('ix_resume_profiles_id'), table_name='resume_profiles')
    op.drop_table('resume_profiles')

