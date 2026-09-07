from backend.app.training.models import SessionItem


def test_session_item_block_type_fits_all_canonical_category_codes():
    assert SessionItem.__table__.c.block_type.type.length >= 80
