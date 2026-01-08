"""Add feature flags and roles

Revision ID: 004_add_feature_flags_and_roles
Revises: 003_add_github_integration
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_feature_flags_and_roles'
down_revision = '003_add_github_integration'
branch_labels = None
depends_on = None


def upgrade():
    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)

    # Create user_roles association table
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    # Create user_role_assignments table
    op.create_table(
        'user_role_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_role_assignments_id'), 'user_role_assignments', ['id'], unique=False)
    op.create_index(op.f('ix_user_role_assignments_role_id'), 'user_role_assignments', ['role_id'], unique=False)
    op.create_index(op.f('ix_user_role_assignments_user_id'), 'user_role_assignments', ['user_id'], unique=False)

    # Create feature_flags table
    op.create_table(
        'feature_flags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='disabled'),
        sa.Column('rollout_percentage', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('role_overrides', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_feature_flags_id'), 'feature_flags', ['id'], unique=False)
    op.create_index(op.f('ix_feature_flags_name'), 'feature_flags', ['name'], unique=True)

    # Create feature_flag_history table
    op.create_table(
        'feature_flag_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('feature_flag_id', sa.Integer(), nullable=False),
        sa.Column('changed_by', sa.Integer(), nullable=True),
        sa.Column('old_status', sa.String(length=20), nullable=True),
        sa.Column('new_status', sa.String(length=20), nullable=True),
        sa.Column('old_rollout_percentage', sa.Integer(), nullable=True),
        sa.Column('new_rollout_percentage', sa.Integer(), nullable=True),
        sa.Column('old_role_overrides', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('new_role_overrides', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['feature_flag_id'], ['feature_flags.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feature_flag_history_id'), 'feature_flag_history', ['id'], unique=False)
    op.create_index(op.f('ix_feature_flag_history_feature_flag_id'), 'feature_flag_history', ['feature_flag_id'], unique=False)

    # Insert default roles
    op.execute("""
        INSERT INTO roles (name, display_name, description, permissions, is_active)
        VALUES 
        ('user', 'User', 'Regular user role', '[]', true),
        ('admin', 'Administrator', 'Administrator role with full access', '["*"]', true),
        ('moderator', 'Moderator', 'Moderator role with limited admin access', '["manage_feature_flags", "view_users"]', true)
    """)

    # Insert default feature flags
    op.execute("""
        INSERT INTO feature_flags (name, display_name, description, status, rollout_percentage, role_overrides, config, is_active)
        VALUES 
        ('autofill', 'Autofill Feature', 'Enable/disable autofill functionality', 'disabled', 0, '{}', '{}', true),
        ('ai_generation', 'AI Generation Feature', 'Enable/disable AI text generation', 'disabled', 0, '{}', '{}', true)
    """)


def downgrade():
    op.drop_index(op.f('ix_feature_flag_history_feature_flag_id'), table_name='feature_flag_history')
    op.drop_index(op.f('ix_feature_flag_history_id'), table_name='feature_flag_history')
    op.drop_table('feature_flag_history')
    op.drop_index(op.f('ix_feature_flags_name'), table_name='feature_flags')
    op.drop_index(op.f('ix_feature_flags_id'), table_name='feature_flags')
    op.drop_table('feature_flags')
    op.drop_index(op.f('ix_user_role_assignments_user_id'), table_name='user_role_assignments')
    op.drop_index(op.f('ix_user_role_assignments_role_id'), table_name='user_role_assignments')
    op.drop_index(op.f('ix_user_role_assignments_id'), table_name='user_role_assignments')
    op.drop_table('user_role_assignments')
    op.drop_table('user_roles')
    op.drop_index(op.f('ix_roles_name'), table_name='roles')
    op.drop_index(op.f('ix_roles_id'), table_name='roles')
    op.drop_table('roles')

