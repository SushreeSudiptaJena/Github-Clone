"""create initial tables

Revision ID: 0001_create_tables
Revises: 
Create Date: 2026-02-05 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_create_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_user_username', 'user', ['username'])

    op.create_table(
        'session',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'message',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    op.create_foreign_key('fk_session_user', 'session', 'user', ['user_id'], ['id'])
    op.create_foreign_key('fk_message_session', 'message', 'session', ['session_id'], ['id'])


def downgrade():
    op.drop_constraint('fk_message_session', 'message', type_='foreignkey')
    op.drop_constraint('fk_session_user', 'session', type_='foreignkey')
    op.drop_table('message')
    op.drop_table('session')
    op.drop_index('ix_user_username', table_name='user')
    op.drop_table('user')
