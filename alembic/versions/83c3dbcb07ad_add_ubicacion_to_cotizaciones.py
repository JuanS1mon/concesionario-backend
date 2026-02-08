# Alembic migration script
"""
Revision ID: 83c3dbcb07ad
Revises: 1c0cb9ebb650
Create Date: 2026-02-07 20:45:39.813095
"""
revision = '83c3dbcb07ad'
down_revision = '1c0cb9ebb650'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('cotizaciones', sa.Column('ubicacion', sa.String(), nullable=True))


def downgrade():
    op.drop_column('cotizaciones', 'ubicacion')
