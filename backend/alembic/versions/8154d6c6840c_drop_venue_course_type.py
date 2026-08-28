"""drop venue course type

Revision ID: 8154d6c6840c
Revises: 42876360bc28
Create Date: 2026-08-27 20:28:57.719531

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8154d6c6840c'
down_revision: Union[str, Sequence[str], None] = '42876360bc28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

course_type_enum = postgresql.ENUM('scy', 'scm', 'lcm', name='course_type')


def upgrade() -> None:
    """Upgrade schema."""
    # All college swim meets are contested in a 25yd (SCY) pool, so the
    # course-type distinction on a venue was never meaningful here.
    op.drop_column('venues', 'course_type')
    # Autogenerate only drops the column — the enum type itself is orphaned
    # in Postgres unless dropped explicitly.
    course_type_enum.drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    """Downgrade schema."""
    course_type_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('venues', sa.Column('course_type', course_type_enum, autoincrement=False, nullable=True))
