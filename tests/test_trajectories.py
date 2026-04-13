from __future__ import annotations

import math

import pytest

from simulador_multirotor.core.contracts import TrajectoryReference
from simulador_multirotor.trajectories import (
    CircleTrajectory,
    LissajousTrajectory,
    ParametricCurveTrajectory,
    SpiralTrajectory,
    StraightTrajectory,
    TrajectoryAdapter,
    TrajectoryContract,
)


def test_trajectory_adapter_exposes_common_contract() -> None:
    adapter = TrajectoryAdapter(
        sample_fn=lambda time_s: TrajectoryReference(
            time_s=time_s,
            position_m=(time_s, 0.0, 0.0),
            velocity_m_s=(1.0, 0.0, 0.0),
            yaw_rad=0.0,
            valid_from_s=0.0,
            valid_until_s=1.0,
        ),
        kind="external-demo",
        source="simulated",
        duration_s=1.0,
        parameters={"family": "external"},
    )

    assert isinstance(adapter, TrajectoryContract)
    assert adapter.is_complete_at(1.5) is True
    reference = adapter.reference_at(0.25)
    assert reference.position_m == (0.25, 0.0, 0.0)
    assert reference.valid_until_s == pytest.approx(1.0)


def test_straight_trajectory_is_linear_and_clamped() -> None:
    trajectory = StraightTrajectory(
        kind="line",
        duration_s=1.0,
        start_position_m=(1.0, 2.0, 3.0),
        velocity_m_s=(2.0, 0.0, -1.0),
    )

    start = trajectory.reference_at(0.0)
    mid = trajectory.reference_at(0.5)
    past_end = trajectory.reference_at(1.5)

    assert start.position_m == (1.0, 2.0, 3.0)
    assert mid.position_m == pytest.approx((2.0, 2.0, 2.5))
    assert mid.velocity_m_s == pytest.approx((2.0, 0.0, -1.0))
    assert past_end.time_s == pytest.approx(1.0)
    assert past_end.position_m == pytest.approx((3.0, 2.0, 2.0))
    assert past_end.metadata["trajectory_exhausted"] is True


def test_circle_trajectory_matches_key_points() -> None:
    trajectory = CircleTrajectory(
        kind="circle",
        duration_s=2.0,
        center_m=(0.0, 0.0, 1.0),
        radius_m=2.0,
        angular_speed_rad_s=math.pi,
        start_phase_rad=0.0,
    )

    start = trajectory.reference_at(0.0)
    quarter = trajectory.reference_at(0.5)

    assert start.position_m == pytest.approx((2.0, 0.0, 1.0))
    assert start.velocity_m_s == pytest.approx((0.0, 2.0 * math.pi, 0.0))
    assert start.yaw_rad == pytest.approx(math.pi / 2.0)
    assert quarter.position_m == pytest.approx((0.0, 2.0, 1.0), abs=1e-12)


def test_spiral_trajectory_grows_radius_and_height() -> None:
    trajectory = SpiralTrajectory(
        kind="spiral",
        duration_s=2.0,
        center_m=(0.0, 0.0, 0.0),
        initial_radius_m=1.0,
        radial_rate_m_s=0.5,
        angular_speed_rad_s=math.pi,
        vertical_speed_m_s=0.25,
    )

    start = trajectory.reference_at(0.0)
    end = trajectory.reference_at(2.0)

    assert start.position_m == pytest.approx((1.0, 0.0, 0.0))
    assert start.velocity_m_s == pytest.approx((0.5, math.pi, 0.25))
    assert end.position_m == pytest.approx((2.0, 0.0, 0.5), abs=1e-12)


def test_parametric_curve_and_lissajous_are_smooth_and_periodic() -> None:
    parametric = ParametricCurveTrajectory(
        kind="parametric",
        duration_s=1.0,
        origin_m=(0.0, 0.0, 0.0),
        forward_speed_m_s=2.0,
        lateral_amplitude_m=1.0,
        lateral_frequency_rad_s=math.pi,
        vertical_amplitude_m=0.5,
        vertical_frequency_rad_s=2.0 * math.pi,
        lateral_phase_rad=0.0,
        vertical_phase_rad=math.pi / 2.0,
    )
    lissajous = LissajousTrajectory(
        kind="lissajous",
        duration_s=1.0,
        center_m=(0.0, 0.0, 0.0),
        amplitude_m=(1.0, 2.0, 3.0),
        frequency_rad_s=(math.pi, math.pi / 2.0, math.pi / 3.0),
        phase_rad=(0.0, math.pi / 2.0, 0.0),
    )

    parametric_reference = parametric.reference_at(0.25)
    lissajous_reference = lissajous.reference_at(1.0)

    assert parametric_reference.position_m == pytest.approx((0.5, math.sin(math.pi / 4.0), 0.0))
    assert parametric_reference.velocity_m_s[0] == pytest.approx(2.0)
    assert lissajous_reference.position_m == pytest.approx((0.0, 0.0, 3.0 * math.sin(math.pi / 3.0)))
    assert lissajous_reference.velocity_m_s[0] == pytest.approx(-math.pi)
    assert lissajous_reference.velocity_m_s[1] == pytest.approx(-math.pi)
