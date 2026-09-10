from app.extensions import db
from app.models.customer import Customer
from app.models.customer_segment import CustomerSegment
from app.repositories.customer_repository import CustomerRepository
from app.search import search_ilike


def _customers(app):
    seg = CustomerSegment(name="Otros")
    db.session.add(seg)
    db.session.flush()
    for name, rut, nick in [
        ("Claudio Milla", "11.111.111-1", None),
        ("Inspira Sport", None, "Inspira"),
        ("La Farine", "22.222.222-2", None),
        ("milla y cia", None, None),
    ]:
        db.session.add(Customer(name=name, rut=rut, nickname=nick, segment_id=seg.id))
    db.session.commit()


def test_search_ilike_empty_term_returns_query_unchanged(app):
    _customers(app)
    assert search_ilike(Customer.query, "", Customer.name).count() == 4
    assert search_ilike(Customer.query, "   ", Customer.name).count() == 4
    assert search_ilike(Customer.query, None, Customer.name).count() == 4


def test_search_ilike_matches_any_column_case_insensitively(app):
    _customers(app)
    hits = search_ilike(
        Customer.query, "MILLA", Customer.name, Customer.nickname
    ).all()
    assert {c.name for c in hits} == {"Claudio Milla", "milla y cia"}


def test_customer_repository_search_by_name_rut_nickname(app):
    _customers(app)
    repo = CustomerRepository()

    assert [c.name for c in repo.search("milla")] == ["Claudio Milla", "milla y cia"]
    assert [c.name for c in repo.search("22.222")] == ["La Farine"]
    assert [c.name for c in repo.search("inspira")] == ["Inspira Sport"]  # nickname
    assert len(repo.search("")) == 4
    assert repo.search("nada de nada") == []


def test_customer_repository_search_orders_by_name(app):
    _customers(app)
    names = [c.name for c in CustomerRepository().search("")]
    assert names == sorted(names, key=str.lower) or names == sorted(names)


def test_customer_repository_all_by_name_is_case_insensitive_alphabetical(app):
    _customers(app)  # inserted: Claudio, Inspira, La Farine, "milla y cia"
    names = [c.name for c in CustomerRepository().all_by_name()]
    assert names == ["Claudio Milla", "Inspira Sport", "La Farine", "milla y cia"]
