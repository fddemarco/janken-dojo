"""janken/kit/declare.py: blueprints declared as YAML data."""

import unittest

import yaml

from janken.kit import bot, presets
from janken.kit.blueprint import Blueprint, BlueprintError
from janken.kit.declare import blueprint_from_data


def declared(text: str) -> Blueprint:
    return blueprint_from_data(yaml.safe_load(text))


class GrammarTest(unittest.TestCase):
    def test_keywords_positional_and_bare_calls(self) -> None:
        expected = bot.Blueprint(
            guards=(bot.Noise(bot.Knob("NOISE")), bot.Opening(1, bot.ROCK)),
            signals=(bot.React(), bot.LastMove(bot.MY)),
            rotations=(bot.BEAT, bot.COPY),
        )
        self.assertEqual(
            declared("""
                guards: [{Noise: {p: $NOISE}}, {Opening: [1, ROCK]}]
                signals: [React, {LastMove: {of: MY}}]
                rotations: [BEAT, COPY]
            """),
            expected,
        )

    def test_an_empty_section_is_the_default_blueprint(self) -> None:
        self.assertEqual(blueprint_from_data(None), Blueprint())
        self.assertEqual(blueprint_from_data({}), Blueprint())

    def test_wrappers_nest(self) -> None:
        self.assertEqual(
            declared("""
                signals:
                  - Sim: {signal: {NGram: {order: 2, ctx: JOINT}}}
                  - Rotated: {signal: {Geometry: {alpha: 0.1}}, rotations: [BEAT]}
                  - Replay: {ensemble: {staller: {}}}
                rotations: ALL_ROTATIONS
            """).signals,
            (
                bot.Sim(bot.NGram(2, ctx=bot.JOINT)),
                bot.Rotated(bot.Geometry(0.1), (bot.BEAT,)),
                bot.Replay(presets.staller()),
            ),
        )

    def test_around_a_preset_core(self) -> None:
        self.assertEqual(
            declared("""
                around: {iocaine: [$DECAY, 12]}
                selector: {Greedy: {ties: TIES_FIRST}}
                overlays: [{Team: {role: SUPPORT}}]
            """),
            bot.Blueprint.around(
                presets.iocaine(bot.Knob("DECAY"), 12),
                bot.Greedy(bot.TIES_FIRST),
                overlays=(bot.Team(bot.SUPPORT),),
            ),
        )

    def test_a_vigilant_team_of_a_named_fleet(self) -> None:
        self.assertEqual(
            declared("""
                signals: [{Constant: [ROCK]}]
                overlays: [{Team: {role: CHAMPION, fleet: ILIAD_V2, vigilant: true}}]
            """).overlays,
            (bot.Team(bot.CHAMPION, bot.ILIAD_V2, vigilant=True),),
        )

    def test_a_preset_returning_signals_is_spliced(self) -> None:
        signals = declared("""
            signals: [{metabot_signals: [0.9, 12]}, React]
        """).signals
        self.assertEqual(signals, (*presets.metabot_signals(0.9, 12), bot.React()))

    def test_choose_selector(self) -> None:
        self.assertEqual(
            declared("""
                selector:
                  ChooseSelector:
                    index: $SELECT
                    options: [Thompson, {Greedy: {ties: TIES_FIRST}}]
            """).selector,
            bot.ChooseSelector(
                bot.Knob("SELECT"), (bot.Thompson(), bot.Greedy(bot.TIES_FIRST))
            ),
        )


class ErrorTest(unittest.TestCase):
    def assertRefused(self, text: str, where: str) -> None:
        with self.assertRaisesRegex(BlueprintError, where):
            declared(text)

    def test_unknown_names_are_refused_with_their_path(self) -> None:
        self.assertRefused("signals: [React, NGrm]", r"blueprint\.signals\[1\]")
        self.assertRefused("signals: [{LastMove: {of: THEM}}]", "THEM")
        self.assertRefused("guards: [{Noise: {q: 0.1}}]", r"guards\[0\]\.Noise")
        self.assertRefused("signal: [React]", "unknown key")

    def test_malformed_calls_are_refused(self) -> None:
        self.assertRefused("signals: [{React: {}, LastMove: {}}]", "one `Name")
        self.assertRefused("guards: [{Opening: [1, 2, 3, 4]}]", "Opening")
        self.assertRefused("signals: [{LastMove: {of: $}}]", "bad knob")
        self.assertRefused("around: staller", "needs a `selector`")
        self.assertRefused("around: staller\nselector: First\nsignals: []", "unknown")


if __name__ == "__main__":
    unittest.main()
