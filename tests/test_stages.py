"""The compiled stages, run as plain Python on hand-made histories of a few rounds."""

import random
import types
from collections.abc import Mapping, Sequence

import numpy as np
import pytest

from janken.engine.registry import P_MAX
from janken.kit import blueprint, bot, ensemble, matching, overlays, pipeline, selectors
from janken.kit import codes as c
from janken.kit.moves import CRASH, INVALID, PAPER, ROCK, SCISSORS

R, P, S, X = ROCK, PAPER, SCISSORS, INVALID
NO_DEFAULTS: Mapping[str, float | int] = types.MappingProxyType({})


# Rounds a Runner's state is sized for: longer than any history in these tests.
RUNNER_ROUNDS = 64


class Runner:
    """A compiled blueprint with fresh state, played over fixed histories."""

    def __init__(
        self,
        blueprint: bot.Blueprint,
        defaults: Mapping[str, float | int] = NO_DEFAULTS,
    ) -> None:
        compiled = blueprint.compile(defaults)
        self.spec, self.knobs = compiled.spec, compiled.knobs
        self.f, self.i = compiled.new_state(RUNNER_ROUNDS)
        self.prm = np.zeros(P_MAX)
        for k, value in enumerate(defaults.values()):
            self.prm[k] = float(value)

    def moves(self, my: Sequence[int], opp: Sequence[int]) -> list[int]:
        """The bot's move at every round 0..len(my), given these histories."""
        a = np.array(my, np.int64)
        b = np.array(opp, np.int64)
        return [
            int(pipeline.play(self.f, self.i, self.prm, a, b, n, self.spec, self.knobs))
            for n in range(len(a) + 1)
        ]

    def last(self, my: Sequence[int], opp: Sequence[int]) -> int:
        return self.moves(my, opp)[-1]


def signal_bot(*signals: bot.SignalLike) -> Runner:
    """A bot that plays its first signal's symbol as is (rotation COPY)."""
    return Runner(
        bot.Blueprint(core=bot.Bandit(predictors=signals, rotations=(bot.COPY,)))
    )


class TestGuard:
    def setup_method(self) -> None:
        random.seed(1)

    def test_opening_plays_its_move_then_lets_the_round_through(self) -> None:
        runner = Runner(
            bot.Blueprint(
                guards=(bot.Opening(2, PAPER),),
                core=bot.Bandit(predictors=(bot.Constant(R),)),
            )
        )
        assert runner.moves([R, R, R], [R, R, R]) == [P, P, P, P]
        runner = Runner(
            bot.Blueprint(
                guards=(bot.Opening(2, PAPER),),
                core=bot.Bandit(predictors=(bot.Constant(R),), rotations=(bot.COPY,)),
            )
        )
        assert runner.moves([R, R, R], [R, R, R]) == [P, P, R, R]

    def test_noise_one_is_random_and_noise_zero_passes(self) -> None:
        loud = Runner(
            bot.Blueprint(
                guards=(bot.Noise(1.0),),
                core=bot.Bandit(predictors=(bot.Constant(R),), rotations=(bot.COPY,)),
            )
        )
        assert len(set(loud.moves([R] * 30, [R] * 30))) > 1
        quiet = Runner(
            bot.Blueprint(
                guards=(bot.Noise(0.0),),
                core=bot.Bandit(predictors=(bot.Constant(R),), rotations=(bot.COPY,)),
            )
        )
        assert set(quiet.moves([R] * 30, [R] * 30)) == {R}

    def test_on_invalid_crashes_on_the_last_round_only(self) -> None:
        def crasher(scope: int, side: int) -> Runner:
            return Runner(
                bot.Blueprint(
                    guards=(bot.OnInvalid(bot.CRASH_ACTION, scope, side),),
                    core=bot.Bandit(
                        predictors=(bot.Constant(R),), rotations=(bot.COPY,)
                    ),
                )
            )

        last = crasher(bot.LAST, bot.OPP).moves([R, R, R], [R, X, R])
        assert last == [R, R, CRASH, R]
        anywhere = crasher(bot.ANY, bot.OPP).moves([R, R, R], [R, X, R])
        assert anywhere == [R, R, CRASH, CRASH]
        mine_ignored = crasher(bot.ANY, bot.OPP).moves([X, R], [R, R])
        assert mine_ignored == [R, R, R]
        mine_seen = crasher(bot.ANY, bot.BOTH).moves([X, R], [R, R])
        assert mine_seen == [R, CRASH, CRASH]

    def test_without_a_guard_invalid_rounds_are_skipped(self) -> None:
        runner = signal_bot(bot.LastMove(bot.OPP))
        assert runner.last([R, R, R], [S, P, X]) == P


