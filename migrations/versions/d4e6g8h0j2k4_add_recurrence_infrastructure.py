"""add recurrence infrastructure (parent_task_id + app_state)

Revision ID: d4e6g8h0j2k4
Revises: c3d5f7a21b04
Create Date: 2026-02-19 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e6g8h0j2k4'
down_revision = 'c3d5f7a21b04'
branch_labels = None
depends_on = None


def upgrade():
    # Neue Tabelle: app_state (Key-Value fuer internen App-Zustand)
    op.create_table(
        'app_state',
        sa.Column('key', sa.String(50), nullable=False),
        sa.Column('value', sa.String(200), nullable=False),
        sa.PrimaryKeyConstraint('key'),
    )

    # Spalte parent_task_id zu tasks hinzufuegen
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parent_task_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_tasks_parent_task_id', 'tasks', ['parent_task_id'], ['id']
        )


def downgrade():
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.drop_constraint('fk_tasks_parent_task_id', type_='foreignkey')
        batch_op.drop_column('parent_task_id')

    op.drop_table('app_state')
