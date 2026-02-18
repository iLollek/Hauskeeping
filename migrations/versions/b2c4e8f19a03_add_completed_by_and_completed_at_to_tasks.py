"""add completed_by and completed_at to tasks

Revision ID: b2c4e8f19a03
Revises: a968675a101b
Create Date: 2026-02-18 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c4e8f19a03'
down_revision = 'a968675a101b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('completed_by', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('completed_at', sa.DateTime(), nullable=True))
        batch_op.create_foreign_key('fk_tasks_completed_by', 'users', ['completed_by'], ['id'])


def downgrade():
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.drop_constraint('fk_tasks_completed_by', type_='foreignkey')
        batch_op.drop_column('completed_at')
        batch_op.drop_column('completed_by')
