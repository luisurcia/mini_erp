from app.models.user import User


def _user(role):
    return User(username="test", role=role)


def test_admin_can_access_every_module():
    admin = _user(User.ROLE_ADMIN)
    for module in User._ALL_MODULES:
        assert admin.can_access(module)


def test_bodeguero_can_access_only_products_inventory_supplies():
    bodeguero = _user(User.ROLE_BODEGUERO)
    assert bodeguero.can_access(User.MODULE_PRODUCTS)
    assert bodeguero.can_access(User.MODULE_INVENTORY)
    assert bodeguero.can_access(User.MODULE_SUPPLIES)
    assert not bodeguero.can_access(User.MODULE_SALES)
    assert not bodeguero.can_access(User.MODULE_TOP_CUSTOMERS)
    assert not bodeguero.can_access(User.MODULE_CUSTOMERS)


def test_ventas_can_access_only_sales_products_top_customers_customers():
    ventas = _user(User.ROLE_VENTAS)
    assert ventas.can_access(User.MODULE_SALES)
    assert ventas.can_access(User.MODULE_PRODUCTS)
    assert ventas.can_access(User.MODULE_TOP_CUSTOMERS)
    assert ventas.can_access(User.MODULE_CUSTOMERS)
    assert not ventas.can_access(User.MODULE_INVENTORY)
    assert not ventas.can_access(User.MODULE_SUPPLIES)


def test_is_admin_only_true_for_admin_role():
    assert _user(User.ROLE_ADMIN).is_admin
    assert not _user(User.ROLE_BODEGUERO).is_admin
    assert not _user(User.ROLE_VENTAS).is_admin
