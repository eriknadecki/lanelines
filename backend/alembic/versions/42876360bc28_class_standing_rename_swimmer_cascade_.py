"""class standing rename, swimmer cascade delete

Revision ID: 42876360bc28
Revises: 54c829fa8854
Create Date: 2026-08-27 09:51:50.306174

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42876360bc28'
down_revision: Union[str, Sequence[str], None] = '54c829fa8854'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename + retype in place (not drop+add, autogenerate's default guess)
    # so any real roster data survives: class_year was a graduation-year
    # int, class_standing is a free-form string (FR/SO/JR/SR/etc).
    op.alter_column(
        'swimmers',
        'class_year',
        new_column_name='class_standing',
        type_=sa.String(length=10),
        postgresql_using='class_year::VARCHAR(10)',
    )
    op.drop_constraint(op.f('swimmers_team_id_fkey'), 'swimmers', type_='foreignkey')
    op.create_foreign_key(None, 'swimmers', 'teams', ['team_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, 'swimmers', type_='foreignkey')
    op.create_foreign_key(op.f('swimmers_team_id_fkey'), 'swimmers', 'teams', ['team_id'], ['id'])
    op.alter_column(
        'swimmers',
        'class_standing',
        new_column_name='class_year',
        type_=sa.Integer(),
        postgresql_using='NULLIF(class_standing, \'\')::INTEGER',
    )
