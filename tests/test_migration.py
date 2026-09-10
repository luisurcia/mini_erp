from datetime import datetime
from decimal import Decimal

import pytest
from openpyxl import Workbook

from app.exceptions import MiniErpError
from app.extensions import db
from app.migration import build_report, import_ventas
from app.models.customer import Customer
from app.models.customer_segment import CustomerSegment
from app.models.product import Product
from app.models.sales import Sale

HEADER = [
    "Fecha", "cliente", "cantidad", "P", "J", "M", "O", "C", "EL", "FM", "GB",
    "valor unitario", "valor total Neto", "con iva?", "Iva", "N° Factura",
    "total pago", "Fecha de pago", "Comentario",
]


def _row(fecha, cliente, flavors, vu, neto, con_iva, total_pago,
         fecha_pago=None, nfact=None, coment=None):
    """flavors: dict como {'J': 5, 'M': 2}."""
    cols = {"P": 3, "J": 4, "M": 5, "O": 6, "C": 7, "EL": 8, "FM": 9, "GB": 10}
    r = [None] * 19
    r[0], r[1] = fecha, cliente
    r[2] = sum(flavors.values())
    for k, v in flavors.items():
        r[cols[k]] = v
    r[11], r[12], r[13], r[16] = vu, neto, con_iva, total_pago
    r[17], r[15], r[18] = fecha_pago, nfact, coment
    return r


@pytest.fixture()
def segment(app):
    s = CustomerSegment(name="Otros", is_active=True)
    db.session.add(s)
    db.session.commit()
    return s


