"""Aerodynamic disturbance helpers for the multirotor simulator.

The wind model uses an exact discrete Ornstein-Uhlenbeck update so the gust
variance stays stable when the simulator `dt` changes. The base wind remains a
deterministic offset and the gust process adds a seed-reproducible stochastic
component on top of it.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from math import exp, isfinite, sqrt


def _coerce_float(value: object, field_name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a real number") from exc
    if not isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    return result


def _coerce_vector(value: tuple[object, object, object], field_name: str) -> tuple[float, float, float]:
    if len(value) != 3:
        raise ValueError(f"{field_name} must contain exactly 3 values")
    return (
        _coerce_float(value[0], field_name),
        _coerce_float(value[1], field_name),
        _coerce_float(value[2], field_name),
    )


def _vector_norm(vector: tuple[float, float, float]) -> float:
    return sqrt(sum(component * component for component in vector))


def _advance_ou_component(
    *,
    current_value: float,
    target_mean: float,
    stationary_std: float,
    dt_s: float,
    correlation_time_s: float,
    rng: random.Random,
) -> float:
    if stationary_std <= 0.0:
        return target_mean
    decay = exp(-dt_s / correlation_time_s)
    innovation_scale = sqrt(max(0.0, 1.0 - decay * decay))
    return target_mean + decay * (current_value - target_mean) + innovation_scale * stationary_std * rng.gauss(0.0, 1.0)


@dataclass(slots=True)
class AerodynamicEnvironment:
    parasitic_drag_enabled: bool = False
    induced_hover_enabled: bool = False
    wind_velocity_m_s: tuple[float, float, float] = (0.0, 0.0, 0.0)
    wind_gust_std_m_s: tuple[float, float, float] = (0.0, 0.0, 0.0)
    wind_gust_time_constant_s: float = 0.25
    parasitic_drag_area_m2: float = 0.0
    air_density_kg_m3: float = 1.225
    induced_hover_loss_ratio: float = 0.0
    seed: int | None = None
    last_wind_base_velocity_m_s: tuple[float, float, float] = field(
        init=False,
        default=(0.0, 0.0, 0.0),
    )
    last_wind_gust_velocity_m_s: tuple[float, float, float] = field(
        init=False,
        default=(0.0, 0.0, 0.0),
    )
    last_wind_velocity_m_s: tuple[float, float, float] = field(
        init=False,
        default=(0.0, 0.0, 0.0),
    )
    _gust_velocity_m_s: tuple[float, float, float] = field(
        init=False,
        repr=False,
        default=(0.0, 0.0, 0.0),
    )
    last_parasitic_drag_force_newton: tuple[float, float, float] = field(
        init=False,
        default=(0.0, 0.0, 0.0),
    )
    last_induced_force_body_newton: tuple[float, float, float] = field(
        init=False,
        default=(0.0, 0.0, 0.0),
    )
    _rng: random.Random = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "parasitic_drag_enabled", bool(self.parasitic_drag_enabled))
        object.__setattr__(self, "induced_hover_enabled", bool(self.induced_hover_enabled))
        object.__setattr__(self, "wind_velocity_m_s", _coerce_vector(self.wind_velocity_m_s, "wind_velocity_m_s"))
        object.__setattr__(self, "wind_gust_std_m_s", _coerce_vector(self.wind_gust_std_m_s, "wind_gust_std_m_s"))
        object.__setattr__(self, "wind_gust_time_constant_s", _coerce_float(self.wind_gust_time_constant_s, "wind_gust_time_constant_s"))
        object.__setattr__(self, "parasitic_drag_area_m2", _coerce_float(self.parasitic_drag_area_m2, "parasitic_drag_area_m2"))
        object.__setattr__(self, "air_density_kg_m3", _coerce_float(self.air_density_kg_m3, "air_density_kg_m3"))
        object.__setattr__(self, "induced_hover_loss_ratio", _coerce_float(self.induced_hover_loss_ratio, "induced_hover_loss_ratio"))
        if self.parasitic_drag_area_m2 < 0.0:
            raise ValueError("parasitic_drag_area_m2 must be non-negative")
        if self.air_density_kg_m3 <= 0.0:
            raise ValueError("air_density_kg_m3 must be positive")
        if self.induced_hover_loss_ratio < 0.0:
            raise ValueError("induced_hover_loss_ratio must be non-negative")
        if self.wind_gust_time_constant_s <= 0.0:
            raise ValueError("wind_gust_time_constant_s must be positive")
        if any(component < 0.0 for component in self.wind_gust_std_m_s):
            raise ValueError("wind_gust_std_m_s must be non-negative")
        object.__setattr__(self, "_rng", random.Random(self.seed))
        object.__setattr__(self, "_gust_velocity_m_s", (0.0, 0.0, 0.0))

    def is_active(self) -> bool:
        return self.parasitic_drag_enabled or self.induced_hover_enabled or any(
            component != 0.0 for component in self.wind_velocity_m_s
        ) or any(component != 0.0 for component in self.wind_gust_std_m_s)

    def sample_wind_velocity(self, dt_s: float) -> tuple[float, float, float]:
        dt = _coerce_float(dt_s, "dt_s")
        if dt <= 0.0:
            raise ValueError("dt_s must be positive")

        gust = tuple(
            _advance_ou_component(
                current_value=current_component,
                target_mean=0.0,
                stationary_std=stationary_std,
                dt_s=dt,
                correlation_time_s=self.wind_gust_time_constant_s,
                rng=self._rng,
            )
            for current_component, stationary_std in zip(self._gust_velocity_m_s, self.wind_gust_std_m_s)
        )
        wind = tuple(base + delta for base, delta in zip(self.wind_velocity_m_s, gust))
        object.__setattr__(self, "last_wind_base_velocity_m_s", self.wind_velocity_m_s)
        object.__setattr__(self, "last_wind_gust_velocity_m_s", gust)
        object.__setattr__(self, "last_wind_velocity_m_s", wind)
        object.__setattr__(self, "_gust_velocity_m_s", gust)
        return wind

    def compute_parasitic_drag_force_newton(
        self,
        relative_air_velocity_m_s: tuple[float, float, float],
    ) -> tuple[float, float, float]:
        if not self.parasitic_drag_enabled or self.parasitic_drag_area_m2 <= 0.0:
            force = (0.0, 0.0, 0.0)
            object.__setattr__(self, "last_parasitic_drag_force_newton", force)
            return force

        speed = _vector_norm(relative_air_velocity_m_s)
        if speed <= 0.0:
            force = (0.0, 0.0, 0.0)
            object.__setattr__(self, "last_parasitic_drag_force_newton", force)
            return force

        scale = -0.5 * self.air_density_kg_m3 * self.parasitic_drag_area_m2 * speed
        force = tuple(scale * component for component in relative_air_velocity_m_s)
        object.__setattr__(self, "last_parasitic_drag_force_newton", force)
        return force

    def compute_induced_force_body_newton(
        self,
        collective_thrust_newton: float,
        *,
        max_collective_thrust_newton: float,
    ) -> tuple[float, float, float]:
        if not self.induced_hover_enabled or self.induced_hover_loss_ratio <= 0.0:
            force = (0.0, 0.0, 0.0)
            object.__setattr__(self, "last_induced_force_body_newton", force)
            return force

        thrust = max(0.0, _coerce_float(collective_thrust_newton, "collective_thrust_newton"))
        max_thrust = _coerce_float(max_collective_thrust_newton, "max_collective_thrust_newton")
        if max_thrust <= 0.0:
            raise ValueError("max_collective_thrust_newton must be positive")

        induced_loss_newton = self.induced_hover_loss_ratio * thrust * (thrust / max_thrust)
        induced_loss_newton = min(induced_loss_newton, thrust)
        force = (0.0, 0.0, -induced_loss_newton)
        object.__setattr__(self, "last_induced_force_body_newton", force)
        return force
