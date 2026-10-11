import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from janken import rating as elo


class TitleTest(unittest.TestCase):
    def test_titles_are_ordered_weakest_first(self):
        self.assertEqual(elo.TITLES, ("novice", "cm", "master", "im", "gm"))
        floors = [floor for _, floor in elo.RATING_TITLES]
        self.assertEqual(floors, sorted(floors, reverse=True))
        # Every rating title is a real title, and none is handed out at the start.
        for name, floor in elo.RATING_TITLES:
            self.assertIn(name, elo.TITLES)
            self.assertGreater(floor, elo.START_RATING)
        # Every rung but the start is a floor, so nothing can out-rate the
        # ladder: the bot leading the standings always holds a title.
        self.assertIsNone(elo.floor_for("novice"))
        self.assertEqual(len(elo.RATING_TITLES), len(elo.TITLES) - 1)

    def test_the_first_title_is_the_cheapest_rung(self):
        """A bot that only just out-rates the field is a CM and nothing more.

        The lowest floor exists so a leader never reads `Novice`, not to hand
        out the higher titles early, so it sits strictly between the starting
        rating and the next rung up.
        """
        floor = elo.floor_for("cm")
        self.assertEqual(elo.RATING_TITLES[-1], ("cm", floor))  # the lowest floor
        self.assertGreater(floor, elo.START_RATING)
        self.assertLess(floor, elo.floor_for("master"))
        self.assertEqual(elo.title_for_rating(floor), "cm")
        self.assertEqual(elo.title_for_rating(floor - 0.5), "novice")

    def test_every_title_has_a_display_name(self):
        for title in elo.TITLES:
            self.assertNotEqual(elo.name(title), title)  # a real name, not the slug
            self.assertTrue(elo.abbr(title))
        # Abbreviations stay unique, so the title column is unambiguous.
        abbrs = [elo.abbr(t) for t in elo.TITLES]
        self.assertEqual(len(set(abbrs)), len(abbrs))

    def test_title_tracks_the_peak_rating(self):
        self.assertEqual(elo.title_for_rating(elo.START_RATING), "novice")
        for name, floor in elo.RATING_TITLES:
            self.assertEqual(elo.title_for_rating(floor), name)
            self.assertNotEqual(elo.title_for_rating(floor - 1), name)
        self.assertEqual(elo.title_for_rating(9999), elo.TITLES[-1])

    def test_ladder_reads_as_a_ladder(self):
        line = elo.ladder()
        for title in elo.TITLES:
            self.assertIn(elo.name(title), line)
        self.assertIn("2100+", line)  # the floors are spelled out
        self.assertIn("Candidate Master 1600+", line)
        # `novice` is the start, not a floor, so it carries no number.
        self.assertNotIn("Novice 1", line)


if __name__ == "__main__":
    unittest.main()
