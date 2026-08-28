"""venue name uniqueness

Revision ID: 67588807744a
Revises: 8154d6c6840c
Create Date: 2026-08-27 21:39:07.314948

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67588807744a'
down_revision: Union[str, Sequence[str], None] = '8154d6c6840c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint('venues_name_key', 'venues', ['name'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('venues_name_key', 'venues', type_='unique')
