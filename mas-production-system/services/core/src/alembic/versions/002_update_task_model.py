"""Update task model

Revision ID: 002
Revises: 001
Create Date: 2025-07-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Drop old constraints
    op.drop_constraint('check_priority_range', 'tasks', type_='check')
    
    # Drop old columns
    op.drop_column('tasks', 'organization_id')
    op.drop_column('tasks', 'requirements')
    op.drop_column('tasks', 'deadline')
    op.drop_column('tasks', 'assigned_agents')
    op.drop_column('tasks', 'started_at')
    
    # Add new columns
    op.add_column('tasks', sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False))
    op.add_column('tasks', sa.Column('title', sa.String(200), nullable=False))
    op.add_column('tasks', sa.Column('task_type', sa.String(50), nullable=False))
    op.add_column('tasks', sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('tasks', sa.Column('task_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'))
    op.add_column('tasks', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    
    # Change priority to string
    op.alter_column('tasks', 'priority',
                    existing_type=sa.INTEGER(),
                    type_=sa.String(20),
                    existing_nullable=False,
                    postgresql_using="CASE WHEN priority <= 3 THEN 'low' WHEN priority <= 6 THEN 'medium' WHEN priority <= 8 THEN 'high' ELSE 'critical' END")
    
    # Add foreign keys
    op.create_foreign_key('fk_tasks_owner_id', 'tasks', 'users', ['owner_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_tasks_assigned_to', 'tasks', 'agents', ['assigned_to'], ['id'], ondelete='SET NULL')
    
    # Update constraints
    op.create_check_constraint('check_task_status_new', 'tasks', "status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled')")
    op.create_check_constraint('check_task_priority', 'tasks', "priority IN ('low', 'medium', 'high', 'critical')")


def downgrade():
    # Remove new constraints
    op.drop_constraint('check_task_priority', 'tasks', type_='check')
    op.drop_constraint('check_task_status_new', 'tasks', type_='check')
    
    # Remove foreign keys
    op.drop_constraint('fk_tasks_assigned_to', 'tasks', type_='foreignkey')
    op.drop_constraint('fk_tasks_owner_id', 'tasks', type_='foreignkey')
    
    # Remove new columns
    op.drop_column('tasks', 'updated_at')
    op.drop_column('tasks', 'task_metadata')
    op.drop_column('tasks', 'assigned_to')
    op.drop_column('tasks', 'task_type')
    op.drop_column('tasks', 'title')
    op.drop_column('tasks', 'owner_id')
    
    # Change priority back to integer
    op.alter_column('tasks', 'priority',
                    existing_type=sa.String(20),
                    type_=sa.INTEGER(),
                    existing_nullable=False,
                    postgresql_using="CASE WHEN priority = 'low' THEN 3 WHEN priority = 'medium' THEN 5 WHEN priority = 'high' THEN 8 ELSE 10 END")
    
    # Add old columns back
    op.add_column('tasks', sa.Column('started_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('tasks', sa.Column('assigned_agents', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True))
    op.add_column('tasks', sa.Column('deadline', sa.DateTime(timezone=True), nullable=True))
    op.add_column('tasks', sa.Column('requirements', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'))
    op.add_column('tasks', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Add old constraints
    op.create_check_constraint('check_priority_range', 'tasks', 'priority >= 1 AND priority <= 10')