"""Initial schema for SIH 26008 conveyor predictive maintenance

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-21 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create mines table
    op.create_table(
        'mines',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mines_name'), 'mines', ['name'], unique=False)

    # 2. Create conveyors table
    op.create_table(
        'conveyors',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('mine_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('belt_type', sa.String(length=100), nullable=False),
        sa.Column('length', sa.Float(), nullable=False),
        sa.Column('width', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='OPERATIONAL'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['mine_id'], ['mines.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conveyors_mine_id'), 'conveyors', ['mine_id'], unique=False)
    op.create_index(op.f('ix_conveyors_name'), 'conveyors', ['name'], unique=False)

    # 3. Create sensor_nodes table
    op.create_table(
        'sensor_nodes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('conveyor_id', sa.Integer(), nullable=False),
        sa.Column('node_code', sa.String(length=100), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('firmware_version', sa.String(length=50), nullable=False, server_default='v1.0.0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ONLINE'),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conveyor_id'], ['conveyors.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sensor_nodes_conveyor_id'), 'sensor_nodes', ['conveyor_id'], unique=False)
    op.create_index(op.f('ix_sensor_nodes_node_code'), 'sensor_nodes', ['node_code'], unique=True)

    # 4. Create telemetries table
    op.create_table(
        'telemetries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('sensor_node_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('vibration_rms', sa.Float(), nullable=False),
        sa.Column('vibration_peak', sa.Float(), nullable=False),
        sa.Column('vibration_kurtosis', sa.Float(), nullable=False),
        sa.Column('acoustic_rms', sa.Float(), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=False),
        sa.Column('belt_speed', sa.Float(), nullable=False),
        sa.Column('load', sa.Float(), nullable=False),
        sa.Column('tracking_position', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['sensor_node_id'], ['sensor_nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_telemetries_sensor_node_id'), 'telemetries', ['sensor_node_id'], unique=False)
    op.create_index(op.f('ix_telemetries_timestamp'), 'telemetries', ['timestamp'], unique=False)
    op.create_index('ix_telemetry_sensor_timestamp', 'telemetries', ['sensor_node_id', 'timestamp'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_telemetry_sensor_timestamp', table_name='telemetries')
    op.drop_index(op.f('ix_telemetries_timestamp'), table_name='telemetries')
    op.drop_index(op.f('ix_telemetries_sensor_node_id'), table_name='telemetries')
    op.drop_table('telemetries')

    op.drop_index(op.f('ix_sensor_nodes_node_code'), table_name='sensor_nodes')
    op.drop_index(op.f('ix_sensor_nodes_conveyor_id'), table_name='sensor_nodes')
    op.drop_table('sensor_nodes')

    op.drop_index(op.f('ix_conveyors_name'), table_name='conveyors')
    op.drop_index(op.f('ix_conveyors_mine_id'), table_name='conveyors')
    op.drop_table('conveyors')

    op.drop_index(op.f('ix_mines_name'), table_name='mines')
    op.drop_table('mines')
