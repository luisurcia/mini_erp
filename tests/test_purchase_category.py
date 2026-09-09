from sqlalchemy import text

from app.blueprints.purchases.forms import PurchaseForm
from app.extensions import db
from app.models.purchase_category import PurchaseCategory
from app.schema import ensure_purchase_category_catalog


def test_ensure_defaults_seeds_the_starter_list_once(app):
    PurchaseCategory.ensure_defaults()
    PurchaseCategory.ensure_defaults()

    names = [c.name for c in PurchaseCategory.query.order_by(PurchaseCategory.id).all()]
    assert names == [
        "No definido",
        "Insumos",
        "Repuestos",
        "Artículos de Limpieza",
        "Otros",
    ]


def test_form_lists_active_categories_with_no_definido_first(app):
    PurchaseCategory.ensure_defaults()
    inactive = PurchaseCategory(name="Vieja", is_active=False)
    db.session.add(inactive)
    db.session.commit()

    with app.test_request_context():
        form = PurchaseForm()

    labels = [label for _, label in form.category_id.choices]
    assert labels[0] == "No definido"
    assert "Vieja" not in labels


def test_form_keeps_an_inactive_assigned_category_selectable_on_edit(app):
    PurchaseCategory.ensure_defaults()
    old = PurchaseCategory(name="Descontinuada", is_active=False)
    db.session.add(old)
    db.session.commit()

    class FakePurchase:
        category_id = old.id
        category = old

    with app.test_request_context():
        form = PurchaseForm(purchase=FakePurchase())

    assert old.id in [value for value, _ in form.category_id.choices]


def test_migration_backfills_free_text_categories_without_data_loss(app):
    PurchaseCategory.ensure_defaults()
    # Recreate a pre-#110 `purchases` table: free-text `category`, no FK.
    db.session.execute(text("DROP TABLE purchases"))
    db.session.execute(
        text(
            "CREATE TABLE purchases ("
            " id INTEGER PRIMARY KEY, sequence INTEGER, purchase_date DATE,"
            " item VARCHAR(200), supplier VARCHAR(160), category VARCHAR(80),"
            " invoice_number VARCHAR(60), amount NUMERIC(12,2),"
            " includes_tax BOOLEAN, notes VARCHAR(255), voided BOOLEAN,"
            " created_at DATETIME, updated_at DATETIME)"
        )
    )
    db.session.execute(
        text(
            "INSERT INTO purchases "
            "(sequence, purchase_date, item, supplier, amount, includes_tax, "
            " voided, category, created_at, updated_at) VALUES "
            "(1,'2026-06-01','A','P',1000,0,0,'Aseo','2026-06-01','2026-06-01'),"
            "(2,'2026-06-02','B','Q',2000,0,0,'insumos','2026-06-02','2026-06-02'),"
            "(3,'2026-06-03','C','R',3000,0,0,NULL,'2026-06-03','2026-06-03')"
        )
    )
    db.session.commit()

    ensure_purchase_category_catalog()

    rows = db.session.execute(
        text("SELECT sequence, category_id FROM purchases ORDER BY sequence")
    ).fetchall()
    by_id = {c.id: c.name for c in PurchaseCategory.query.all()}
    assert by_id[rows[0].category_id] == "Aseo"  # new category from free text
    assert by_id[rows[1].category_id] == "Insumos"  # case-insensitive match
    assert by_id[rows[2].category_id] == "No definido"  # NULL -> fallback

    columns = {c["name"] for c in db.inspect(db.engine).get_columns("purchases")}
    assert "category" not in columns
