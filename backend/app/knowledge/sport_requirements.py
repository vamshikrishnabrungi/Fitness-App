from __future__ import annotations

SPORT_SCOPE_REQUIREMENTS: dict[str, dict[str, tuple[str, ...]]] = {
    "running": {
        "event_code": (
            "run_walk", "100m", "200m", "400m", "800m", "1500m", "mile",
            "5k", "10k", "half_marathon", "marathon", "trail", "ultra",
        )
    },
}

REQUIRED_DEMAND_DIMENSIONS = (
    "competition_format", "effort_duration", "work_recovery", "force_direction",
    "contraction_behavior", "energy_system", "repeated_effort", "schedule_congestion",
    "tissue_load", "environment_surface", "monitoring",
)
REQUIRED_PHASES = ("general_preparation", "specific_preparation", "competition", "transition")
REQUIRED_RECIPE_FAMILIES = {
    "running": ("preparation", "endurance", "interval", "speed", "strength", "tissue_capacity", "recovery"),
}
DEFAULT_RECIPE_FAMILIES = REQUIRED_RECIPE_FAMILIES["running"]


def package_coverage_errors(sport_code: str, *, demands, priorities, recipes, phases, week_templates) -> list[str]:
    if sport_code != "running":
        return ["only the running knowledge package is supported"]
    errors: list[str] = []
    dimensions = {
        row.dimension_code for row in demands
        if all(getattr(row, field, None) is None for field in ("event_code", "role_code", "discipline_code", "format_code"))
    }
    missing_dimensions = sorted(set(REQUIRED_DEMAND_DIMENSIONS) - dimensions)
    if missing_dimensions:
        errors.append(f"missing generic demand dimensions: {', '.join(missing_dimensions)}")
    for field, values in SPORT_SCOPE_REQUIREMENTS[sport_code].items():
        represented_demands = {getattr(row, field) for row in demands if getattr(row, field) is not None}
        represented_priorities = {getattr(row, field) for row in priorities if getattr(row, field) is not None}
        missing_demands = sorted(set(values) - represented_demands)
        missing_priorities = sorted(set(values) - represented_priorities)
        if missing_demands:
            errors.append(f"demand coverage missing {field}: {', '.join(missing_demands)}")
        if missing_priorities:
            errors.append(f"priority coverage missing {field}: {', '.join(missing_priorities)}")
    phase_codes = {row.phase_code for row in phases}
    week_phase_codes = {row.phase_code for row in week_templates}
    missing_phases = sorted(set(REQUIRED_PHASES) - phase_codes)
    missing_weeks = sorted(set(REQUIRED_PHASES) - week_phase_codes)
    if missing_phases:
        errors.append(f"program phases missing: {', '.join(missing_phases)}")
    if missing_weeks:
        errors.append(f"weekly structures missing phases: {', '.join(missing_weeks)}")
    available = {row.recipe_type for row in recipes}
    missing_families = sorted(set(REQUIRED_RECIPE_FAMILIES["running"]) - available)
    if missing_families:
        errors.append(f"session recipe families missing: {', '.join(missing_families)}")
    return errors
