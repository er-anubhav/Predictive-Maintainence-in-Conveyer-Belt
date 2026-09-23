"""Add multimodal fusion and camera evidence fields to telemetries table

Revision ID: 005_add_multimodal_fusion_fields
Revises: 004_add_ml_inference_fields
Create Date: 2026-09-22 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '005_add_multimodal_fusion_fields'
down_revision: Union[str, None] = '004_add_ml_inference_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('telemetries', sa.Column('operating_state', sa.String(length=32), nullable=True))
    op.add_column('telemetries', sa.Column('multimodal_state', sa.String(length=32), nullable=True))
    op.add_column('telemetries', sa.Column('fusion_reasons', sa.Text(), nullable=True))
    op.add_column('telemetries', sa.Column('camera_status', sa.String(length=32), nullable=True))
    op.add_column('telemetries', sa.Column('camera_frame_ref', sa.String(length=255), nullable=True))
    op.add_column('telemetries', sa.Column('camera_is_simulated', sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column('telemetries', 'camera_is_simulated')
    op.drop_column('telemetries', 'camera_frame_ref')
    op.drop_column('telemetries', 'camera_status')
    op.drop_column('telemetries', 'fusion_reasons')
    op.drop_column('telemetries', 'multimodal_state')
    op.drop_column('telemetries', 'operating_state')
