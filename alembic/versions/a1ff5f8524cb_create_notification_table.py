"""CREATE NOTIFICATION TABLE

Revision ID: a1ff5f8524cb
Revises: e1b7628fb6c0
Create Date: 2025-11-14 17:37:21.737737

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from app.models import NotificationStatus


# revision identifiers, used by Alembic.
revision: str = 'a1ff5f8524cb'
down_revision: Union[str, Sequence[str], None] = 'e1b7628fb6c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Enum must be created in the database first
# create enum type safely
notification_status_enum = postgresql.ENUM(
    'PENDING', 'SENT', 'FAILED', 'RETRYING',
    name='notificationstatusenum',
    create_type=False  # <- don't auto-create, we'll handle manually
)


def upgrade():
    # create enum only if it doesn't exist
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notificationstatusenum') THEN CREATE TYPE notificationstatusenum AS ENUM ('PENDING', 'SENT', 'FAILED', 'RETRYING'); END IF; END $$;")
    
    op.create_table(
        'notifications',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column('title', sa.String, nullable=False),
        sa.Column('message', sa.String, nullable=False),
        sa.Column('channels', sa.JSON, nullable=False),
        sa.Column('status', notification_status_enum, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade():
    op.drop_table('notifications')
    op.execute("DROP TYPE IF EXISTS notificationstatusenum;")