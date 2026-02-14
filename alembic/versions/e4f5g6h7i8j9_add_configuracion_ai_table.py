"""add_configuracion_ai_table

Revision ID: e4f5g6h7i8j9
Revises: d1e2f3a4b5c6
Create Date: 2026-02-13 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e4f5g6h7i8j9'
down_revision = 'd1e2f3a4b5c6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('configuracion_ai',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('proveedor', sa.String(), nullable=False),
        sa.Column('api_key', sa.String(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_configuracion_ai_id'), 'configuracion_ai', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_configuracion_ai_id'), table_name='configuracion_ai')
    op.drop_table('configuracion_ai')
