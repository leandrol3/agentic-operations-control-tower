"""Explicit didactic thresholds, not NovaCore production policy."""
import os
from decimal import Decimal
from pathlib import Path
from typing import Literal
from pydantic import Field, model_validator
from ..models import Contract
from .contracts import AgentSLO


class ControlPlaneConfig(Contract):
    version: str
    source: Literal['didactic_configured_example']
    window_size: int = Field(ge=2, le=50)
    min_samples: int = Field(ge=2, le=50)
    goal_warning_gap: Decimal = Field(ge=0, allow_inf_nan=False)
    trend_relative_tolerance: Decimal = Field(ge=0, le=1, allow_inf_nan=False)
    severe_completion_below: Decimal = Field(ge=0, le=100, allow_inf_nan=False)
    review_high_violations: int = Field(ge=2)
    slos: tuple[AgentSLO, ...] = Field(min_length=1)

    @model_validator(mode='after')
    def valid(self):
        if self.min_samples > self.window_size:
            raise ValueError('min_samples exceeds window_size')
        if len({s.slo_id for s in self.slos}) != len(self.slos):
            raise ValueError('Duplicate SLO ID')
        return self


def load_config():
    path = Path(os.environ.get('CONTROL_PLANE_CONFIG_FILE', 'config/lesson04-control-plane.json'))
    return ControlPlaneConfig.model_validate_json(path.read_text())
