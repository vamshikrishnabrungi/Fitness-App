from backend.app.knowledge.importer import find_unresolved_relation_codes


def test_catalogue_relation_validation_reports_unknown_stable_codes():
    payloads = [
        {"progression_codes": ["known", "missing-b"], "regression_codes": ["missing-a"]},
        {"substitution_codes": ["missing-b", "known"]},
    ]
    assert find_unresolved_relation_codes(payloads, {"known"}) == ["missing-a", "missing-b"]


def test_catalogue_relation_validation_accepts_complete_graph():
    payloads = [{"progression_codes": ["next"], "substitution_codes": ["peer"]}]
    assert find_unresolved_relation_codes(payloads, {"next", "peer"}) == []
