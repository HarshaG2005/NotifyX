"""CREATE USER TABLE

Revision ID: e1b7628fb6c0
Revises: 
Create Date: 2025-11-14 17:18:31.903745

"""
from typing import Sequence, Union
from sqlalchemy.dialects import postgresql

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1b7628fb6c0'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('email', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('password', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('TRUE')),

        # JSON preferences
        sa.Column(
            'preferences',
            postgresql.JSON(),
            server_default=sa.text(
                """'{"email": true, "sms": true, "push": true, "in_app": true}'"""
            )
        ),

        # timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )



def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('users')