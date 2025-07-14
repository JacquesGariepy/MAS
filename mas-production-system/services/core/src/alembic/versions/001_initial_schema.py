"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create custom types
    op.execute("CREATE TYPE agent_status AS ENUM ('idle', 'working', 'negotiating', 'coordinating', 'error')")
    op.execute("CREATE TYPE agent_type AS ENUM ('reflexive', 'cognitive', 'hybrid')")
    op.execute("CREATE TYPE org_type AS ENUM ('hierarchy', 'market', 'network', 'team')")
    op.execute("CREATE TYPE memory_type AS ENUM ('semantic', 'episodic', 'working')")
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('username', sa.String(50), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False, default=False),
        sa.Column('agent_quota', sa.Integer(), nullable=False, default=10),
        sa.Column('api_calls_quota', sa.Integer(), nullable=False, default=10000),
        sa.Column('storage_quota_mb', sa.Integer(), nullable=False, default=1024),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
    )
    
    # Create indexes
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_active_verified', 'users', ['is_active', 'is_verified'])
    
    # Create agents table
    op.create_table(
        'agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('agent_type', postgresql.ENUM('reflexive', 'cognitive', 'hybrid', name='agent_type'), nullable=False),
        sa.Column('beliefs', postgresql.JSONB(), nullable=False, default={}),
        sa.Column('desires', postgresql.ARRAY(sa.String), nullable=False, default=[]),
        sa.Column('intentions', postgresql.ARRAY(sa.String), nullable=False, default=[]),
        sa.Column('capabilities', postgresql.ARRAY(sa.String), nullable=False, default=[]),
        sa.Column('reactive_rules', postgresql.JSONB(), default={}),
        sa.Column('configuration', postgresql.JSONB(), default={}),
        sa.Column('status', postgresql.ENUM('idle', 'working', 'negotiating', 'coordinating', 'error', name='agent_status'), nullable=False, default='idle'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('total_actions', sa.Integer(), nullable=False, default=0),
        sa.Column('successful_actions', sa.Integer(), nullable=False, default=0),
        sa.Column('total_messages', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('last_active_at', sa.DateTime(timezone=True)),
    )
    
    # Create indexes
    op.create_index('ix_agents_owner_active', 'agents', ['owner_id', 'is_active'])
    op.create_index('ix_agents_type_status', 'agents', ['agent_type', 'status'])
    
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('org_type', postgresql.ENUM('hierarchy', 'market', 'network', 'team', name='org_type'), nullable=False),
        sa.Column('roles', postgresql.JSONB(), nullable=False, default={}),
        sa.Column('norms', postgresql.JSONB(), nullable=False, default=[]),
        sa.Column('structure', postgresql.JSONB(), default={}),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('member_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Create agent_organization association table
    op.create_table(
        'agent_organization',
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='CASCADE')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE')),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('agent_id', 'organization_id', name='uq_agent_org'),
    )
    
    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('receiver_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('performative', sa.String(20), nullable=False),
        sa.Column('content', postgresql.JSONB(), nullable=False),
        sa.Column('protocol', sa.String(20), nullable=False, default='fipa-acl'),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('in_reply_to', postgresql.UUID(as_uuid=True)),
        sa.Column('is_read', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Create indexes
    op.create_index('ix_messages_conversation', 'messages', ['conversation_id', 'created_at'])
    op.create_index('ix_messages_receiver_unread', 'messages', ['receiver_id', 'is_read'])
    
    # Create memories table with vector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    op.create_table(
        'memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', postgresql.ARRAY(sa.Float)),
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.Column('memory_type', postgresql.ENUM('semantic', 'episodic', 'working', name='memory_type'), nullable=False),
        sa.Column('importance', sa.Float(), nullable=False, default=0.5),
        sa.Column('access_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True)),
    )
    
    # Create indexes including vector index
    op.create_index('ix_memories_agent_type', 'memories', ['agent_id', 'memory_type'])
    op.create_index('ix_memories_importance', 'memories', ['importance'])
    
    # Create GIN index for JSONB columns
    op.execute('CREATE INDEX ix_agents_beliefs_gin ON agents USING gin(beliefs)')
    op.execute('CREATE INDEX ix_agents_configuration_gin ON agents USING gin(configuration)')
    op.execute('CREATE INDEX ix_memories_metadata_gin ON memories USING gin(metadata)')

def downgrade():
    op.drop_table('memories')
    op.drop_table('messages')
    op.drop_table('agent_organization')
    op.drop_table('organizations')
    op.drop_table('agents')
    op.drop_table('users')
    
    op.execute('DROP TYPE IF EXISTS memory_type')
    op.execute('DROP TYPE IF EXISTS org_type')
    op.execute('DROP TYPE IF EXISTS agent_type')
    op.execute('DROP TYPE IF EXISTS agent_status')