"""add_ventas_table

Revision ID: c1a2b3d4e5f6
Revises: bd97f14bb50c
Create Date: 2026-02-08 18:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c1a2b3d4e5f6'
down_revision = 'bd97f14bb50c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('ventas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=False),
        sa.Column('auto_vendido_id', sa.Integer(), nullable=False),
        sa.Column('precio_venta', sa.Float(), nullable=False),
        sa.Column('auto_tomado_id', sa.Integer(), nullable=True),
        sa.Column('precio_toma', sa.Float(), nullable=True),
        sa.Column('es_parte_pago', sa.Boolean(), nullable=True),
        sa.Column('diferencia', sa.Float(), nullable=True),
        sa.Column('ganancia_estimada', sa.Float(), nullable=True),
        sa.Column('cotizacion_id', sa.Integer(), nullable=True),
        sa.Column('oportunidad_id', sa.Integer(), nullable=True),
        sa.Column('estado', sa.String(), nullable=True),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('fecha_venta', sa.DateTime(), nullable=True),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=True),
        sa.Column('fecha_actualizacion', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id'], ),
        sa.ForeignKeyConstraint(['auto_vendido_id'], ['autos.id'], ),
        sa.ForeignKeyConstraint(['auto_tomado_id'], ['autos.id'], ),
        sa.ForeignKeyConstraint(['cotizacion_id'], ['cotizaciones.id'], ),
        sa.ForeignKeyConstraint(['oportunidad_id'], ['oportunidades.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ventas_id'), 'ventas', ['id'], unique=False)
    op.create_index(op.f('ix_ventas_cliente_id'), 'ventas', ['cliente_id'], unique=False)
    op.create_index(op.f('ix_ventas_auto_vendido_id'), 'ventas', ['auto_vendido_id'], unique=False)
    op.create_index(op.f('ix_ventas_estado'), 'ventas', ['estado'], unique=False)
    op.create_index(op.f('ix_ventas_fecha_venta'), 'ventas', ['fecha_venta'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_ventas_fecha_venta'), table_name='ventas')
    op.drop_index(op.f('ix_ventas_estado'), table_name='ventas')
    op.drop_index(op.f('ix_ventas_auto_vendido_id'), table_name='ventas')
    op.drop_index(op.f('ix_ventas_cliente_id'), table_name='ventas')
    op.drop_index(op.f('ix_ventas_id'), table_name='ventas')
    op.drop_table('ventas')
