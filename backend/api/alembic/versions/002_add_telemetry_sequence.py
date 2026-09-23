"""Add sequence column to telemetries table for duplicate detection

Revision ID: 002_add_telemetry_sequence
Revises: 001_initial_schema
Create Date: 2026-09-21 15:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_add_telemetry_sequence'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('telemetries', sa.Column('sequence', sa.BigInteger(), nullable=True))
    op.create_index(op.f('ix_telemetries_sequence'), 'telemetries', ['sequence'], unique=False)
    op.create_index('ix_telemetry_sensor_sequence', 'telemetries', ['sensor_node_id', 'sequence'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_telemetry_sensor_sequence', table_name='telemetries')
    op.drop_index(op.f('ix_telemetries_sequence'), table_name='telemetries')
    op.drop_column('telemetries', 'sequence')
