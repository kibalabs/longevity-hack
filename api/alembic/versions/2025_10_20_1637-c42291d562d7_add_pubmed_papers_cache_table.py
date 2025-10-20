"""add_pubmed_papers_cache_table

Revision ID: c42291d562d7
Revises: aa96371385df
Create Date: 2025-10-20 16:37:11.275945

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c42291d562d7'
down_revision = 'aa96371385df'
branch_labels = None
depends_on = None


def upgrade():
    # Create PubMed papers cache table
    op.create_table(
        'tbl_pubmed_papers',
        sa.Column('pubmed_id', sa.String(), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('authors', sa.Text(), nullable=True),
        sa.Column('journal', sa.String(), nullable=True),
        sa.Column('year', sa.String(), nullable=True),
        sa.Column('fetched_date', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('pubmed_id'),
    )
    op.create_index('idx_pubmed_papers_fetched_date', 'tbl_pubmed_papers', ['fetched_date'])


def downgrade():
    op.drop_index('idx_pubmed_papers_fetched_date', table_name='tbl_pubmed_papers')
    op.drop_table('tbl_pubmed_papers')
