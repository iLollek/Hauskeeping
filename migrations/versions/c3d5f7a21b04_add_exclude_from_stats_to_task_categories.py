"""add exclude_from_stats to task_categories

Revision ID: c3d5f7a21b04
Revises: b2c4e8f19a03
Create Date: 2026-02-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d5f7a21b04'
down_revision = 'b2c4e8f19a03'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('task_categories', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'exclude_from_stats',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ))


def downgrade():
    with op.batch_alter_table('task_categories', schema=None) as batch_op:
        batch_op.drop_column('exclude_from_stats')
