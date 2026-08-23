from types import SimpleNamespace

from backend.app.knowledge.sport_requirements import REQUIRED_DEMAND_DIMENSIONS, package_coverage_errors


def row(**values):
    defaults=dict(event_code=None,role_code=None,discipline_code=None,format_code=None)
    return SimpleNamespace(**{**defaults,**values})


def test_running_package_gate_requires_every_locked_event_scope():
    demands=[row(dimension_code=value) for value in REQUIRED_DEMAND_DIMENSIONS]
    priorities=[]
    recipes=[row(recipe_type=value) for value in ("preparation","endurance","interval","speed","strength","tissue_capacity","recovery")]
    phases=[row(phase_code=value) for value in ("general_preparation","specific_preparation","competition","transition")]
    weeks=[row(phase_code=value) for value in ("general_preparation","specific_preparation","competition","transition")]
    errors=package_coverage_errors("running",demands=demands,priorities=priorities,recipes=recipes,phases=phases,week_templates=weeks)
    assert any("run_walk" in value and "400m" in value for value in errors)


def test_swimming_scope_keeps_event_and_discipline_separate():
    demands=[row(dimension_code=value) for value in REQUIRED_DEMAND_DIMENSIONS]
    priorities=[]
    recipes=[row(recipe_type=value) for value in ("preparation","endurance","interval","power","strength","shoulder_capacity","recovery")]
    phases=[row(phase_code=value) for value in ("general_preparation","specific_preparation","competition","transition")]
    errors=package_coverage_errors("swimming",demands=demands,priorities=priorities,recipes=recipes,phases=phases,week_templates=phases)
    assert any("event_code" in value for value in errors)
    assert any("discipline_code" in value for value in errors)
