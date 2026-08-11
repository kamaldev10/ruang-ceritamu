"""Add missing index on messages.is_read

Revision ID: 9a15e934aadf
Revises: 82d63c844155
Create Date: 2026-08-11 16:34:53.173717

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a15e934aadf'
down_revision = '82d63c844155'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_messages_is_read'), ['is_read'], unique=False)


def downgrade():
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_messages_is_read'))
