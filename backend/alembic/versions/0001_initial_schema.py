"""Initial schema for the manufacturing decision copilot.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-09 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depend_on = None


def upgrade() -> None:
    op.create_table(
        'products',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
    )

    op.create_table(
        'requirements',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('product_id', sa.String(), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('field', sa.String(), nullable=False),
        sa.Column('operator', sa.String(), nullable=False),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('mandatory', sa.Boolean(), nullable=True, server_default=sa.sql.expression.true()),
    )

    op.create_table(
        'suppliers',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('location', sa.String(), nullable=True),
    )

    op.create_table(
        'supplier_facts',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('supplier_id', sa.String(), sa.ForeignKey('suppliers.id'), nullable=False),
        sa.Column('field', sa.String(), nullable=False),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('source_doc', sa.String(), nullable=False),
        sa.Column('source_field', sa.String(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True, server_default='1.0'),
        sa.Column('retrieved_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'quotations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('supplier_id', sa.String(), sa.ForeignKey('suppliers.id'), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(), nullable=True, server_default='USD'),
        sa.Column('moq', sa.Integer(), nullable=True),
        sa.Column('lead_time_days', sa.Integer(), nullable=True),
        sa.Column('incoterm', sa.String(), nullable=True),
        sa.Column('valid_until', sa.String(), nullable=True),
    )

    op.create_table(
        'evidence_chunks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('supplier_id', sa.String(), sa.ForeignKey('suppliers.id'), nullable=False),
        sa.Column('doc_id', sa.String(), nullable=False),
        sa.Column('source_field', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
    )

    op.create_table(
        'evaluation_runs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('metric', sa.String(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('evaluation_runs')
    op.drop_table('evidence_chunks')
    op.drop_table('quotations')
    op.drop_table('supplier_facts')
    op.drop_table('suppliers')
    op.drop_table('requirements')
    op.drop_table('products')
