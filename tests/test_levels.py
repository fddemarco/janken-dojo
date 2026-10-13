"""Bot levels, computed from the core predictor tree: L1 heuristics, then one level
per aggregator (Bandit, Gate, NaiveBayes) above its highest arm."""

from janken import library
from janken.kit import bot, levels
from tests import data

ROCKY = bot.Constant(bot.ROCK)
LAST = bot.LastMove(bot.OPP)


def bandit(*predictors: bot.SignalLike) -> bot.Bandit:
    return bot.Bandit(
        predictors, bot.ALL_ROTATIONS, bot.Dirichlet(0.9), selector=bot.Thompson()
    )


def level(core: bot.Predictor) -> int:
    return levels.level(bot.Blueprint(core=core))


class TestLevel:
    def test_heuristics_are_level_one(self) -> None:
        assert level(bot.Heuristic(LAST, bot.BEAT)) == 1
        assert level(bot.Heuristic(bot.Sim(LAST), bot.COPY)) == 1
        assert level(bot.Heuristic()) == 1  # silent: random play
        assert levels.level(bot.Blueprint()) == 1

    def test_every_aggregator_adds_a_level(self) -> None:
        assert level(bandit(LAST)) == 2
        one = bot.Bandit((LAST,), scorer=bot.DecayedNet(0.9), selector=bot.Greedy())
        assert level(one) == 2  # one scored arm: still an aggregator
        priority = bot.Bandit((bot.Sim(LAST), ROCKY), rotations=(bot.BEAT,))
        assert level(priority) == 2  # no scorer: still an aggregator

    def test_a_replay_counts_at_its_own_level(self) -> None:
        l2 = bandit(LAST, ROCKY)
        assert l2.level() == 2
        l3 = bandit(LAST, bot.Replay(l2))
        assert l3.level() == 3
        l4 = bandit(LAST, bot.Replay(l3))
        assert l4.level() == 4
        mine = bandit(LAST, bot.Replay(l3, side=bot.MY))
        assert mine.level() == 4  # from our side too

    def test_a_heuristic_over_a_replay_is_the_replayed_bots_level(self) -> None:
        l3 = bandit(LAST, bot.Replay(bandit(LAST, ROCKY)))
        assert level(bot.Heuristic(bot.Replay(l3), bot.BEAT)) == 3

    def test_declared_bots_get_their_cores_level(self) -> None:
        for stem, expected in [
            ("frequency_v1", 1),
            ("smartbot_v1", 2),
            ("smartbot_sims_v1", 3),
            ("anti_smartbot_sims_v1", 3),
            ("gate_edge_v1", 4),
        ]:
            path = data.bot(stem)
            assert levels.level(library.read_blueprint(path)) == expected, path

    def test_a_naive_bayes_combiner_is_one_above_its_inputs(self) -> None:
        combiner = bot.NaiveBayes((LAST,))
        assert combiner.level() == 2
        assert bandit(LAST, combiner).level() == 3

    def test_a_gate_is_one_above_its_main_bandit_and_experts(self) -> None:
        l3 = bandit(LAST, bot.Replay(bandit(LAST, ROCKY)))
        anti = bot.Rotated(bot.Replay(l3), (bot.BEAT,))
        assert level(bot.Gate(l3, (anti,))) == 4
        assert level(bot.Gate(bandit(LAST), (ROCKY,))) == 3

    def test_any_oracle_makes_an_oracle(self) -> None:
        assert level(bandit(LAST, bot.Oracle())) == levels.ORACLE
        gated = bot.Gate(bandit(LAST), (bot.Rotated(bot.Oracle(), (bot.BEAT,)),))
        assert level(gated) == levels.ORACLE
        assert level(bot.Heuristic(bot.Oracle(), bot.BEAT)) == levels.ORACLE
        assert levels.name(levels.ORACLE) == "Oracle"
        assert levels.name(3) == "L3"


class TestTree:
    def test_a_walk_visits_every_predictor_depth_first(self) -> None:
        inner = bot.Bandit((ROCKY,))
        core = bot.Bandit((bot.Sim(LAST), bot.Replay(inner)))
        assert list(core.walk()) == [
            core,
            bot.Sim(LAST),
            LAST,
            bot.Replay(inner),
            inner,
            ROCKY,
        ]

    def test_decorators_have_one_child_and_leaves_none(self) -> None:
        assert LAST.children() == ()
        assert bot.Rotated(LAST, (bot.COPY,)).children() == (LAST,)
        assert bot.Heuristic(LAST, bot.BEAT).children() == (LAST,)
        assert bot.Sim(LAST).level() == 1

    def test_a_bandit_counts_its_predictors_arms(self) -> None:
        core = bot.Bandit((LAST, bot.Rotated(ROCKY, (bot.COPY,))), bot.ALL_ROTATIONS)
        assert core.arms() == 4
