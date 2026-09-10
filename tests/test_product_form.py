from app.blueprints.products.forms import ProductForm


def _validate(app, **data):
    # Scoby's config: flavor/size/sku/price hidden -> form is name +
    # short_name + color + is_active. Apply the same field-dropping the
    # route does so the test mirrors production.
    from app.blueprints.products.routes import _apply_product_field_visibility
    from app.models.company import Company

    settings = Company.get_settings()
    settings.product_flavor_enabled = False
    settings.product_size_enabled = False
    settings.product_sku_enabled = False
    settings.product_price_enabled = False

    with app.test_request_context("/products/new", method="POST", data=data):
        form = ProductForm()
        _apply_product_field_visibility(form, settings)
        return form.validate(), form.errors


def test_color_is_required(app):
    ok, errors = _validate(app, name="Kombucha Pomelo", short_name="P", color="")
    assert not ok
    assert "color" in errors


def test_color_must_be_a_hex_value(app):
    ok, errors = _validate(app, name="Kombucha Pomelo", short_name="P", color="rojo")
    assert not ok
    assert "color" in errors


def test_valid_hex_color_passes(app):
    ok, errors = _validate(app, name="Kombucha Pomelo", short_name="P", color="#E0762E")
    assert ok, errors
