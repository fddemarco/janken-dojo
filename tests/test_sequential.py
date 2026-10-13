"""janken/lab/sequential.py: alpha spending, Student's t, the stopping rules."""

import random

import pytest

from janken.lab import sequential


class TestSpending:
    def test_all_of_alpha_is_spent_by_the_last_look(self) -> None:
        alphas = sequential.look_alphas([0.2, 0.4, 0.6, 0.8, 1.0], 0.05)
        assert sum(alphas) == pytest.approx(0.05)
        assert alphas[0] < 1e-4 < alphas[-1]  # O'Brien-Fleming: little spent early

    def test_spending_grows_with_the_information(self) -> None:
        spent = [sequential.spent(t, 0.05) for t in (0.0, 0.25, 0.5, 1.0)]
        assert spent == sorted(spent) and spent[0] == 0.0
        assert spent[-1] == pytest.approx(0.05)

    def test_a_look_of_equally_spaced_ones(self) -> None:
        assert sequential.look_alpha(2, 4, 0.05) == pytest.approx(
            sequential.spent(0.5, 0.05) - sequential.spent(0.25, 0.05)
        )

    def test_the_looks_fall_evenly_over_the_plan(self) -> None:
        assert sequential.ladder(10, 5) == [2, 4, 6, 8, 10]
        assert sequential.ladder(3, 5) == [1, 2, 3]


class TestStudentT:
    @pytest.mark.parametrize(
        ("df", "table"), [(1, 12.706), (2, 4.303), (5, 2.571), (30, 2.042)]
    )
    def test_bounds_match_the_tables(self, df: int, table: float) -> None:
        assert sequential.t_bound(0.05, df) == pytest.approx(table, abs=1e-3)

    def test_many_degrees_of_freedom_are_the_normal(self) -> None:
        assert sequential.t_bound(0.05, 100_000) == pytest.approx(1.96, abs=1e-3)

    def test_the_tail_is_alpha_at_the_bound(self) -> None:
        bound = sequential.t_bound(0.01, 4)
        assert sequential.t_two_sided(bound, 4) == pytest.approx(0.01, rel=1e-6)


class TestClearOf:
    def test_one_value_has_no_spread_to_judge(self) -> None:
        assert not sequential.clear_of([0.9], 0.36, 0.05)

    def test_a_far_mean_with_a_small_spread_is_clear(self) -> None:
        assert sequential.clear_of([0.55, 0.57, 0.56], 0.36, 0.05)
        assert sequential.clear_of([0.10, 0.11, 0.12], 0.36, 0.05)

    def test_a_close_mean_is_not(self) -> None:
        assert not sequential.clear_of([0.30, 0.42, 0.37], 0.36, 0.05)

    def test_identical_values_are_clear_unless_on_the_level(self) -> None:
        assert sequential.clear_of([0.5, 0.5], 0.36, 0.05)
        assert not sequential.clear_of([0.36, 0.36], 0.36, 0.05)

    def test_stopping_on_noise_stays_under_alpha(self) -> None:
        # Pure noise around the level, looked at after every value from the third
        # on: the spent alphas keep the chance of ever stopping under alpha.
        rng = random.Random(0)
        n, alpha, trials = 10, 0.05, 1500
        looks = list(range(3, n + 1))
        alphas = sequential.look_alphas([k / n for k in looks], alpha)
        stopped = 0
        for _ in range(trials):
            values = [rng.gauss(0.0, 1.0) for _ in range(n)]
            if any(
                sequential.clear_of(values[:k], 0.0, a)
                for k, a in zip(looks, alphas, strict=True)
            ):
                stopped += 1
        assert stopped / trials <= alpha + 0.01


class TestLook:
    def test_a_strong_effect_is_clear(self) -> None:
        diffs = [0.5, 0.4, 0.6, 0.5, 0.45, 0.55] * 5
        seen = sequential.look(diffs, 0.5, 0.01, 0.04, 0.1)
        assert seen.clear and not seen.futile and seen.n == 30

    def test_no_effect_halfway_is_futile(self) -> None:
        diffs = [1.0, -1.0, 0.0] * 60  # a mean of exactly 0
        seen = sequential.look(diffs, 0.5, 0.01, 0.04, 0.1)
        assert seen.futile and not seen.clear

    def test_the_last_look_is_never_futile(self) -> None:
        seen = sequential.look([0.1, -0.1, 0.0], 1.0, 0.04, 0.04, 0.1)
        assert not seen.futile

    def test_conditional_power_follows_the_effect(self) -> None:
        weak = sequential.conditional_power(0.2, 0.5, 1.96)
        strong = sequential.conditional_power(3.0, 0.5, 1.96)
        assert weak < 0.1
        assert strong > 0.9
