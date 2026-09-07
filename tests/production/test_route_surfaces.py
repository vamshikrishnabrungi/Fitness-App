from backend.app.main import app as public_app
from backend.app.worker_main import app as worker_app


def _paths(app) -> set[str]:
    paths = {route.path for route in app.routes if hasattr(route, "path")}
    for route in app.routes:
        contexts = getattr(route, "effective_route_contexts", None)
        if contexts:
            paths.update(context.path for context in contexts())
    return paths


def test_public_api_does_not_mount_internal_worker_routes():
    paths = _paths(public_app)
    assert not any(path.startswith("/internal") for path in paths)
    assert "/api/v1/activities" in paths


def test_worker_app_exposes_only_health_and_internal_routes():
    paths = _paths(worker_app)
    assert "/healthz" in paths
    assert "/internal/pubsub/{topic}" in paths
    assert all(path in {"/healthz", "/readyz"} or path.startswith("/internal") for path in paths)
