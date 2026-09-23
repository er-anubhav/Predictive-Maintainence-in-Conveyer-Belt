"""Add signal features (crest_factor, dominant_frequency_hz, spectral_energy) to telemetries table

Revision ID: 003_add_signal_features
Revises: 002_add_telemetry_sequence
Create Date: 2026-09-21 15:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_add_signal_features'
down_revision: Union[str, None] = '002_add_telemetry_sequence'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('telemetries', sa.Column('crest_factor', sa.Float(), nullable=True))
    op.add_column('telemetries', sa.Column('dominant_frequency_hz', sa.Float(), nullable=True))
    op.add_column('telemetries', sa.Column('spectral_energy', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('telemetries', 'spectral_energy')
    op.drop_column('telemetries', 'dominant_frequency_hz')
    op.drop_column('telemetries', 'crest_factor')
