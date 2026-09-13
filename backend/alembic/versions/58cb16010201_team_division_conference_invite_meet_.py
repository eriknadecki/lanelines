"""team division conference, invite meet type

Revision ID: 58cb16010201
Revises: 67588807744a
Create Date: 2026-09-13 15:05:28.524740

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '58cb16010201'
down_revision: Union[str, Sequence[str], None] = '67588807744a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TEAM_CONFERENCE_VALUES = [
    'America East Conference', 'American Athletic Conference', 'Atlantic 10 Conference',
    'Atlantic Coast Conference', 'Atlantic Sun Conference', 'Big 12 Conference', 'Big East Conference',
    'Big Ten Conference', 'Big West Conference', 'Coastal Athletic Association', 'Horizon League',
    'Ivy League', 'Metro Atlantic Athletic Conference', 'Mid-American Conference',
    'Missouri Valley Conference', 'Mountain West Conference', 'Northeast Conference', 'Pac-12 Conference',
    'Patriot League', 'Southeastern Conference', 'Southern Conference', 'Summit League',
    'Sun Belt Conference', 'West Coast Conference', 'Mountain Pacific Sports Federation',
    'Metropolitan Swimming Conference', 'California Collegiate Athletic Association',
    'Central Atlantic Collegiate Conference', 'Conference Carolinas', 'East Coast Conference',
    'Great Lakes Intercollegiate Athletic Conference', 'Great Lakes Valley Conference',
    'Great Midwest Athletic Conference', 'Lone Star Conference', 'Mountain East Conference',
    'Northeast-10 Conference', 'Northern Sun Intercollegiate Conference', 'Peach Belt Conference',
    'Pennsylvania State Athletic Conference', 'Rocky Mountain Athletic Conference',
    'South Atlantic Conference', 'Sunshine State Conference', 'Appalachian Swimming Conference',
    'New South Intercollegiate Swim Conference', 'Pacific Coast Swim Conference',
    'Allegheny Mountain Collegiate Conference', 'American Rivers Conference',
    'American Southwest Conference', 'Atlantic East Conference', 'Centennial Conference',
    'City University of New York Athletic Conference', 'Coast to Coast Athletic Conference',
    'College Conference of Illinois and Wisconsin', 'Collegiate Conference of the South',
    'Conference of New England', 'Empire 8', 'Great Northeast Athletic Conference',
    'Heartland Collegiate Athletic Conference', 'Landmark Conference', 'Liberty League',
    'Little East Conference', 'Michigan Intercollegiate Athletic Association',
    'Middle Atlantic Conferences', 'Midwest Conference', 'Minnesota Intercollegiate Athletic Conference',
    'New England Collegiate Conference', 'New England Small College Athletic Conference',
    "New England Women's and Men's Athletic Conference", 'New Jersey Athletic Conference',
    'North Atlantic Conference', 'North Coast Athletic Conference', 'Northwest Conference',
    'Ohio Athletic Conference', 'Old Dominion Athletic Conference', "Presidents' Athletic Conference",
    'Skyline Conference', 'Southern Athletic Association',
    'Southern California Intercollegiate Athletic Conference', 'Southern Collegiate Athletic Conference',
    'State University of New York Athletic Conference', 'United East Conference',
    'University Athletic Association', 'USA South Athletic Conference',
    'Wisconsin Intercollegiate Athletic Conference',
]


def upgrade() -> None:
    """Upgrade schema."""
    # Postgres won't let a new enum value be used in the same transaction
    # that adds it, and autogenerate doesn't detect new values on an
    # existing native enum anyway — added by hand, matching the pattern used
    # for adding 'tri' to meet_type in 54c829fa8854.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE meet_type ADD VALUE IF NOT EXISTS 'invite'")

    # add_column (unlike create_table) doesn't auto-create the backing
    # Postgres enum type, so it must be created explicitly first.
    team_division = sa.Enum('D1', 'D2', 'D3', name='team_division')
    team_division.create(op.get_bind(), checkfirst=True)
    op.add_column('teams', sa.Column('division', team_division, nullable=True))

    team_conference = sa.Enum(*TEAM_CONFERENCE_VALUES, name='team_conference')
    team_conference.create(op.get_bind(), checkfirst=True)
    op.add_column('teams', sa.Column('conference', team_conference, nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('teams', 'conference')
    op.drop_column('teams', 'division')
    sa.Enum(name='team_conference').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='team_division').drop(op.get_bind(), checkfirst=True)
    # Postgres has no ALTER TYPE ... DROP VALUE, so the 'invite' meet_type
    # value can't be cleanly removed here — a downgrade leaves it in place.
