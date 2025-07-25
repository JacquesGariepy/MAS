"""
SQLAlchemy models with proper indexing and constraints
"""

from uuid import uuid4

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey,
    Table, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

Base = declarative_base()

# Association tables
agent_organization = Table(
    'agent_organization',
    Base.metadata,
    Column('agent_id', UUID(as_uuid=True), ForeignKey('agents.id', ondelete='CASCADE')),
    Column('organization_id', UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE')),
    Column('role', String(50), nullable=False),
    Column('joined_at', DateTime(timezone=True), server_default=func.now()),
    UniqueConstraint('agent_id', 'organization_id', name='uq_agent_org'),
    Index('ix_agent_org_role', 'role')
)

class User(Base):
    """User model with authentication and quotas"""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    
    # Quotas
    agent_quota = Column(Integer, default=10, nullable=False)
    api_calls_quota = Column(Integer, default=10000, nullable=False)
    storage_quota_mb = Column(Integer, default=1024, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))
    
    # Relationships
    agents = relationship("Agent", back_populates="owner", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint('agent_quota >= 0', name='check_agent_quota_positive'),
        CheckConstraint('api_calls_quota >= 0', name='check_api_quota_positive'),
        Index('ix_user_active_verified', 'is_active', 'is_verified'),
    )

class APIKey(Base):
    """API Key model for authentication"""
    __tablename__ = 'api_keys'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    
    permissions = Column(ARRAY(String), default=list, nullable=False)
    rate_limit = Column(Integer, default=1000, nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True))
    last_used_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")

class Agent(Base):
    """Agent model with complete BDI architecture"""
    __tablename__ = 'agents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)
    agent_type = Column(String(20), nullable=False, default='cognitive')
    
    # BDI Model
    beliefs = Column(JSONB, default=dict, nullable=False)
    desires = Column(ARRAY(String), default=list, nullable=False)
    intentions = Column(ARRAY(String), default=list, nullable=False)
    
    # Capabilities and configuration
    capabilities = Column(ARRAY(String), default=list, nullable=False)
    reactive_rules = Column(JSONB, default=dict)
    configuration = Column(JSONB, default=dict)
    
    # State
    status = Column(String(20), default='idle', nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Performance metrics
    total_actions = Column(Integer, default=0, nullable=False)
    successful_actions = Column(Integer, default=0, nullable=False)
    total_messages = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_active_at = Column(DateTime(timezone=True))
    
    # Relationships
    owner = relationship("User", back_populates="agents")
    organizations = relationship("Organization", secondary=agent_organization, back_populates="agents")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    memories = relationship("Memory", back_populates="agent", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_agent_owner_active', 'owner_id', 'is_active'),
        Index('ix_agent_type_status', 'agent_type', 'status'),
        CheckConstraint("status IN ('idle', 'working', 'negotiating', 'coordinating', 'error')", name='check_agent_status'),
        CheckConstraint("agent_type IN ('reflexive', 'cognitive', 'hybrid')", name='check_agent_type'),
    )
    
    @validates('beliefs', 'configuration')
    def validate_json(self, key, value):
        """Ensure JSON fields are dictionaries"""
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError(f"{key} must be a dictionary")
        return value

class Organization(Base):
    """Organization model with flexible structure"""
    __tablename__ = 'organizations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    name = Column(String(100), nullable=False)
    org_type = Column(String(20), nullable=False)
    
    # Structure and rules
    roles = Column(JSONB, default=dict, nullable=False)
    norms = Column(JSONB, default=list, nullable=False)
    structure = Column(JSONB, default=dict)
    
    # State
    is_active = Column(Boolean, default=True, nullable=False)
    member_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    agents = relationship("Agent", secondary=agent_organization, back_populates="organizations")
    
    __table_args__ = (
        Index('ix_org_owner_active', 'owner_id', 'is_active'),
        CheckConstraint("org_type IN ('hierarchy', 'market', 'network', 'team')", name='check_org_type'),
        CheckConstraint('member_count >= 0', name='check_member_count_positive'),
    )

class Message(Base):
    """Message model for agent communication"""
    __tablename__ = 'messages'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    sender_id = Column(UUID(as_uuid=True), ForeignKey('agents.id', ondelete='CASCADE'), nullable=False)
    receiver_id = Column(UUID(as_uuid=True), ForeignKey('agents.id', ondelete='CASCADE'), nullable=False)
    
    performative = Column(String(20), nullable=False)
    content = Column(JSONB, nullable=False)
    protocol = Column(String(20), default='fipa-acl', nullable=False)
    
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    in_reply_to = Column(UUID(as_uuid=True))
    
    is_read = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    sender = relationship("Agent", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("Agent", foreign_keys=[receiver_id], back_populates="received_messages")
    
    __table_args__ = (
        Index('ix_message_conversation', 'conversation_id', 'created_at'),
        Index('ix_message_receiver_unread', 'receiver_id', 'is_read'),
        CheckConstraint("performative IN ('inform', 'request', 'propose', 'accept', 'reject', 'query', 'subscribe')", 
                        name='check_performative'),
    )

class Memory(Base):
    """Semantic memory storage for agents"""
    __tablename__ = 'memories'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id', ondelete='CASCADE'), nullable=False)
    
    content = Column(Text, nullable=False)
    embedding = Column(ARRAY(Float))  # Vector embedding
    memory_metadata = Column(JSONB, default=dict)  # Renamed from metadata
    
    memory_type = Column(String(20), default='semantic', nullable=False)
    importance = Column(Float, default=0.5, nullable=False)
    access_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_accessed_at = Column(DateTime(timezone=True))
    
    # Relationships
    agent = relationship("Agent", back_populates="memories")
    
    __table_args__ = (
        Index('ix_memory_agent_type', 'agent_id', 'memory_type'),
        Index('ix_memory_importance', 'importance'),
        CheckConstraint('importance >= 0 AND importance <= 1', name='check_importance_range'),
        CheckConstraint("memory_type IN ('semantic', 'episodic', 'working')", name='check_memory_type'),
    )

class Task(Base):
    """Task model for coordination"""
    __tablename__ = 'tasks'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    task_type = Column(String(50), nullable=False)
    
    status = Column(String(20), default='pending', nullable=False)
    priority = Column(String(20), default='medium', nullable=False)
    
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('agents.id', ondelete='SET NULL'))
    task_metadata = Column(JSONB, default=dict, nullable=False)
    
    result = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('ix_task_status_priority', 'status', 'priority'),
        CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled')", 
                        name='check_task_status'),
        CheckConstraint("priority IN ('low', 'medium', 'high', 'critical')", name='check_task_priority'),
    )