def _xlsx(tmp_path, data_rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "Ventas"
    ws.append(HEADER)
    for r in data_rows:
        ws.append(r)
    path = tmp_path / "ventas.xlsx"
    wb.save(path)
    return str(path)


def test_basic_multiproduct_sale(app, segment, tmp_path):
    path = _xlsx(tmp_path, [
        _row(datetime(2025, 6, 4), "Claudio Milla", {"J": 5, "M": 3}, 1680, 13440,
             "no", 13440, fecha_pago=datetime(2025, 6, 5), nfact="Boleta 2"),
    ])
    result = import_ventas(path, dry_run=False, overrides={}, note_only={})

    assert result.sales == 1
    assert len(result.products_created) == 8
    sale = Sale.query.one()
    assert sale.customer.name == "Claudio Milla"
    assert sale.customer.segment_id == segment.id
    assert len(sale.items) == 2
    assert {i.quantity for i in sale.items} == {5, 3}
    assert all(i.warehouse_id is None for i in sale.items)
    assert all(i.unit_price == Decimal("1680") for i in sale.items)
    assert sale.tax_applied is False
    assert sale.total_amount == Decimal("13440")
    assert sale.status == "completed"
    assert sale.payment_status == "paid"
    assert sale.paid_at == datetime(2025, 6, 5)
    assert sale.payment_reference == "Migración planilla"
    assert sale.invoice_number == "Boleta 2"


def test_iva_sale_computes_tax_from_total_minus_subtotal(app, segment, tmp_path):
    path = _xlsx(tmp_path, [
        _row(datetime(2025, 7, 1), "Inspira Sport", {"P": 5, "J": 5, "M": 5, "O": 5},
             1680, 33600, "sí", 39984),
    ])
    import_ventas(path, dry_run=False, overrides={}, note_only={})
    sale = Sale.query.one()
    assert sale.tax_applied is True
    assert sale.tax_rate_applied == Decimal("19")
    assert sale.subtotal_amount == Decimal("33600")
    assert sale.total_amount == Decimal("39984")
    assert sale.tax_amount == Decimal("6384")
    assert sale.payment_status == "unpaid"


def test_unit_price_is_rounded_to_whole_pesos(app, segment, tmp_path):
    path = _xlsx(tmp_path, [
        _row(datetime(2025, 6, 23), "Liliana Lopez", {"J": 20}, 1466.4, 29328, "no", 29328),
    ])
    import_ventas(path, dry_run=False, overrides={}, note_only={})
    sale = Sale.query.one()
    assert sale.items[0].unit_price == Decimal("1466")


def test_overrides_force_no_tax_and_fixed_total(app, segment, tmp_path):
    path = _xlsx(tmp_path, [
        # fila 2: "una parte" -> sin IVA
        _row(datetime(2025, 6, 4), "Claudio Milla", {"J": 18}, 1680, 30240,
             "una parte", 31830),
        # fila 3: marcada sí pero override sin IVA + total fijo
        _row(datetime(2026, 2, 23), "Pedro Philippi", {"P": 10, "M": 10}, 1500, 30000,
             "no", 35000),
    ])
    overrides = {
        2: dict(force_no_tax=True, total_amount=Decimal("30240"), note="una parte -> sin IVA"),
        3: dict(total_amount=Decimal("30000"), force_no_tax=True, note="neto $30.000"),
    }
    result = import_ventas(path, dry_run=False, overrides=overrides, note_only={})

    milla = Sale.query.join(Customer).filter(Customer.name == "Claudio Milla").one()
    assert milla.tax_applied is False
    assert milla.total_amount == Decimal("30240")

    pedro = Sale.query.join(Customer).filter(Customer.name == "Pedro Philippi").one()
    assert pedro.tax_applied is False
    assert pedro.total_amount == Decimal("30000")
    assert "$5.000" not in (pedro.notes or "")  # note text is from override
    assert pedro.notes.endswith("neto $30.000")
    assert {(r[0]) for r in result.special_rows} == {2, 3}


def test_customers_are_deduped_by_normalized_name(app, segment, tmp_path):
    path = _xlsx(tmp_path, [
        _row(datetime(2025, 6, 4), "Dafne  Gato", {"J": 2}, 1000, 2000, "no", 2000),
        _row(datetime(2025, 7, 4), "dafne gato", {"M": 1}, 1000, 1000, "no", 1000),
        _row(datetime(2025, 8, 4), "Otro Cliente", {"O": 1}, 1000, 1000, "no", 1000),
    ])
    result = import_ventas(path, dry_run=False, overrides={}, note_only={})
    assert Customer.query.count() == 2
    assert sorted(result.customers_created) == ["Dafne Gato", "Otro Cliente"]


def test_dry_run_writes_nothing(app, segment, tmp_path):
    path = _xlsx(tmp_path, [
        _row(datetime(2025, 6, 4), "Claudio Milla", {"J": 5}, 1680, 8400, "no", 8400),
    ])
    result = import_ventas(path, dry_run=True, overrides={}, note_only={})
    assert result.sales == 1
    assert Sale.query.count() == 0
    assert Customer.query.count() == 0
    assert Product.query.count() == 0


def test_real_run_refuses_when_sales_exist(app, segment, tmp_path):
    db.session.add(Customer(name="X", segment_id=segment.id))
    db.session.flush()
    db.session.add(Sale(customer_id=Customer.query.first().id, sale_date=datetime(2025, 1, 1),
                        total_amount=0))
    db.session.commit()
    path = _xlsx(tmp_path, [
        _row(datetime(2025, 6, 4), "Y", {"J": 1}, 1000, 1000, "no", 1000),
    ])
    with pytest.raises(MiniErpError, match="reset-data"):
        import_ventas(path, dry_run=False, overrides={}, note_only={})


def test_report_has_totals_and_reconciliation(app, segment, tmp_path):
    path = _xlsx(tmp_path, [
        _row(datetime(2025, 6, 4), "A", {"J": 5}, 1000, 5000, "no", 5000,
             fecha_pago=datetime(2025, 6, 4)),
        _row(datetime(2025, 6, 5), "B", {"M": 2, "O": 3}, 1000, 5000, "sí", 5950),
    ])
    result = import_ventas(path, dry_run=True, overrides={}, note_only={})
    report = build_report(result)
    assert "# Log de migración" in report
    assert "SIMULACIÓN" in report
    assert "Ventas cargadas | 2" in report
    assert "Botellas | 10" in report
    assert "Ventas con IVA (facturas) | 1" in report
    assert "Reconciliación con la planilla" in report
