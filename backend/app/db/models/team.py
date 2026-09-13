import uuid
from enum import StrEnum

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TeamDivision(StrEnum):
    d1 = "D1"
    d2 = "D2"
    d3 = "D3"


class TeamConference(StrEnum):
    # Division I
    america_east_conference = "America East Conference"
    american_athletic_conference = "American Athletic Conference"
    atlantic_10_conference = "Atlantic 10 Conference"
    atlantic_coast_conference = "Atlantic Coast Conference"
    atlantic_sun_conference = "Atlantic Sun Conference"
    big_12_conference = "Big 12 Conference"
    big_east_conference = "Big East Conference"
    big_ten_conference = "Big Ten Conference"
    big_west_conference = "Big West Conference"
    coastal_athletic_association = "Coastal Athletic Association"
    horizon_league = "Horizon League"
    ivy_league = "Ivy League"
    metro_atlantic_athletic_conference = "Metro Atlantic Athletic Conference"
    mid_american_conference = "Mid-American Conference"
    missouri_valley_conference = "Missouri Valley Conference"
    mountain_west_conference = "Mountain West Conference"
    northeast_conference = "Northeast Conference"
    pac_12_conference = "Pac-12 Conference"
    patriot_league = "Patriot League"
    southeastern_conference = "Southeastern Conference"
    southern_conference = "Southern Conference"
    summit_league = "Summit League"
    sun_belt_conference = "Sun Belt Conference"
    west_coast_conference = "West Coast Conference"
    mountain_pacific_sports_federation = "Mountain Pacific Sports Federation"
    metropolitan_swimming_conference = "Metropolitan Swimming Conference"

    # Division II
    california_collegiate_athletic_association = "California Collegiate Athletic Association"
    central_atlantic_collegiate_conference = "Central Atlantic Collegiate Conference"
    conference_carolinas = "Conference Carolinas"
    east_coast_conference = "East Coast Conference"
    great_lakes_intercollegiate_athletic_conference = "Great Lakes Intercollegiate Athletic Conference"
    great_lakes_valley_conference = "Great Lakes Valley Conference"
    great_midwest_athletic_conference = "Great Midwest Athletic Conference"
    lone_star_conference = "Lone Star Conference"
    mountain_east_conference = "Mountain East Conference"
    northeast_10_conference = "Northeast-10 Conference"
    northern_sun_intercollegiate_conference = "Northern Sun Intercollegiate Conference"
    peach_belt_conference = "Peach Belt Conference"
    pennsylvania_state_athletic_conference = "Pennsylvania State Athletic Conference"
    rocky_mountain_athletic_conference = "Rocky Mountain Athletic Conference"
    south_atlantic_conference = "South Atlantic Conference"
    sunshine_state_conference = "Sunshine State Conference"
    appalachian_swimming_conference = "Appalachian Swimming Conference"
    new_south_intercollegiate_swim_conference = "New South Intercollegiate Swim Conference"
    pacific_coast_swim_conference = "Pacific Coast Swim Conference"

    # Division III
    allegheny_mountain_collegiate_conference = "Allegheny Mountain Collegiate Conference"
    american_rivers_conference = "American Rivers Conference"
    american_southwest_conference = "American Southwest Conference"
    atlantic_east_conference = "Atlantic East Conference"
    centennial_conference = "Centennial Conference"
    cuny_athletic_conference = "City University of New York Athletic Conference"
    coast_to_coast_athletic_conference = "Coast to Coast Athletic Conference"
    college_conference_of_illinois_and_wisconsin = "College Conference of Illinois and Wisconsin"
    collegiate_conference_of_the_south = "Collegiate Conference of the South"
    conference_of_new_england = "Conference of New England"
    empire_8 = "Empire 8"
    great_northeast_athletic_conference = "Great Northeast Athletic Conference"
    heartland_collegiate_athletic_conference = "Heartland Collegiate Athletic Conference"
    landmark_conference = "Landmark Conference"
    liberty_league = "Liberty League"
    little_east_conference = "Little East Conference"
    michigan_intercollegiate_athletic_association = "Michigan Intercollegiate Athletic Association"
    middle_atlantic_conferences = "Middle Atlantic Conferences"
    midwest_conference = "Midwest Conference"
    minnesota_intercollegiate_athletic_conference = "Minnesota Intercollegiate Athletic Conference"
    new_england_collegiate_conference = "New England Collegiate Conference"
    new_england_small_college_athletic_conference = "New England Small College Athletic Conference"
    new_england_womens_and_mens_athletic_conference = "New England Women's and Men's Athletic Conference"
    new_jersey_athletic_conference = "New Jersey Athletic Conference"
    north_atlantic_conference = "North Atlantic Conference"
    north_coast_athletic_conference = "North Coast Athletic Conference"
    northwest_conference = "Northwest Conference"
    ohio_athletic_conference = "Ohio Athletic Conference"
    old_dominion_athletic_conference = "Old Dominion Athletic Conference"
    presidents_athletic_conference = "Presidents' Athletic Conference"
    skyline_conference = "Skyline Conference"
    southern_athletic_association = "Southern Athletic Association"
    southern_california_intercollegiate_athletic_conference = "Southern California Intercollegiate Athletic Conference"
    southern_collegiate_athletic_conference = "Southern Collegiate Athletic Conference"
    suny_athletic_conference = "State University of New York Athletic Conference"
    united_east_conference = "United East Conference"
    university_athletic_association = "University Athletic Association"
    usa_south_athletic_conference = "USA South Athletic Conference"
    wisconsin_intercollegiate_athletic_conference = "Wisconsin Intercollegiate Athletic Conference"


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    short_name: Mapped[str] = mapped_column(String(20))
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    home_venue_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("venues.id"), nullable=True)
    # values_callable: these enums' member names are Python-identifier-safe
    # snake_case, distinct from their human-readable .value strings, so
    # without this SQLAlchemy would bind/compare using .name (its default)
    # instead of the .value the Postgres enum type and migration actually use.
    division: Mapped[TeamDivision | None] = mapped_column(
        Enum(TeamDivision, name="team_division", values_callable=lambda obj: [e.value for e in obj]),
        nullable=True,
    )
    conference: Mapped[TeamConference | None] = mapped_column(
        Enum(TeamConference, name="team_conference", values_callable=lambda obj: [e.value for e in obj]),
        nullable=True,
    )
