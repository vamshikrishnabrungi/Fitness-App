from backend.app.maps.valhalla import normalized_confidence


def test_match_confidence_penalizes_missing_and_distant_points() -> None:
    good, ratio, distance = normalized_confidence(
        [{"type": "matched", "distance_from_trace_point": 2} for _ in range(10)]
    )
    weak, _, _ = normalized_confidence(
        [{"type": "matched", "distance_from_trace_point": 25}] * 5
        + [{"type": "unmatched", "distance_from_trace_point": 0}] * 5
    )
    assert good > 0.95
    assert ratio == 1
    assert distance == 2
    assert weak < 0.85
