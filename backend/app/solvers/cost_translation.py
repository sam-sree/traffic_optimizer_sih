"""
Translates the abstract weighted-objective "cost" score into real-world rupee
and time figures, so results are readable by someone who doesn't think in the
solver's internal unitless cost metric.

All conversion factors below are stated assumptions, not measured facts - they
are order-of-magnitude reasonable for an Indian urban delivery fleet, but are
deliberately exposed as parameters (not hidden constants) so they can be
overridden with real operator data if it's ever available. Do not present the
rupee figures as precise/measured - present them as "at an assumed fuel cost
of X and driver wage of Y" alongside the number, so the estimate's basis is
transparent.

Default assumptions:
- Fuel cost per km (~Rs 7/km): a light commercial delivery vehicle at roughly
  13 km/litre and diesel around Rs 90-95/litre.
- Driver wage per hour (~Rs 80/hour): roughly Rs 19,000/month over a ~240
  working-hour month for a delivery driver - a mid-range, not precise, figure.
These are illustrative defaults for a pitch, not a verified cost audit.
"""

from typing import Dict, Optional

DEFAULT_FUEL_COST_PER_KM_INR = 7.0
DEFAULT_DRIVER_WAGE_PER_HOUR_INR = 80.0


def compute_real_world_cost(
    total_time_sec: float,
    total_distance_m: float,
    fuel_cost_per_km_inr: float = DEFAULT_FUEL_COST_PER_KM_INR,
    driver_wage_per_hour_inr: float = DEFAULT_DRIVER_WAGE_PER_HOUR_INR,
) -> Dict[str, float]:
    """
    Converts real, already-computed route metrics (time, distance) into an
    estimated rupee cost. Does not fabricate any new metric - it's a linear
    transform of numbers the solver already produced.
    """
    distance_km = total_distance_m / 1000.0
    time_hours = total_time_sec / 3600.0

    fuel_cost_inr = distance_km * fuel_cost_per_km_inr
    labor_cost_inr = time_hours * driver_wage_per_hour_inr
    total_cost_inr = fuel_cost_inr + labor_cost_inr

    return {
        "fuel_cost_inr": round(fuel_cost_inr, 2),
        "labor_cost_inr": round(labor_cost_inr, 2),
        "total_cost_inr": round(total_cost_inr, 2),
        "assumptions": {
            "fuel_cost_per_km_inr": fuel_cost_per_km_inr,
            "driver_wage_per_hour_inr": driver_wage_per_hour_inr,
        },
    }


def compute_savings_vs_baseline(
    optimized_time_sec: float,
    optimized_distance_m: float,
    baseline_time_sec: float,
    baseline_distance_m: float,
    fuel_cost_per_km_inr: float = DEFAULT_FUEL_COST_PER_KM_INR,
    driver_wage_per_hour_inr: float = DEFAULT_DRIVER_WAGE_PER_HOUR_INR,
) -> Dict[str, float]:
    """
    Compares an optimized solution's real-world cost against a baseline
    (e.g. the naive Dijkstra nearest-neighbor solver, representing an
    "unoptimized" fleet) and reports the rupee and percentage savings.
    Returns zeroed savings (not a negative or crashed result) if the
    "optimized" run happens to be worse than baseline - that's a legitimate
    possible outcome, not an error, and should be shown honestly as such.
    """
    optimized = compute_real_world_cost(
        optimized_time_sec, optimized_distance_m, fuel_cost_per_km_inr, driver_wage_per_hour_inr
    )
    baseline = compute_real_world_cost(
        baseline_time_sec, baseline_distance_m, fuel_cost_per_km_inr, driver_wage_per_hour_inr
    )

    savings_inr = baseline["total_cost_inr"] - optimized["total_cost_inr"]
    savings_pct = (
        (savings_inr / baseline["total_cost_inr"]) * 100.0
        if baseline["total_cost_inr"] > 0 else 0.0
    )

    return {
        "optimized_cost_inr": optimized["total_cost_inr"],
        "baseline_cost_inr": baseline["total_cost_inr"],
        "savings_inr": round(savings_inr, 2),
        "savings_pct": round(savings_pct, 1),
        "assumptions": optimized["assumptions"],
    }
