from app.models.customer import Customer


def test_shipping_address_line_joins_filled_parts():
    customer = Customer(
        name="Acme",
        shipping_street="Av. Siempre Viva",
        shipping_number="742",
        shipping_commune="Providencia",
        shipping_city="Santiago",
        shipping_region="Metropolitana",
    )
    assert (
        customer.shipping_address_line
        == "Av. Siempre Viva 742, Providencia, Santiago, Metropolitana"
    )


def test_shipping_address_line_skips_missing_parts():
    customer = Customer(name="Acme", shipping_street="Calle 1", shipping_commune="Ñuñoa")
    assert customer.shipping_address_line == "Calle 1, Ñuñoa"


def test_shipping_address_line_is_none_when_empty():
    assert Customer(name="Acme").shipping_address_line is None
