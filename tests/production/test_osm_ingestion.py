from backend.app.maps.osm_ingestion import line_length_m, runnable_way, split_max_length


class Tags(dict):
    pass


def test_running_access_filter_rejects_private_and_unsafe_road_classes():
    assert runnable_way(Tags(highway="footway"))
    assert not runnable_way(Tags(highway="motorway"))
    assert not runnable_way(Tags(highway="path", access="private"))
    assert not runnable_way(Tags(highway="cycleway", foot="no"))
    assert runnable_way(Tags(highway="tertiary", sidewalk="both"))
    assert not runnable_way(Tags(highway="tertiary", sidewalk="no"))


def test_long_curved_geometry_is_split_into_claim_edges_no_longer_than_100m():
    # Roughly 333 metres near the equator, including a turn.
    coordinates = [(0.0, 0.0), (0.0015, 0.0), (0.0015, 0.0015)]
    parts = split_max_length(coordinates)
    assert len(parts) == 4
    assert all(line_length_m(part) <= 100.5 for part in parts)
    assert parts[0][0] == coordinates[0]
    assert parts[-1][-1] == coordinates[-1]