class Negotiation(Base):
    """Negotiation tracking"""
    __tablename__ = 'negotiations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    initiator_id = Column(UUID(as_uuid=True), ForeignKey('agents.id', ondelete='CASCADE'), nullable=False)
    
    negotiation_type = Column(String(20), nullable=False)
    subject = Column(JSONB, nullable=False)
    participants = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    
    status = Column(String(20), default='active', nullable=False)
    result = Column(JSONB)
    
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('ix_negotiation_status', 'status', 'started_at'),
        CheckConstraint("negotiation_type IN ('bilateral', 'multilateral', 'mediated', 'integrative')", 
                        name='check_negotiation_type'),
        CheckConstraint("status IN ('active', 'completed', 'failed', 'cancelled')", 
                        name='check_negotiation_status'),
    )

class Auction(Base):
    """Auction model"""
    __tablename__ = 'auctions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    auctioneer_id = Column(UUID(as_uuid=True), ForeignKey('agents.id', ondelete='CASCADE'), nullable=False)
    
    auction_type = Column(String(20), nullable=False)
    item_description = Column(Text, nullable=False)
    
    starting_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    reserve_price = Column(Float)
    
    status = Column(String(20), default='open', nullable=False)
    winner_id = Column(UUID(as_uuid=True), ForeignKey('agents.id', ondelete='SET NULL'))
    final_price = Column(Float)
    
    starts_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    
    bids = relationship("Bid", back_populates="auction", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_auction_status_ends', 'status', 'ends_at'),
        CheckConstraint("auction_type IN ('english', 'dutch', 'vickrey', 'double')", 
                        name='check_auction_type'),
        CheckConstraint("status IN ('open', 'closed', 'cancelled')", 
                        name='check_auction_status'),
        CheckConstraint('starting_price >= 0', name='check_starting_price_positive'),
        CheckConstraint('current_price >= 0', name='check_current_price_positive'),
    )

class Bid(Base):
    """Bid model for auctions"""
    __tablename__ = 'bids'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    auction_id = Column(UUID(as_uuid=True), ForeignKey('auctions.id', ondelete='CASCADE'), nullable=False)
    bidder_id = Column(UUID(as_uuid=True), ForeignKey('agents.id', ondelete='CASCADE'), nullable=False)
    
    amount = Column(Float, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    auction = relationship("Auction", back_populates="bids")
    
    __table_args__ = (
        UniqueConstraint('auction_id', 'bidder_id', 'amount', name='uq_auction_bidder_amount'),
        Index('ix_bid_auction_amount', 'auction_id', 'amount'),
        CheckConstraint('amount > 0', name='check_bid_amount_positive'),
    )

class AuditLog(Base):
    """Audit log for compliance and debugging"""
    __tablename__ = 'audit_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(UUID(as_uuid=True))
    
    details = Column(JSONB, default=dict)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('ix_audit_user_action', 'user_id', 'action', 'created_at'),
        Index('ix_audit_resource', 'resource_type', 'resource_id', 'created_at'),
    )