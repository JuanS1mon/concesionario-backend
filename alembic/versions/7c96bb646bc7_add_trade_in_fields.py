# Alembic migration script
"""
Revision ID: 7c96bb646bc7
Revises: d1e2f3a4b5c6
Create Date: 2026-02-09 13:00:19.175473
"""
from alembic import op
import sqlalchemy as sa

revision = '7c96bb646bc7'
down_revision = 'd1e2f3a4b5c6'
branch_labels = None
depends_on = None


def upgrade():
    # Agregar columna precio_compra
    op.add_column('autos', sa.Column('precio_compra', sa.Float(), nullable=True))
    
    # Agregar columna es_trade_in con valor por defecto False
    op.add_column('autos', sa.Column('es_trade_in', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    # Eliminar las columnas agregadas
    op.drop_column('autos', 'es_trade_in')
    op.drop_column('autos', 'precio_compra')
