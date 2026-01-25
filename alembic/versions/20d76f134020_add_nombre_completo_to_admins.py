# Alembic migration script
"""
Revision ID: 20d76f134020
Revises: 55e169a86147
Create Date: 2026-01-25 15:54:59.075456
"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('admins', sa.Column('nombre_completo', sa.String(), nullable=True))

def downgrade():
    op.drop_column('admins', 'nombre_completo')
