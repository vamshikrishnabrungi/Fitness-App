from backend.app.main import app


def test_every_authenticated_mutation_declares_idempotency_key() -> None:
    schema = app.openapi()
    missing: list[str] = []
    for path, path_item in schema["paths"].items():
        for method in ("post", "put", "patch", "delete"):
            operation = path_item.get(method)
            if not operation or not operation.get("security"):
                continue
            parameters = operation.get("parameters", [])
            if not any(
                parameter.get("in") == "header"
                and parameter.get("name") == "Idempotency-Key"
                and parameter.get("required") is True
                for parameter in parameters
            ):
                missing.append(f"{method.upper()} {path}")
    assert missing == []


def test_public_authentication_commands_do_not_require_an_idempotency_header() -> None:
    operation = app.openapi()["paths"]["/api/v1/auth/otp/request"]["post"]
    assert not any(parameter.get("name") == "Idempotency-Key" for parameter in operation.get("parameters", []))
