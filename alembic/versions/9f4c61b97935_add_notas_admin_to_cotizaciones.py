# Alembic migration script
"""
Revision ID: 9f4c61b97935
Revises: 83c3dbcb07ad
Create Date: 2026-02-07 21:21:26.854523
"""
revision = '9f4c61b97935'
down_revision = '83c3dbcb07ad'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('cotizaciones', sa.Column('notas_admin', sa.String(), nullable=True))


def downgrade():
    op.drop_column('cotizaciones', 'notas_admin')
