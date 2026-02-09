"""add_pricing_tables

Revision ID: d1e2f3a4b5c6
Revises: c1a2b3d4e5f6
Create Date: 2026-02-08 22:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd1e2f3a4b5c6'
down_revision = 'c1a2b3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # Tabla de listings crudos del scraping
    op.create_table('market_raw_listings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fuente', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('titulo', sa.String(), nullable=True),
        sa.Column('marca_raw', sa.String(), nullable=True),
        sa.Column('modelo_raw', sa.String(), nullable=True),
        sa.Column('anio', sa.Integer(), nullable=True),
        sa.Column('km', sa.Integer(), nullable=True),
        sa.Column('precio', sa.Float(), nullable=True),
        sa.Column('moneda', sa.String(), nullable=True),
        sa.Column('ubicacion', sa.String(), nullable=True),
        sa.Column('imagen_url', sa.String(), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.Column('procesado', sa.Boolean(), nullable=True),
        sa.Column('fecha_publicacion', sa.DateTime(), nullable=True),
        sa.Column('fecha_scraping', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_market_raw_listings_id'), 'market_raw_listings', ['id'], unique=False)
    op.create_index('ix_market_raw_fuente', 'market_raw_listings', ['fuente'], unique=False)
    op.create_index('ix_market_raw_marca_modelo', 'market_raw_listings', ['marca_raw', 'modelo_raw'], unique=False)

    # Tabla de listings normalizados
    op.create_table('market_listings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('raw_listing_id', sa.Integer(), nullable=True),
        sa.Column('fuente', sa.String(), nullable=False),
        sa.Column('marca_id', sa.Integer(), nullable=False),
        sa.Column('modelo_id', sa.Integer(), nullable=False),
        sa.Column('anio', sa.Integer(), nullable=False),
        sa.Column('km', sa.Integer(), nullable=True),
        sa.Column('precio', sa.Float(), nullable=False),
        sa.Column('moneda', sa.String(), nullable=True),
        sa.Column('ubicacion', sa.String(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.Column('fecha_publicacion', sa.DateTime(), nullable=True),
        sa.Column('fecha_scraping', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['raw_listing_id'], ['market_raw_listings.id'], ),
        sa.ForeignKeyConstraint(['marca_id'], ['marcas.id'], ),
        sa.ForeignKeyConstraint(['modelo_id'], ['modelos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_market_listings_id'), 'market_listings', ['id'], unique=False)
    op.create_index('ix_market_listings_comparables', 'market_listings', ['marca_id', 'modelo_id', 'anio'], unique=False)
    op.create_index('ix_market_listings_fuente', 'market_listings', ['fuente'], unique=False)


def downgrade():
    op.drop_index('ix_market_listings_fuente', table_name='market_listings')
    op.drop_index('ix_market_listings_comparables', table_name='market_listings')
    op.drop_index(op.f('ix_market_listings_id'), table_name='market_listings')
    op.drop_table('market_listings')

    op.drop_index('ix_market_raw_marca_modelo', table_name='market_raw_listings')
    op.drop_index('ix_market_raw_fuente', table_name='market_raw_listings')
    op.drop_index(op.f('ix_market_raw_listings_id'), table_name='market_raw_listings')
    op.drop_table('market_raw_listings')