class TestSignal:
    def setup_method(self) -> None:
        random.seed(1)

    def test_last_move(self) -> None:
        assert signal_bot(bot.LastMove(bot.OPP)).last([R, P], [S, P]) == P
        assert signal_bot(bot.LastMove(bot.MY)).last([R, P], [S, S]) == P

    def test_first_selector_falls_back_without_a_symbol(self) -> None:
        runner = Runner(
            bot.Blueprint(
                core=bot.Bandit(
                    predictors=(bot.LastMove(),),
                    rotations=(bot.COPY,),
                    selector=bot.First(S),
                )
            )
        )
        assert runner.moves([], []) == [S]

    def test_frequency(self) -> None:
        assert signal_bot(bot.Frequency(bot.OPP)).last([R] * 4, [S, P, S, R]) == S
        assert signal_bot(bot.Frequency(bot.MY)).last([P, P, R], [S] * 3) == P

    def test_ngram_learns_a_cycle(self) -> None:
        cycle = [R, P, S] * 4
        runner = signal_bot(bot.NGram(1, ctx=bot.OPP))
        assert runner.last([R] * 12, cycle) == R  # after S comes R
        sampled = signal_bot(bot.NGram(1, ctx=bot.OPP, sample=True))
        assert sampled.last([R] * 12, cycle) == R  # the row is all R

    def test_backoff_uses_the_longest_known_context(self) -> None:
        runner = signal_bot(bot.Backoff(3, ctx=bot.JOINT))
        my = [R, P, S, R, P, S, R, P]
        opp = [S, S, R, S, S, R, S, S]
        assert runner.last(my, opp) == R

    def test_longest_match(self) -> None:
        runner = signal_bot(bot.LongestMatch(5, ctx=bot.OPP))
        assert runner.last([R] * 7, [R, P, S, P, R, P, S]) == P
        no_repeat = signal_bot(bot.LongestMatch(5)).last([R], [R])
        assert no_repeat in (R, P, S)  # nothing to match: the random fallback

    def test_relative_rotation(self) -> None:
        runner = signal_bot(bot.Relative(bot.OPP))
        assert runner.last([R] * 5, [R, P, S, R, P]) == S  # always +1

    def test_react(self) -> None:
        runner = signal_bot(bot.React())
        assert runner.last([P], [R]) == S  # we won: it beats our paper
        assert runner.last([R], [P]) == P  # we lost: it repeats

    def test_generators(self) -> None:
        assert signal_bot(bot.Constant(S)).moves([R], [R]) == [S, S]
        assert signal_bot(bot.Cycle(2)).moves([R, R], [R, R]) == [R, S, P]
        assert signal_bot(bot.Biased(1.0, 0.0)).moves([R], [R]) == [R, R]
        win_stay = signal_bot(bot.WinStay(1))
        assert win_stay.last([R], [S]) == R  # won: stay
        assert win_stay.last([R], [P]) == P  # lost: shift by 1

    def test_geometry_plays_moves(self) -> None:
        runner = signal_bot(bot.Geometry(0.2, 10))
        moves = runner.moves([R, P, S] * 6, [P, S, R] * 6)
        assert all(0 <= m <= 2 for m in moves)

    def test_a_sim_plays_what_beats_its_prediction_of_us(self) -> None:
        runner = signal_bot(bot.Sim(bot.LastMove(bot.OPP)))
        assert runner.last([R, S], [P, P]) == R  # it expects S, plays R


class TestNaiveBayes:
    def setup_method(self) -> None:
        random.seed(1)

    def test_without_inputs_it_follows_the_prior(self) -> None:
        runner = Runner(
            bot.Blueprint(core=bot.Bandit(predictors=(bot.NaiveBayes((), 1.0),)))
        )
        assert runner.last([S, S, S], [R, R, R]) == P

    def test_it_learns_what_a_signal_means_and_ignores_a_useless_one(self) -> None:
        # The opponent cycles, so LastMove(OPP)'s symbol is always one behind its
        # next move: NaiveBayes learns that and plays the beat of the real next move,
        # where LastMove's own BEAT arm would lose.
        runner = Runner(
            bot.Blueprint(
                core=bot.Bandit(
                    predictors=(
                        bot.NaiveBayes((bot.LastMove(bot.OPP), bot.Constant(R)), 1.0),
                        bot.LastMove(bot.OPP),
                        bot.Constant(R),
                    )
                )
            )
        )
        moves = runner.moves([R] * 9, [R, P, S] * 3)
        assert moves[-1] == P  # the next move is R
        assert moves[-2] == R  # the next move is S

    def test_no_evidence_no_symbol(self) -> None:
        runner = Runner(
            bot.Blueprint(
                core=bot.Bandit(
                    predictors=(bot.NaiveBayes((bot.Constant(R),)), bot.Constant(R)),
                    rotations=(bot.COPY,),
                )
            )
        )
        assert runner.moves([], []) == [R]  # the first arm with a move

    def test_it_runs_inside_a_replay(self) -> None:
        core = bot.Bandit(
            (bot.NaiveBayes((bot.LastMove(bot.OPP),)), bot.LastMove(bot.OPP)),
            scorer=bot.DecayedNet(1.0),
        )
        runner = Runner(
            bot.Blueprint(
                core=bot.Bandit(
                    predictors=(bot.Replay(core),),
                    rotations=(bot.BEAT,),
                    scorer=bot.DecayedNet(1.0),
                    selector=bot.Greedy(),
                )
            )
        )
        moves = runner.moves([R, P, S] * 4, [P, P, R] * 4)
        assert all(0 <= m <= 2 for m in moves)


