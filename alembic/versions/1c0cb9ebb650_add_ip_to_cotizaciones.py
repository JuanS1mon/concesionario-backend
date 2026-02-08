# Alembic migration script
"""
Revision ID: 1c0cb9ebb650
Revises: b0f67e94d3d6
Create Date: 2026-02-07 20:27:33.757372
"""
revision = '1c0cb9ebb650'
down_revision = 'b0f67e94d3d6'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('cotizaciones', sa.Column('ip', sa.String(), nullable=True))


def downgrade():
    op.drop_column('cotizaciones', 'ip')
