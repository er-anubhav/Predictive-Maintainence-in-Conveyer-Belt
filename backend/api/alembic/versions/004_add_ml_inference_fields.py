"""Add ML inference evidence fields to telemetries table

Revision ID: 004_add_ml_inference_fields
Revises: 003_add_signal_features
Create Date: 2026-09-22 21:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004_add_ml_inference_fields'
down_revision: Union[str, None] = '003_add_signal_features'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('telemetries', sa.Column('model_version', sa.String(length=32), nullable=True))
    op.add_column('telemetries', sa.Column('anomaly_score', sa.Float(), nullable=True))
    op.add_column('telemetries', sa.Column('composite_z_deviation', sa.Float(), nullable=True))
    op.add_column('telemetries', sa.Column('persistence_3of5', sa.Boolean(), nullable=True))
    op.add_column('telemetries', sa.Column('persistence_5of9', sa.Boolean(), nullable=True))
    op.add_column('telemetries', sa.Column('alert_state', sa.String(length=32), nullable=True))
    op.add_column('telemetries', sa.Column('data_quality', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('telemetries', 'data_quality')
    op.drop_column('telemetries', 'alert_state')
    op.drop_column('telemetries', 'persistence_5of9')
    op.drop_column('telemetries', 'persistence_3of5')
    op.drop_column('telemetries', 'composite_z_deviation')
    op.drop_column('telemetries', 'anomaly_score')
    op.drop_column('telemetries', 'model_version')