def rock_or_paper() -> bot.Bandit:
    """A bandit of two arms, rock and paper, on net scores."""
    return bot.Bandit(
        (bot.Constant(R), bot.Constant(P)),
        rotations=(bot.COPY,),
        scorer=bot.DecayedNet(1.0),
        selector=bot.Greedy(),
    )


def replaying(replay: bot.Replay) -> Runner:
    """A bot that plays a replay's symbol as is."""
    return Runner(bot.Blueprint(core=bot.Heuristic(replay, bot.COPY)))


class TestReplaySide:
    """A whole bandit replayed: from the opponent's side its likely move, from ours
    its own (a bot of level 2+ as an arm). We play paper, the opponent scissors:
    rock wins for us, paper for them."""

    MY_MOVES, OPP_MOVES = [P] * 4, [S] * 4

    def test_from_our_side_it_plays_its_own_best_arm(self) -> None:
        runner = replaying(bot.Replay(rock_or_paper(), side=bot.MY))
        assert runner.last(self.MY_MOVES, self.OPP_MOVES) == R

    def test_from_the_opponents_side_it_names_their_move(self) -> None:
        runner = replaying(bot.Replay(rock_or_paper(), side=bot.OPP))
        assert runner.last(self.MY_MOVES, self.OPP_MOVES) == P

    def test_a_nested_replays_side_is_relative_to_the_one_holding_it(self) -> None:
        def nested(outer: int, inner: int) -> int:
            middle = bot.Bandit(
                (bot.Replay(rock_or_paper(), side=inner),),
                rotations=(bot.COPY,),
                scorer=bot.DecayedNet(1.0),
            )
            runner = replaying(bot.Replay(middle, side=outer))
            return runner.last(self.MY_MOVES, self.OPP_MOVES)

        assert nested(bot.MY, bot.MY) == R
        assert nested(bot.MY, bot.OPP) == P
        assert nested(bot.OPP, bot.MY) == P
        assert nested(bot.OPP, bot.OPP) == R  # swapped twice: our side again


def longest_match_by_scan(stream: Sequence[int], max_len: int, n: int) -> int:
    """The matcher's definition, by brute force (the algorithm the index replaced):
    the end just after the most recent earlier repeat of the longest suffix."""
    for length in range(min(max_len, n - 1), 0, -1):
        for j in range(n - length - 1, -1, -1):
            if list(stream[j : j + length]) == list(stream[n - length : n]):
                return j + length
    return -1


