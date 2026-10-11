"""A whole bot: guards, a core predictor, overlays."""

import dataclasses
from collections.abc import Mapping

from . import encoder, lowering
from .compiled import Compiled
from .composites import Bandit
from .guards import Guard
from .overlays import Overlay
from .predictor import Predictor


@dataclasses.dataclass(frozen=True)
class Blueprint:
    """A whole bot: guards, a core predictor (a Bandit or a Gate), overlays."""

    guards: tuple[Guard, ...] = ()
    core: Predictor = Bandit()
    overlays: tuple[Overlay, ...] = ()

    def compile(self, defaults: Mapping[str, float | int]) -> Compiled:
        """Validate and encode the blueprint for a bot with these defaults."""
        return encoder.Encoder(defaults).encode(
            self.guards, lowering.lower(self.core), self.overlays
        )
