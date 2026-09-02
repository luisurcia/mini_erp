from app.models.user import User


def _user(role):
    return User(username="test", role=role)


def test_admin_can_access_every_module():
    admin = _user(User.ROLE_ADMIN)
    for module in User._ALL_MODULES:
        assert admin.can_access(module)


def test_bodeguero_can_access_only_inventory_supplies():
    bodeguero = _user(User.ROLE_BODEGUERO)
    assert bodeguero.can_access(User.MODULE_INVENTORY)
    assert bodeguero.can_access(User.MODULE_SUPPLIES)
    # Products catalog is admin-only master data (#78).
    assert not bodeguero.can_access(User.MODULE_PRODUCTS)
    assert not bodeguero.can_access(User.MODULE_SALES)
    assert not bodeguero.can_access(User.MODULE_TOP_CUSTOMERS)
    assert not bodeguero.can_access(User.MODULE_CUSTOMERS)
    # Purchases ledger is admin-only financial data (#93).
    assert not bodeguero.can_access(User.MODULE_PURCHASES)


def test_ventas_can_access_only_sales_top_customers_customers():
    ventas = _user(User.ROLE_VENTAS)
    assert ventas.can_access(User.MODULE_SALES)
    assert ventas.can_access(User.MODULE_TOP_CUSTOMERS)
    assert ventas.can_access(User.MODULE_CUSTOMERS)
    # Products catalog is admin-only master data (#78); the sale form's
    # product picker doesn't gate on it.
    assert not ventas.can_access(User.MODULE_PRODUCTS)
    assert not ventas.can_access(User.MODULE_INVENTORY)
    assert not ventas.can_access(User.MODULE_SUPPLIES)
    assert not ventas.can_access(User.MODULE_PURCHASES)


def test_is_admin_only_true_for_admin_role():
    assert _user(User.ROLE_ADMIN).is_admin
    assert not _user(User.ROLE_BODEGUERO).is_admin
    assert not _user(User.ROLE_VENTAS).is_admin


def test_display_name_uses_full_name_when_set():
    user = User(username="mundurraga", first_name="Mario", last_name="Undurraga")
    assert user.display_name == "Mario Undurraga"


def test_display_name_handles_only_one_name_part():
    assert User(username="m", first_name="Mario").display_name == "Mario"
    assert User(username="u", last_name="Undurraga").display_name == "Undurraga"


def test_display_name_falls_back_to_username():
    assert User(username="admin").display_name == "admin"
    assert User(username="admin", first_name="", last_name="  ").display_name == "admin"
