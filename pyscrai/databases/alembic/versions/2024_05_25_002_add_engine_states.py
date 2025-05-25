"""add engine states and event updates

Revision ID: 2024_05_25_002
Revises: c15179238652
Create Date: 2024-05-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2024_05_25_002'
down_revision = 'c15179238652'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to event_types table
    op.add_column('event_types', sa.Column('category', sa.String(), nullable=True))
    op.add_column('event_types', sa.Column('engine_type', sa.String(), nullable=True))
    
    # Add new columns to event_instances table
    op.add_column('event_instances', sa.Column('processed_by_engines', sa.JSON(), nullable=True))
    op.add_column('event_instances', sa.Column('priority', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('event_instances', sa.Column('status', sa.String(), nullable=False, server_default='queued'))
    op.add_column('event_instances', sa.Column('lock_until', sa.DateTime(), nullable=True))
    op.add_column('event_instances', sa.Column('locked_by', sa.String(), nullable=True))
    op.add_column('event_instances', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('event_instances', sa.Column('last_error', sa.String(), nullable=True))
    op.add_column('event_instances', sa.Column('next_retry_time', sa.DateTime(), nullable=True))
    
    # Create new engine_states table
    op.create_table('engine_states',
        sa.Column('id', sa.String(), nullable=False),  # UUID as string
        sa.Column('engine_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('last_heartbeat', sa.DateTime(), nullable=True),
        sa.Column('current_workload', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_engine_states_engine_type'), 'engine_states', ['engine_type'], unique=False)
    op.create_index(op.f('ix_engine_states_status'), 'engine_states', ['status'], unique=False)
    op.create_index(op.f('ix_event_instances_status'), 'event_instances', ['status'], unique=False)
    op.create_index(op.f('ix_event_instances_priority'), 'event_instances', ['priority'], unique=False)
    op.create_index(op.f('ix_event_instances_lock_until'), 'event_instances', ['lock_until'], unique=False)
    op.create_index(op.f('ix_event_types_category'), 'event_types', ['category'], unique=False)
    op.create_index(op.f('ix_event_types_engine_type'), 'event_types', ['engine_type'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_event_types_engine_type'), table_name='event_types')
    op.drop_index(op.f('ix_event_types_category'), table_name='event_types')
    op.drop_index(op.f('ix_event_instances_lock_until'), table_name='event_instances')
    op.drop_index(op.f('ix_event_instances_priority'), table_name='event_instances')
    op.drop_index(op.f('ix_event_instances_status'), table_name='event_instances')
    op.drop_index(op.f('ix_engine_states_status'), table_name='engine_states')
    op.drop_index(op.f('ix_engine_states_engine_type'), table_name='engine_states')
    
    # Drop engine_states table
    op.drop_table('engine_states')
    
    # Drop columns from event_instances
    op.drop_column('event_instances', 'next_retry_time')
    op.drop_column('event_instances', 'last_error')
    op.drop_column('event_instances', 'retry_count')
    op.drop_column('event_instances', 'locked_by')
    op.drop_column('event_instances', 'lock_until')
    op.drop_column('event_instances', 'status')
    op.drop_column('event_instances', 'priority')
    op.drop_column('event_instances', 'processed_by_engines')
    
    # Drop columns from event_types
    op.drop_column('event_types', 'engine_type')
    op.drop_column('event_types', 'category')
