import pytest

from app.blueprints.customers.forms import CustomerForm
from app.extensions import db
from app.models.customer_segment import CustomerSegment


@pytest.fixture()
def segment(app):
    s = CustomerSegment(name="Comercio", is_active=True)
    db.session.add(s)
    db.session.commit()
    return s


def _validate(app, **data):
    with app.test_request_context("/customers/new", method="POST", data=data):
        form = CustomerForm()
        return form.validate(), form.errors


def test_name_and_segment_alone_are_enough_to_create_a_customer(app, segment):
    ok, errors = _validate(app, name="Acme", segment_id=str(segment.id))
    assert ok, errors


def test_rut_is_optional(app, segment):
    ok, errors = _validate(app, name="Acme", segment_id=str(segment.id), rut="")
    assert ok, errors


def test_name_is_required(app, segment):
    ok, errors = _validate(app, segment_id=str(segment.id))
    assert not ok
    assert "name" in errors


def test_segment_is_required(app, segment):
    ok, errors = _validate(app, name="Acme")
    assert not ok
    assert "segment_id" in errors


def test_empty_segment_placeholder_is_rejected(app, segment):
    # The select opens on "— Select a segment —" (value ""); submitting it
    # unchanged must fail validation, not save a null segment (#77).
    ok, errors = _validate(app, name="Acme", segment_id="")
    assert not ok
    assert "segment_id" in errors


def test_segment_choices_start_with_the_placeholder(app, segment):
    with app.test_request_context():
        form = CustomerForm()
        assert form.segment_id.choices[0][0] == ""