class TestMatchIndex:
    """janken/kit/matching.py against the brute-force definition."""

    STREAMS: Mapping[int, int] = types.MappingProxyType(
        {bot.OPP: c.STREAM_OPP, bot.MY: c.STREAM_MY, bot.JOINT: c.STREAM_JOINT}
    )

    def histories(self) -> list[tuple[list[int], list[int]]]:
        rng = random.Random(7)
        rounds = 60
        noisy = [rng.randrange(3) for _ in range(rounds)]
        return [
            (noisy, [rng.randrange(3) for _ in range(rounds)]),
            ([R] * rounds, [R] * rounds),  # one repeated symbol: the longest chains
            ([t % 3 for t in range(rounds)], [(t // 2) % 3 for t in range(rounds)]),
            (noisy, [P if rng.random() < 0.8 else S for _ in range(rounds)]),
        ]

    def test_every_round_matches_the_scan(self, subtests: pytest.Subtests) -> None:
        for ctx, stream in self.STREAMS.items():
            for my, opp in self.histories():
                symbols = [
                    {c.STREAM_OPP: o, c.STREAM_MY: m}.get(stream, m * 3 + o)
                    for m, o in zip(my, opp)
                ]
                for max_len in (1, 3, 12, 20):
                    with subtests.test(ctx=ctx, max_len=max_len, first=symbols[:6]):
                        assert self.indexed(ctx, max_len, my, opp) == [
                            longest_match_by_scan(symbols, max_len, n)
                            for n in range(len(my) + 1)
                        ]

    def indexed(
        self, ctx: int, max_len: int, my: Sequence[int], opp: Sequence[int]
    ) -> list[int]:
        """The index's answer at every n, folding one round at a time."""
        compiled = bot.Blueprint(
            core=bot.Bandit(predictors=(bot.LongestMatch(max_len, ctx=ctx),))
        ).compile({})
        spec = compiled.spec
        _, i = compiled.new_state(len(my))
        a = np.array(my, np.int64)
        b = np.array(opp, np.int64)
        x = spec[c.H_IDX_AT]
        out = [matching.query(spec, x, i, max_len, 0)]
        for k in range(len(my)):
            matching.fold(spec, x, i, k, a, b)
            out.append(matching.query(spec, x, i, max_len, k + 1))
        return out


class TestSecondMatch:
    """SecondMatch against its definition, by brute force."""

    def test_every_round_matches_the_scan(self, subtests: pytest.Subtests) -> None:
        histories = TestMatchIndex().histories()
        for ctx, stream in TestMatchIndex.STREAMS.items():
            for my, opp in histories:
                symbols = [
                    {c.STREAM_OPP: o, c.STREAM_MY: m}.get(stream, m * 3 + o)
                    for m, o in zip(my, opp)
                ]
                for max_len in (3, 12):
                    runner = signal_bot(bot.SecondMatch(max_len, ctx=ctx))
                    moves = runner.moves(my, opp)
                    with subtests.test(ctx=ctx, max_len=max_len, first=symbols[:6]):
                        for n in range(len(my) + 1):
                            j = longest_match_by_scan(symbols, max_len, n)
                            j2 = longest_match_by_scan(symbols, max_len, j)
                            if j >= 0 and j2 >= 0:
                                assert moves[n] == opp[j2], n

    def test_no_second_repeat_no_symbol(self) -> None:
        runner = Runner(
            bot.Blueprint(
                core=bot.Bandit(
                    predictors=(bot.SecondMatch(12), bot.Constant(S)),
                    rotations=(bot.COPY,),
                )
            )
        )
        # R P R: the suffix R repeats at end 1, but s[0:1] has no earlier repeat.
        assert runner.last([R, R, R], [R, P, R]) == S


class TestScorer:
    def test_dirichlet_counts_win_tie_loss(self) -> None:
        f = np.zeros(3)
        kn = np.array([0.5])
        ensemble.score_arm(c.SC_DIRICHLET, f, 0, P, R, kn, 0)  # win
        ensemble.score_arm(c.SC_DIRICHLET, f, 0, R, R, kn, 0)  # tie
        assert list(f) == [0.5, 1.0, 0.0]
        assert ensemble.value(c.SC_DIRICHLET, f, 0) == pytest.approx(
            0.5 / 4.5, rel=0, abs=0.5e-7
        )

    def test_decayed_net(self) -> None:
        f = np.zeros(3)
        kn = np.array([0.5])
        ensemble.score_arm(c.SC_DECAYED, f, 0, P, R, kn, 0)
        ensemble.score_arm(c.SC_DECAYED, f, 0, R, P, kn, 0)
        assert f[0] == 0.5 * 1.0 - 1.0

    def test_drop_switch_resets_on_a_loss(self) -> None:
        f = np.zeros(3)
        kn = np.array([1.0])
        for _ in range(3):
            ensemble.score_arm(c.SC_DROP_SWITCH, f, 0, P, R, kn, 0)
        assert f[0] == 3.0
        ensemble.score_arm(c.SC_DROP_SWITCH, f, 0, R, P, kn, 0)
        assert f[0] == 0.0
        never = np.array([0.0])
        ensemble.score_arm(c.SC_DROP_SWITCH, f, 0, R, P, never, 0)
        assert f[0] == -1.0


class TestSelector:
    """Two arms, ROCK then PAPER, with scores set by hand."""

    def arms(
        self, selector: bot.Selector, scores: Sequence[float], random_arm: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        compiled = bot.Blueprint(
            core=bot.Bandit(
                predictors=(bot.Constant(R), bot.Constant(P)),
                rotations=(bot.COPY,),
                scorer=bot.DecayedNet(0.9),
                random_arm=random_arm,
                selector=selector,
            )
        ).compile({})
        spec = compiled.spec
        f, i = compiled.new_state(1)
        kn = pipeline.resolve_knobs(spec, f, np.zeros(P_MAX), compiled.knobs)
        core = spec[c.H_CORE]
        ensemble.set_arms(spec, core, i, np.array([R, P]), 0)
        for a, v in enumerate(scores):
            f[spec[core + c.E_SCORE_F] + 3 * a] = v
        return spec, f, i, kn

    def choose(
        self, selector: bot.Selector, scores: Sequence[float], random_arm: int
    ) -> int:
        spec, f, i, kn = self.arms(selector, scores, random_arm)
        no_history = np.zeros(1, np.int64)
        return int(
            selectors.choose(
                spec, spec[c.H_SEL_AT], spec[c.H_CORE], f, i, kn, 0, 0, no_history
            )
        )

    def setup_method(self) -> None:
        random.seed(3)

    def test_greedy_plays_the_best_arm_and_breaks_ties_in_order(self) -> None:
        assert self.choose(bot.Greedy(), [0.1, 0.7], bot.RA_NONE) == P
        assert self.choose(bot.Greedy(bot.TIES_FIRST), [0.5, 0.5], bot.RA_NONE) == R

    def test_a_pinned_random_arm_wins_when_every_model_loses(self) -> None:
        moves = {
            self.choose(bot.Greedy(), [-1.0, -2.0], bot.RA_PINNED) for _ in range(40)
        }
        assert moves == {R, P, S}

    def test_sampled_vote_only_plays_proposed_moves(self) -> None:
        moves = {
            self.choose(bot.SampledVote(0.5), [0.0, 0.0], bot.RA_NONE)
            for _ in range(40)
        }
        assert moves == {R, P}
        sharp = {
            self.choose(bot.SampledVote(0.01), [0.0, 1.0], bot.RA_NONE)
            for _ in range(40)
        }
        assert sharp == {P}

    def test_thompson_plays_a_proposed_move(self) -> None:
        compiled = bot.Blueprint(
            core=bot.Bandit(
                predictors=(bot.Constant(S),),
                rotations=(bot.COPY,),
                scorer=bot.Dirichlet(0.9),
                selector=bot.Thompson(),
            )
        )
        runner = Runner(compiled)
        assert set(runner.moves([R] * 5, [R] * 5)) == {S}


GATE_SCORER = bot.Dirichlet(0.9)


def main_bandit(*moves: int, scorer: bot.Scorer = GATE_SCORER) -> bot.Bandit:
    """A main bandit of Constant arms, played as they are, Thompson sampled."""
    return bot.Bandit(
        tuple(bot.Constant(m) for m in moves),
        (bot.COPY,),
        scorer,
        selector=bot.Thompson(),
    )


def gated(*moves: int) -> tuple[bot.SignalLike, ...]:
    """Gated Constant experts (one arm each under a COPY main bandit)."""
    return tuple(bot.Constant(m) for m in moves)


class TestGate:
    """Two experts: a main bandit of one Constant(ROCK) arm, and a gated expert."""

    def gate_bot(
        self, expert: int, edge: float, warmup: int, rule: int = bot.EDGE
    ) -> Runner:
        gate = bot.Gate(main_bandit(R), gated(expert), rule, edge, warmup=warmup)
        return Runner(bot.Blueprint(core=gate))

    def test_anti_first_plays_the_gated_arm_until_the_main_expert_leads(
        self,
    ) -> None:
        # The opponent plays SCISSORS: the main ROCK wins, the gated PAPER loses.
        moves = self.gate_bot(P, 0.3, 2, bot.ANTI_FIRST).moves([P] * 6, [S] * 6)
        assert moves[:2] == [P, P]  # warming up: the gated arm
        assert moves[2:] == [R] * 5  # ROCK leads by more than 0.3

    def test_anti_first_keeps_a_gated_arm_that_holds_its_own(self) -> None:
        moves = self.gate_bot(P, 0.3, 0, bot.ANTI_FIRST).moves([P] * 6, [R] * 6)
        assert set(moves) == {P}  # PAPER beats ROCK, ROCK only ties

    def hold_vs_anti_first(self, rounds_of_rock: int) -> tuple[list[int], list[int]]:
        """Main ROCK vs gated PAPER: 3 rounds of SCISSORS (ROCK leads), then ROCK
        (PAPER wins, ROCK ties); the lead (6 - k) / (6 + k) after k rounds of ROCK."""
        opp = [S] * 3 + [R] * rounds_of_rock
        my = [P] * len(opp)
        hold = self.gate_bot(P, 0.3, 0, bot.ANTI_FIRST_HOLD).moves(my, opp)
        first = self.gate_bot(P, 0.3, 0, bot.ANTI_FIRST).moves(my, opp)
        return hold, first

    def test_hold_keeps_the_main_expert_while_its_lead_dips(self) -> None:
        hold, first = self.hold_vs_anti_first(8)
        assert hold[1:] == [R] * 11  # the lead stays above -0.3
        assert first[1:7] == [R] * 6
        assert first[7:] == [P] * 5  # back once the lead is <= 0.3

    def test_hold_returns_to_the_gated_arm_once_it_leads_by_the_edge(self) -> None:
        hold, _ = self.hold_vs_anti_first(14)
        assert hold[1:15] == [R] * 14
        assert hold[15:] == [P] * 3  # PAPER leads by more than 0.3

    def test_main_first_moves_to_the_gated_arm_once_it_leads(self) -> None:
        # The main ROCK ties ROCK, the gated PAPER beats it: after 1 round the
        # lead (1 - 0) / 4 = 0.25 > 0.2, and PAPER is kept while it leads.
        moves = self.gate_bot(P, 0.2, 0, bot.MAIN_FIRST).moves([P] * 6, [R] * 6)
        assert moves[0] == R
        assert moves[1:] == [P] * 6

    def test_main_first_stays_on_the_main_expert_while_it_leads(self) -> None:
        moves = self.gate_bot(P, 0.2, 0, bot.MAIN_FIRST).moves([P] * 6, [S] * 6)
        assert moves == [R] * 7  # ROCK beats SCISSORS, PAPER loses

    def leader(self, opp: list[int]) -> list[int]:
        """LEADER over a main ROCK and two gated experts, PAPER then SCISSORS."""
        gate = bot.Gate(main_bandit(R), gated(P, S), bot.LEADER, 0.3, warmup=0)
        runner = Runner(bot.Blueprint(core=gate))
        return runner.moves([R] * len(opp), opp)

    def test_the_leader_takes_over_once_it_leads_by_the_edge(self) -> None:
        # vs ROCK: PAPER's record is 1/4 after one round (not > 0.3), 2/5 after two.
        moves = self.leader([R] * 3 + [P] * 8)
        assert moves[:2] == [R, R]
        assert moves[2:] == [P] * 10  # held: SCISSORS leads by <= 0.3

    def test_a_challenger_takes_over_once_it_leads_the_current_one(self) -> None:
        # After k rounds of PAPER, SCISSORS leads PAPER by (k - 6) / (k + 6):
        # more than 0.3 from k = 12 on.
        moves = self.leader([R] * 3 + [P] * 14)
        assert moves[2:15] == [P] * 13
        assert moves[15:] == [S] * 3

    def three_experts(self, rule: int) -> list[int]:
        """Main ROCK, gated SCISSORS, then the last gated PAPER: vs 3 rounds of
        ROCK PAPER takes over, then vs PAPER SCISSORS leads it by (k - 6) / (k + 6)
        after k rounds, more than 0.3 from k = 12 on."""
        gate = bot.Gate(main_bandit(R), gated(S, P), rule, 0.3, warmup=0)
        runner = Runner(bot.Blueprint(core=gate))
        opp = [R] * 3 + [P] * 14
        return runner.moves([R] * len(opp), opp)

    def test_with_priority_only_the_last_expert_takes_over_from_a_gated_one(
        self,
    ) -> None:
        assert self.three_experts(bot.LEADER)[15:] == [S] * 3
        assert self.three_experts(bot.LEADER_PRIORITY)[2:] == [P] * 16

    def test_only_leader_gates_several_experts_and_keeps_a_main_arm(self) -> None:
        with pytest.raises(blueprint.BlueprintError):
            bot.Blueprint(
                core=bot.Gate(main_bandit(R), gated(P, S), bot.MAIN_FIRST)
            ).compile({})
        with pytest.raises(blueprint.BlueprintError):
            bot.Blueprint(
                core=bot.Gate(main_bandit(), gated(P, S), bot.LEADER)
            ).compile({})

    def test_the_bandit_follows_the_winning_expert(self) -> None:
        moves = self.gate_bot(P, 0.0, 0, bot.BANDIT).moves([R] * 40, [R] * 40)
        assert moves[20:].count(P) > 18  # PAPER beats, ROCK ties
        moves = self.gate_bot(S, 0.0, 0, bot.BANDIT).moves([R] * 40, [R] * 40)
        assert moves[20:].count(R) > 18  # SCISSORS loses, ROCK ties

    def setup_method(self) -> None:
        random.seed(5)

    def test_a_winning_gated_arm_plays_once_warmed_up_and_over_the_edge(
        self,
    ) -> None:
        moves = self.gate_bot(P, 0.05, 3).moves([R] * 8, [R] * 8)
        assert moves[:3] == [R] * 3  # warming up: Thompson's only arm
        assert moves[3:] == [P] * 6  # PAPER beats ROCK every round

    def test_a_losing_gated_arm_never_plays(self) -> None:
        moves = self.gate_bot(S, 0.0, 0).moves([R] * 8, [R] * 8)
        assert set(moves) == {R}  # SCISSORS loses to ROCK every round

    def test_the_gated_arm_waits_for_its_edge(self) -> None:
        # PAPER vs ROCK: (w - l) / (w + t + l + 3) is 1/4 after one win, 2/5 after two.
        moves = self.gate_bot(P, 0.3, 0).moves([R] * 4, [R] * 4)
        assert moves == [R, R, P, P, P]

    def test_an_invalid_round_is_not_scored(self) -> None:
        moves = self.gate_bot(P, 0.3, 0).moves([R, X, R], [R, R, R])
        assert moves == [R, R, R, P]

    def test_it_needs_a_dirichlet_and_a_main_arm(self) -> None:
        decayed = main_bandit(R, scorer=bot.DecayedNet(0.9))
        with pytest.raises(blueprint.BlueprintError):
            bot.Blueprint(core=bot.Gate(decayed, gated(P))).compile({})
        with pytest.raises(blueprint.BlueprintError):
            bot.Blueprint(core=bot.Gate(main_bandit(), gated(R))).compile({})


class TestOverlay:
    def setup_method(self) -> None:
        random.seed(5)

    def test_stall_on_a_drawdown(self) -> None:
        runner = Runner(
            bot.Blueprint(
                core=bot.Bandit(predictors=(bot.Constant(R),), rotations=(bot.COPY,)),
                overlays=(bot.Stall(dd_window=6, dd_trigger=3, stall_rounds=10),),
            )
        )
        moves = runner.moves([R] * 20, [P] * 20)
        assert moves[:3] == [R, R, R]
        assert len(set(moves[3:])) > 1  # being read: random play

    def test_stall_locks_a_safe_lead(self) -> None:
        runner = Runner(
            bot.Blueprint(
                core=bot.Bandit(predictors=(bot.Constant(R),), rotations=(bot.COPY,)),
                overlays=(bot.Stall(lock_z=0.5, assumed_rounds=30),),
            )
        )
        moves = runner.moves([R] * 25, [S] * 25)
        assert len(set(moves[15:])) > 1

    def test_team_handshake(self) -> None:
        hand = list(overlays.HANDSHAKE)
        champion = list(overlays.ROLE_MOVE)[c.CHAMPION]
        support = Runner(
            bot.Blueprint(
                core=bot.Bandit(predictors=(bot.Constant(S),), rotations=(bot.COPY,)),
                overlays=(bot.Team(bot.SUPPORT),),
            )
        )
        my = hand + [P]
        opp = hand + [champion]
        moves = support.moves(my, opp)
        assert moves[: len(hand)] == hand
        assert moves[-1] == R  # throws the match: rock vs the champion's paper
        stranger = support.moves([S, S], [R, R])
        assert stranger == [S, S, S]  # first move matches, then it plays on

    def test_an_impostor_beats_the_champion_after_a_supports_handshake(self) -> None:
        hand = list(overlays.HANDSHAKE)
        roles = list(overlays.ROLE_MOVE)
        team = (
            bot.Blueprint(
                core=bot.Bandit(predictors=(bot.Constant(R),), rotations=(bot.COPY,)),
                overlays=(bot.Team(role),),
            )
            for role in (bot.CHAMPION, bot.IMPOSTOR)
        )
        champion, impostor = (Runner(b) for b in team)
        my = hand + [roles[c.SUPPORT], S]
        opp = hand + [roles[c.CHAMPION], P]
        assert impostor.moves(my, opp) == hand + [roles[c.SUPPORT], S, S]
        assert champion.moves(opp, my)[-1] == P  # it takes us for a support
        assert impostor.moves([S, R], [R, R]) == [S, R, R]  # a stranger

    def test_a_vigilant_champion_stops_throwing_at_an_impostors_first_win(
        self,
    ) -> None:
        hand = list(overlays.HANDSHAKES[c.ILIAD_V2])
        roles = list(overlays.ROLE_MOVE)
        champion, impostor = (
            Runner(
                bot.Blueprint(
                    core=bot.Bandit(
                        predictors=(bot.Constant(R),), rotations=(bot.COPY,)
                    ),
                    overlays=(bot.Team(role, bot.ILIAD_V2, vigilant=True),),
                )
            )
            for role in (bot.CHAMPION, bot.IMPOSTOR)
        )
        mine = hand + [roles[c.CHAMPION], P, R, R]
        theirs = impostor.moves(hand + [roles[c.SUPPORT], S, S, S], mine)[:-1]
        assert theirs == hand + [roles[c.SUPPORT], S, S, S]
        moves = champion.moves(mine, theirs)
        assert moves[len(hand) + 1] == P  # it takes the impostor for a support
        assert moves[len(hand) + 2 :] == [R, R, R]  # then plays its own move

    def test_vigilant_teammates_keep_throwing_while_the_other_does(self) -> None:
        hand = list(overlays.HANDSHAKES[c.ILIAD_V2])
        roles = list(overlays.ROLE_MOVE)
        champion, support = (
            Runner(
                bot.Blueprint(
                    core=bot.Bandit(
                        predictors=(bot.Constant(S),), rotations=(bot.COPY,)
                    ),
                    overlays=(bot.Team(role, bot.ILIAD_V2, vigilant=True),),
                )
            )
            for role in (bot.CHAMPION, bot.SUPPORT)
        )
        mine = hand + [roles[c.CHAMPION], P, P, P]
        theirs = hand + [roles[c.SUPPORT], R, R, R]
        assert champion.moves(mine, theirs)[-4:] == [P, P, P, P]
        assert support.moves(theirs, mine)[-4:] == [R, R, R, R]
        fake = hand + [roles[c.CHAMPION], P, S, P]  # a fake champion: one SCISSORS
        assert support.moves(theirs, fake)[-4:] == [R, R, S, S]

    def test_fleets_do_not_recognise_each_other(self) -> None:
        v1 = list(overlays.HANDSHAKES[c.ILIAD])
        support = Runner(
            bot.Blueprint(
                core=bot.Bandit(predictors=(bot.Constant(S),), rotations=(bot.COPY,)),
                overlays=(bot.Team(bot.SUPPORT, bot.ILIAD_V2),),
            )
        )
        v2_opening = int(overlays.HANDSHAKES[c.ILIAD_V2][0])
        assert support.moves([v2_opening], v1[:1]) == [v2_opening, S]

    def test_every_fleets_handshake_opens_differently(self) -> None:
        openings = {int(hand[0]) for hand in overlays.HANDSHAKES}
        assert len(openings) == len(overlays.HANDSHAKES)
        assert len(overlays.HANDSHAKES) == c.ILIAD_V3 + 1

    def test_emit_invalid_never_spends_more_than_the_budget(self) -> None:
        runner = Runner(
            bot.Blueprint(
                core=bot.Bandit(predictors=(bot.Constant(R),), rotations=(bot.COPY,)),
                overlays=(bot.EmitInvalid(1, 3),),
            )
        )
        assert runner.moves([R, X, R], [R, R, R]) == [R, X, R, X]
        spent = runner.moves([X, X, R], [R, R, R])
        assert spent[3] == R
        assert overlays.INVALID_BUDGET == 2


class TestReplay:
    def test_a_replay_predicts_the_replayed_bots_best_arm(self) -> None:
        # The opponent replays "beat their last move" with a scored core; we copy
        # its prediction of its own move.
        replayed = bot.Bandit(
            (bot.LastMove(bot.OPP),), (bot.BEAT,), bot.DecayedNet(0.9)
        )
        runner = signal_bot(bot.Replay(replayed))
        assert runner.last([R, S], [P, P]) == R  # it beats our scissors

    def test_a_replay_with_draws_names_the_move_thompson_picks_most(self) -> None:
        # From its side, two arms beat our last move and one always plays P (the
        # beat of Constant R). We alternate R, P: beating our last move ties or
        # loses every round, P wins or ties, so its Thompson draws pick P.
        replayed = bot.Bandit(
            (bot.LastMove(bot.OPP), bot.LastMove(bot.OPP), bot.Constant(R)),
            (bot.BEAT,),
            bot.Dirichlet(1.0),
        )
        runner = signal_bot(bot.Replay(replayed, draws=64))
        my = [R, P] * 6
        assert runner.last(my, [R] * len(my)) == P

    def test_a_nested_replay_sees_the_history_swapped_back(self) -> None:
        # The opponent replays "beat their last move" from our side (so it beats the
        # opponent's own last move) and beats that; we copy its predicted move.
        ours = bot.Bandit((bot.LastMove(bot.OPP),), (bot.BEAT,), bot.DecayedNet(0.9))
        theirs = bot.Bandit((bot.Replay(ours),), (bot.BEAT,), bot.DecayedNet(0.9))
        runner = signal_bot(bot.Replay(theirs))
        # their last P -> we'd play S -> they'd play R
        assert runner.last([R, S], [P, P]) == R
        assert runner.last([R, S, R], [P, P, R]) == S  # R -> P -> S
