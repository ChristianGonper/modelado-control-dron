"""Trajectory layer for the multirotor simulator."""

from ..core.contracts import TrajectoryReference
from .catalog import TRAJECTORY_FACTORIES, build_trajectory_from_config
from .contract import TrajectoryAdapter, TrajectoryContract
from .native import (
    BaseTrajectory,
    CircleTrajectory,
    HoldTrajectory,
    LissajousTrajectory,
    ParametricCurveTrajectory,
    SpiralTrajectory,
    StraightTrajectory,
)

__all__ = [
    "BaseTrajectory",
    "CircleTrajectory",
    "HoldTrajectory",
    "LissajousTrajectory",
    "ParametricCurveTrajectory",
    "SpiralTrajectory",
    "StraightTrajectory",
    "TRAJECTORY_FACTORIES",
    "TrajectoryAdapter",
    "TrajectoryContract",
    "TrajectoryReference",
    "build_trajectory_from_config",
]
