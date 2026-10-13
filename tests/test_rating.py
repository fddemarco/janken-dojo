import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from janken import rating as elo


class TestTitle:
    def test_titles_are_ordered_weakest_first(self) -> None:
        assert elo.TITLES == ("novice", "cm", "master", "im", "gm")
        floors = [floor for _, floor in elo.RATING_TITLES]
        assert floors == sorted(floors, reverse=True)
        # Every rating title is a real title, and none is handed out at the start.
        for name, floor in elo.RATING_TITLES:
            assert name in elo.TITLES
            assert floor > elo.START_RATING
        # Every rung but the start is a floor, so nothing can out-rate the
        # ladder: the bot leading the standings always holds a title.
        assert elo.floor_for("novice") is None
        assert len(elo.RATING_TITLES) == len(elo.TITLES) - 1

    def test_the_first_title_is_the_cheapest_rung(self) -> None:
        """A bot that only just out-rates the field is a CM and nothing more.

        The lowest floor exists so a leader never reads `Novice`, not to hand
        out the higher titles early, so it sits strictly between the starting
        rating and the next rung up.
        """
        floor = elo.floor_for("cm")
        assert elo.RATING_TITLES[-1] == ("cm", floor)  # the lowest floor
        assert floor > elo.START_RATING
        assert floor < elo.floor_for("master")
        assert elo.title_for_rating(floor) == "cm"
        assert elo.title_for_rating(floor - 0.5) == "novice"

    def test_every_title_has_a_display_name(self) -> None:
        for title in elo.TITLES:
            assert elo.name(title) != title  # a real name, not the slug
            assert elo.abbr(title)
        # Abbreviations stay unique, so the title column is unambiguous.
        abbrs = [elo.abbr(t) for t in elo.TITLES]
        assert len(set(abbrs)) == len(abbrs)

    def test_title_tracks_the_peak_rating(self) -> None:
        assert elo.title_for_rating(elo.START_RATING) == "novice"
        for name, floor in elo.RATING_TITLES:
            assert elo.title_for_rating(floor) == name
            assert elo.title_for_rating(floor - 1) != name
        assert elo.title_for_rating(9999) == elo.TITLES[-1]

    def test_ladder_reads_as_a_ladder(self) -> None:
        line = elo.ladder()
        for title in elo.TITLES:
            assert elo.name(title) in line
        assert "2100+" in line  # the floors are spelled out
        assert "Candidate Master 1600+" in line
        # `novice` is the start, not a floor, so it carries no number.
        assert "Novice 1" not in line
