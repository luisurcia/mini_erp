"""One-shot import of Scoby's historical sales from the tracking
spreadsheet (`Migrar.xlsm` / `.xlsx`, sheet `Ventas`) into a freshly-reset
database. See `docs/migracion/plan-carga-datos-reales.md` and issues
#118 / #121.

Runs from the CLI: `flask import-ventas <archivo.xlsx> [--dry-run]`.
Kept out of any blueprint so it can be unit-tested on its own.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from openpyxl import load_workbook

from app.exceptions import MiniErpError
from app.extensions import db
from app.models.customer import Customer
from app.models.customer_segment import CustomerSegment
from app.models.product import Product
from app.models.sales import Sale, SaleItem

# Sabor abreviado (columnas D–K) -> nombre del producto.
PRODUCTS = {
    "P": "Kombucha Pomelo",
    "J": "Kombucha Jengibre",
    "M": "Kombucha Maracuyá",
    "O": "Kombucha Original",
    "C": "Kombucha Café",
    "EL": "Kombucha Edición Limitada",
    "FM": "Kombucha Frambuesa",
    "GB": "Ginger Beer",
}

# Índices de columna (0-based) en la hoja `Ventas`.
COL_FECHA = 0
COL_CLIENTE = 1
COL_FLAVORS = {3: "P", 4: "J", 5: "M", 6: "O", 7: "C", 8: "EL", 9: "FM", 10: "GB"}
COL_VALOR_UNITARIO = 11
COL_NETO = 12
COL_CON_IVA = 13
COL_NFACTURA = 15
COL_TOTAL_PAGO = 16
COL_FECHA_PAGO = 17
COL_COMENTARIO = 18

DEFAULT_SEGMENT = "Otros"
PAYMENT_REFERENCE = "Migración planilla"
TAX_RATE = Decimal("19")
_PESO = Decimal("1")

# Correcciones por fila, cerradas con Scoby el 2026-09-10 (ver el plan §4
# y el issue #117). La clave es el número de fila de la planilla
# (la fila 1 son los encabezados).
ROW_OVERRIDES: dict[int, dict] = {
    2: dict(
        force_no_tax=True,
        total_amount=Decimal("30240"),
        note=(
            "Planilla la marcaba 'con IVA = una parte'; se carga sin IVA "
            "por el neto $30.240 (decisión de Scoby)."
        ),
    ),
    224: dict(
        total_amount=Decimal("16000"),
        note=(
            "Cantidad tomada de las columnas de sabor (16 unidades); "
            "neto ajustado a $16.000 (planilla decía 14)."
        ),
    ),
    275: dict(
        force_no_tax=True,
        note="Marcada 'con IVA = sí' pero sin IVA cobrado; se carga sin IVA (decisión de Scoby).",
    ),
    384: dict(
        force_no_tax=True,
        note="Marcada 'con IVA = sí' pero sin IVA cobrado; se carga sin IVA (decisión de Scoby).",
    ),
    566: dict(
        total_amount=Decimal("30000"),
        force_no_tax=True,
        note="Neto $30.000; se pagaron $5.000 de más (adelanto).",
    ),
    815: dict(
        total_amount=Decimal("30000"),
        force_no_tax=True,
        note="Neto ajustado a $30.000 (decisión de Scoby).",
    ),
    871: dict(
        total_amount=Decimal("30000"),
        force_no_tax=True,
        note="Neto $30.000; la diferencia de $5.000 con la planilla es por despacho.",
    ),
}

# Filas que se cargan sin cambiar el resultado, pero conviene dejar
# registradas en el log.
NOTE_ONLY_ROWS: dict[int, str] = {
    887: "Cantidad tomada de las columnas de sabor (30 unidades); la planilla registraba 40.",
    22: "Precio unitario redondeado a peso entero (planilla: $2.158,33).",
    34: "Precio unitario redondeado a peso entero (planilla: $1.466,4).",
    35: "Precio unitario redondeado a peso entero (planilla: $1.466,4).",
}


def _norm_name(raw) -> str:
    return " ".join(str(raw).split())


def _norm_iva(raw) -> str:
    return str(raw).strip().lower() if raw is not None else ""


def _peso(value) -> Decimal:
    return Decimal(str(value if value is not None else 0)).quantize(
        _PESO, rounding=ROUND_HALF_UP
    )


@dataclass
class ImportResult:
    dry_run: bool
    source_name: str
    source_sha256: str
    sales: int = 0
    line_items: int = 0
    customers_created: list[str] = field(default_factory=list)
    products_created: list[str] = field(default_factory=list)
    total_amount: Decimal = Decimal("0")
    bottles: int = 0
    facturas: int = 0
    paid: int = 0
    unpaid: int = 0
    by_month: dict = field(default_factory=lambda: defaultdict(lambda: [0, Decimal("0"), 0]))
    bottles_by_product: dict = field(default_factory=lambda: defaultdict(int))
    # Cifras crudas de la planilla, sin aplicar correcciones.
    raw_total_pago: Decimal = Decimal("0")
    raw_bottles: int = 0
    raw_distinct_names: set = field(default_factory=set)
    special_rows: list[tuple[int, str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    skipped: list[tuple[int, str]] = field(default_factory=list)


def import_ventas(
    path: str,
    *,
    dry_run: bool,
    overrides: dict[int, dict] | None = None,
    note_only: dict[int, str] | None = None,
) -> ImportResult:
    """Carga las ventas de la planilla. Con `dry_run=True` recorre todo y
    arma el reporte, pero hace rollback al final (no escribe nada).

    `overrides` / `note_only` se pueden inyectar en las pruebas; por
    defecto son las correcciones acordadas con Scoby.
    """
    overrides = ROW_OVERRIDES if overrides is None else overrides
    note_only = NOTE_ONLY_ROWS if note_only is None else note_only
    raw = open(path, "rb").read()
    result = ImportResult(
        dry_run=dry_run,
        source_name=path.rsplit("/", 1)[-1],
        source_sha256=hashlib.sha256(raw).hexdigest(),
    )

    if not dry_run and Sale.query.first() is not None:
        raise MiniErpError(
            "La tabla de ventas no está vacía. Corré `flask reset-data` antes de importar."
        )

    segment = CustomerSegment.query.filter_by(name=DEFAULT_SEGMENT).first()
    if segment is None:
        raise MiniErpError(
            f"Falta el segmento '{DEFAULT_SEGMENT}'. Corré `flask reset-data` primero."
        )

    wb = load_workbook(path, data_only=True, read_only=True)
    ws = wb["Ventas"]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    products = _ensure_products(result)
    customers: dict[str, Customer] = {}

    try:
        for rownum, row in enumerate(rows[1:], start=2):
            if not any(v is not None for v in row[:19]):
                continue
            _import_row(
                rownum, row, products, customers, segment, result, overrides, note_only
            )

        if dry_run:
            db.session.rollback()
        else:
            db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return result


def _ensure_products(result: ImportResult) -> dict[str, Product]:
    out: dict[str, Product] = {}
    for code, name in PRODUCTS.items():
        product = Product.query.filter_by(short_name=code).first()
        if product is None:
            product = Product(
                name=name, short_name=code, sku=f"{code}-355", size_ml=355, is_active=True
            )
            db.session.add(product)
            db.session.flush()
            result.products_created.append(name)
        out[code] = product
    return out


def _get_customer(raw, customers, segment, result) -> Customer:
    name = _norm_name(raw)
    key = name.lower()
    if key not in customers:
        customer = Customer(name=name, segment_id=segment.id)
        db.session.add(customer)
        db.session.flush()
        customers[key] = customer
        result.customers_created.append(name)
    return customers[key]


def _import_row(
    rownum, row, products, customers, segment, result: ImportResult, overrides, note_only
) -> None:
    override = overrides.get(rownum, {})

    sale_date = row[COL_FECHA]
    if not isinstance(sale_date, datetime):
        result.skipped.append((rownum, "sin fecha de venta"))
        return
    if row[COL_CLIENTE] is None or not _norm_name(row[COL_CLIENTE]):
        result.skipped.append((rownum, "sin cliente"))
        return

    lines: list[tuple[Product, int]] = []
    for col, code in COL_FLAVORS.items():
        qty = row[col]
        if isinstance(qty, int | float) and qty > 0:
            lines.append((products[code], int(qty)))
    if not lines:
        result.skipped.append((rownum, "sin unidades en ninguna columna de sabor"))
        return

    unit_price = _peso(row[COL_VALOR_UNITARIO])
    if unit_price <= 0:
        result.skipped.append((rownum, "sin precio unitario"))
        return

    subtotal = sum((unit_price * qty for _p, qty in lines), start=Decimal("0"))
    bottles = sum(qty for _p, qty in lines)

    # La planilla usa "si" / "sí" / "Sí" / "no" / "una parte"; cualquier
    # cosa que empiece con "s" es con IVA.
    con_iva = _norm_iva(row[COL_CON_IVA])
    tax_applied = con_iva.startswith("s") and not override.get("force_no_tax")

    if "total_amount" in override:
        total_amount = override["total_amount"]
    else:
        total_amount = _peso(row[COL_TOTAL_PAGO])

    if tax_applied:
        tax_amount = total_amount - subtotal
        tax_rate_applied = TAX_RATE
        if tax_amount < 0:
            result.warnings.append(
                f"Fila {rownum}: IVA calculado negativo "
                f"(total {total_amount} < neto {subtotal}); se dejó en 0."
            )
            tax_amount = Decimal("0")
    else:
        tax_amount = Decimal("0")
        tax_rate_applied = None

    paid_at = row[COL_FECHA_PAGO] if isinstance(row[COL_FECHA_PAGO], datetime) else None
    if paid_at is not None and paid_at < sale_date:
        result.warnings.append(
            f"Fila {rownum}: fecha de pago ({paid_at.date()}) anterior "
            f"a la venta ({sale_date.date()}); se cargó tal cual."
        )

    note_parts = []
    if row[COL_COMENTARIO] is not None and str(row[COL_COMENTARIO]).strip():
        note_parts.append(str(row[COL_COMENTARIO]).strip())
    if override.get("note"):
        note_parts.append(f"[Migración] {override['note']}")
    notes = " · ".join(note_parts)[:255] or None

    invoice = row[COL_NFACTURA]
    invoice_number = str(invoice).strip()[:40] if invoice is not None else None

    sale = Sale(
        customer=_get_customer(row[COL_CLIENTE], customers, segment, result),
        status=Sale.STATUS_COMPLETED,
        sale_date=sale_date,
        invoice_number=invoice_number or None,
        notes=notes,
        tax_applied=tax_applied,
        tax_rate_applied=tax_rate_applied,
        tax_amount=tax_amount,
        total_amount=total_amount,
        payment_status=Sale.PAYMENT_PAID if paid_at else Sale.PAYMENT_UNPAID,
        payment_reference=PAYMENT_REFERENCE if paid_at else None,
        paid_at=paid_at,
    )
    for product, qty in lines:
        sale.items.append(
            SaleItem(product=product, quantity=qty, unit_price=unit_price, warehouse_id=None)
        )
    db.session.add(sale)

    if subtotal != total_amount and not tax_applied:
        result.warnings.append(
            f"Fila {rownum}: neto de las líneas (${subtotal:,.0f}) ≠ "
            f"total registrado (${total_amount:,.0f})."
        )

    # --- estadísticas ---
    result.sales += 1
    result.line_items += len(lines)
    result.total_amount += total_amount
    result.bottles += bottles
    result.facturas += 1 if tax_applied else 0
    if paid_at:
        result.paid += 1
    else:
        result.unpaid += 1
    ym = (sale_date.year, sale_date.month)
    result.by_month[ym][0] += 1
    result.by_month[ym][1] += total_amount
    result.by_month[ym][2] += bottles
    for product, qty in lines:
        result.bottles_by_product[product.short_name] += qty

    result.raw_total_pago += _peso(row[COL_TOTAL_PAGO])
    result.raw_bottles += bottles
    result.raw_distinct_names.add(str(row[COL_CLIENTE]).strip())

    if rownum in overrides:
        result.special_rows.append(
            (rownum, _norm_name(row[COL_CLIENTE]), overrides[rownum]["note"])
        )
    elif rownum in note_only:
        result.special_rows.append(
            (rownum, _norm_name(row[COL_CLIENTE]), note_only[rownum])
        )


def build_report(result: ImportResult, generated_at: datetime | None = None) -> str:
    generated_at = generated_at or datetime.now()
    mode = "SIMULACIÓN (dry-run, no se escribió nada)" if result.dry_run else "CARGA REAL"
    lines = [
        "# Log de migración — ventas de Scoby",
        "",
        f"- **Fecha de ejecución:** {generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **Modo:** {mode}",
        f"- **Archivo fuente:** `{result.source_name}`",
        f"- **SHA-256:** `{result.source_sha256}`",
        "",
        "## Resumen",
        "",
        "| Concepto | Valor |",
        "|---|---|",
        f"| Ventas cargadas | {result.sales:,} |",
        f"| Líneas de venta | {result.line_items:,} |",
        f"| Clientes creados | {len(result.customers_created):,} |",
        f"| Productos creados | {len(result.products_created)} |",
        f"| Suma total (con IVA) | ${result.total_amount:,.0f} |",
        f"| Botellas | {result.bottles:,} |",
        f"| Ventas con IVA (facturas) | {result.facturas:,} |",
        f"| Pagadas / por pagar | {result.paid:,} / {result.unpaid:,} |",
        "",
        "## Reconciliación con la planilla",
        "",
        "| Métrica | Planilla (cruda) | Cargado | Δ |",
        "|---|---|---|---|",
        f"| Suma ‘total pago’ | ${result.raw_total_pago:,.0f} | ${result.total_amount:,.0f} | "
        f"${result.total_amount - result.raw_total_pago:,.0f} |",
        f"| Botellas | {result.raw_bottles:,} | {result.bottles:,} | "
        f"{result.bottles - result.raw_bottles:+,} |",
        "",
        "La Δ de dinero corresponde a las correcciones acordadas con Scoby "
        "(filas sin IVA que antes sumaban IVA, y netos ajustados). Ver el detalle abajo.",
        "",
        "## Ventas por mes",
        "",
        "| Mes | Ventas | Total | Botellas |",
        "|---|---|---|---|",
    ]
    for (year, month), (count, total, bottles) in sorted(result.by_month.items()):
        lines.append(f"| {year}-{month:02d} | {count} | ${total:,.0f} | {bottles:,} |")

    lines += ["", "## Botellas por producto", "", "| Producto | Botellas |", "|---|---|"]
    for code, name in PRODUCTS.items():
        lines.append(f"| {name} ({code}) | {result.bottles_by_product.get(code, 0):,} |")

    lines += ["", "## Filas con tratamiento especial", ""]
    if result.special_rows:
        lines += ["| Fila | Cliente | Qué se hizo |", "|---|---|---|"]
        for rownum, cliente, note in sorted(result.special_rows):
            lines.append(f"| {rownum} | {cliente} | {note} |")
    else:
        lines.append("_Ninguna._")

    lines += ["", f"## Advertencias ({len(result.warnings)})", ""]
    lines += [f"- {w}" for w in result.warnings] or ["_Ninguna._"]

    lines += ["", f"## Filas omitidas ({len(result.skipped)})", ""]
    lines += [f"- Fila {rn}: {reason}" for rn, reason in result.skipped] or ["_Ninguna._"]

    merged = len(result.raw_distinct_names) - len(result.customers_created)
    if result.customers_created:
        lines += ["", f"## Clientes creados ({len(result.customers_created)})", ""]
        if merged > 0:
            lines.append(
                f"_{len(result.raw_distinct_names)} nombres distintos en la planilla → "
                f"{len(result.customers_created)} clientes ({merged} se consolidaron por "
                f"diferencias de mayúsculas o espacios). Los casi-duplicados por error de "
                f"tipeo (p. ej. 'Gonzales' / 'Gonzalez') quedan separados y Scoby los "
                f"fusiona a mano después._"
            )
            lines.append("")
        lines += [", ".join(sorted(result.customers_created))]

    lines.append("")
    return "\n".join(lines)
