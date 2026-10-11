"""Bot levels, computed from the core predictor tree."""

from janken.kit import bot, levels, presets

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
        assert level(bot.Bandit((LAST,))) == 1
        sim = bot.Bandit((bot.Sim(LAST), ROCKY), rotations=(bot.BEAT,))
        assert level(sim) == 1  # no scorer: no bandit

    def test_a_bandit_over_heuristics_is_level_two(self) -> None:
        assert level(bandit(LAST)) == 2

    def test_a_single_scored_arm_is_no_bandit(self) -> None:
        one = bot.Bandit((LAST,), scorer=bot.DecayedNet(0.9), selector=bot.Greedy())
        assert level(one) == 1

    def test_a_replay_counts_at_its_own_level(self) -> None:
        l2 = bandit(LAST, ROCKY)
        assert l2.level() == 2
        l3 = bandit(LAST, bot.Replay(l2))
        assert l3.level() == 3
        l4 = bandit(LAST, bot.Replay(l3))
        assert l4.level() == 4
        lone = bot.Bandit(
            (bot.Replay(l3),), scorer=bot.DecayedNet(0.9), selector=bot.Greedy()
        )
        assert level(lone) == 3  # one replay arm: no extra layer

    def test_advanced_bots_core_is_level_three(self) -> None:
        assert presets.smartbot_sims(10, 0.95, 0.9, 12).level() == 3
        assert presets.metabot(0.95, 0.9, 12).level() == 2

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
        assert bot.Sim(LAST).level() == 1

    def test_a_bandit_counts_its_predictors_arms(self) -> None:
        core = bot.Bandit((LAST, bot.Rotated(ROCKY, (bot.COPY,))), bot.ALL_ROTATIONS)
        assert core.arms() == 4
