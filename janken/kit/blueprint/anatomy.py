"""A whole bot: guards, a core predictor, overlays."""

import dataclasses
from collections.abc import Mapping

from . import encoder, lowering
from .binding import bind, structural_names
from .compiled import Compiled
from .guards import Guard
from .heuristic import Heuristic
from .overlays import Overlay
from .predictor import Predictor


@dataclasses.dataclass(frozen=True)
class Blueprint:
    """A whole bot: guards, a core predictor (a Heuristic for an L1 bot, else a
    Bandit or a Gate), overlays. The default core plays at random."""

    guards: tuple[Guard, ...] = ()
    core: Predictor = Heuristic()
    overlays: tuple[Overlay, ...] = ()

    def compile(self, defaults: Mapping[str, float | int]) -> Compiled:
        """Validate and encode the blueprint for a bot with these defaults. Its
        structural parameters (binding.py) are bound to them first."""
        fixed = structural_names(self)
        bound = bind(self, {n: defaults[n] for n in fixed if n in defaults})
        return encoder.Encoder(defaults, fixed).encode(
            bound.guards, lowering.lower(bound.core), bound.overlays
        )
