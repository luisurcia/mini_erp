import csv

import pytest
from openpyxl import Workbook

from app.customer_contacts import (
    build_report,
    normalize_phone,
    normalize_rut,
    region_for_comuna,
    update_customer_contacts,
)
from app.extensions import db
from app.models.customer import Customer

EMPRESA_HEADER = [
    None, "Tipo de local", "Razón Social", "Nombre", "Rut", "Direccion",
    "REGION", "Comuna", "Teléfono", "Contacto",
]
PARTICULAR_HEADER = [None, "NOMBRE CLIENTE", "DIRECCIÓN", "COMUNA", "TELÉFONO"]


def _xlsx(tmp_path, empresa_rows, particular_rows):
    wb = Workbook()
    ws1 = wb.active
    ws1.title = "CLIENTE EMPRESA"
    for _ in range(3):
        ws1.append([None] * 10)
    ws1.append(EMPRESA_HEADER)
    for r in empresa_rows:
        ws1.append(r)

    ws2 = wb.create_sheet("CLIENTE PARTICULAR")
    ws2.append([None] * 5)
    ws2.append(PARTICULAR_HEADER)
    for r in particular_rows:
        ws2.append(r)

    path = tmp_path / "clientes.xlsx"
    wb.save(path)
    return str(path)


def _mapeo(tmp_path, rows):
    path = tmp_path / "mapeo.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["hoja", "nombre_excel", "customer_id"])
        w.writerows(rows)
    return str(path)


# --- normalización pura ---


def test_normalize_phone_already_correct():
    assert normalize_phone(56993239737) == ("+56993239737", None)


def test_normalize_phone_missing_country_code():
    assert normalize_phone(961731418) == ("+56961731418", None)


def test_normalize_phone_invalid_is_flagged():
    value, err = normalize_phone("12345")
    assert value is None
    assert "irreconocible" in err


def test_normalize_phone_blank():
    assert normalize_phone(None) == (None, None)
    assert normalize_phone("") == (None, None)


def test_normalize_rut_with_dash():
    assert normalize_rut("78.033.557- 2") == ("78.033.557-2", None)
    assert normalize_rut("77.296417-K") == ("77.296.417-K", None)


def test_normalize_rut_k_no_dash():
    assert normalize_rut("77578315k") == ("77.578.315-K", None)


def test_normalize_rut_ambiguous_no_separator_is_flagged():
    value, err = normalize_rut("77269286")
    assert value is None
    assert "irreconocible" in err


def test_region_for_comuna_accent_and_case_insensitive():
    assert region_for_comuna("peñalolen") == "Región Metropolitana"
    assert region_for_comuna("Peñalolén") == "Región Metropolitana"
    assert region_for_comuna("Quilpué (Los Pinos)") == "Valparaíso"
    assert region_for_comuna("comuna inexistente") is None


# --- comando completo ---


@pytest.fixture()
def empresa_customer(app):
    c = Customer(name="Casa Kutral")
    db.session.add(c)
    db.session.commit()
    return c


@pytest.fixture()
def particular_customer(app):
    c = Customer(name="Javier Cayulef")
    db.session.add(c)
    db.session.commit()
    return c


def test_fills_blank_fields_only(app, empresa_customer, particular_customer, tmp_path):
    xlsx = _xlsx(
        tmp_path,
        empresa_rows=[
            [None, "Cafetería", "Casa Kutral SPA", "Casa Kutral", "77.138.277-0",
             "Ruta F-30 s/n", "V", "Maitencillo", 56953571459, "Contacto X"],
        ],
        particular_rows=[
            [None, "Javier Cayulef", "Claudio Gay 1971", "Santiago", 56993239737],
        ],
    )
    mapeo = _mapeo(tmp_path, [
        ["CLIENTE EMPRESA", "Casa Kutral", empresa_customer.id],
        ["CLIENTE PARTICULAR", "Javier Cayulef", particular_customer.id],
    ])

    result = update_customer_contacts(xlsx, mapeo, dry_run=False)

    db.session.refresh(empresa_customer)
    assert empresa_customer.rut == "77.138.277-0"
    assert empresa_customer.shipping_street == "Ruta F-30 s/n"
    assert empresa_customer.shipping_commune == "Maitencillo"
    assert empresa_customer.shipping_region == "Valparaíso"
    assert empresa_customer.phone == "+56953571459"

    db.session.refresh(particular_customer)
    assert particular_customer.shipping_region == "Región Metropolitana"
    assert particular_customer.phone == "+56993239737"

    assert result.updated_customers == 2
    assert build_report(result)  # no debería tirar excepción
    assert "Casa Kutral" not in result.warnings  # no accidental warning noise


def test_does_not_overwrite_existing_value_without_force(app, empresa_customer, tmp_path):
    empresa_customer.phone = "+56900000000"
    db.session.commit()

    xlsx = _xlsx(
        tmp_path,
        empresa_rows=[
            [None, "Cafetería", "Casa Kutral SPA", "Casa Kutral", "77.138.277-0",
             "Ruta F-30 s/n", "V", "Maitencillo", 56953571459, None],
        ],
        particular_rows=[],
    )
    mapeo = _mapeo(tmp_path, [["CLIENTE EMPRESA", "Casa Kutral", empresa_customer.id]])

    update_customer_contacts(xlsx, mapeo, dry_run=False)
    db.session.refresh(empresa_customer)
    assert empresa_customer.phone == "+56900000000"
    assert empresa_customer.rut == "77.138.277-0"  # el resto de los campos, vacíos, sí se llenan


def test_force_overwrites(app, empresa_customer, tmp_path):
    empresa_customer.phone = "+56900000000"
    db.session.commit()

    xlsx = _xlsx(
        tmp_path,
        empresa_rows=[
            [None, "Cafetería", "Casa Kutral SPA", "Casa Kutral", "77.138.277-0",
             "Ruta F-30 s/n", "V", "Maitencillo", 56953571459, None],
        ],
        particular_rows=[],
    )
    mapeo = _mapeo(tmp_path, [["CLIENTE EMPRESA", "Casa Kutral", empresa_customer.id]])

    update_customer_contacts(xlsx, mapeo, dry_run=False, force=True)
    db.session.refresh(empresa_customer)
    assert empresa_customer.phone == "+56953571459"


def test_dry_run_writes_nothing(app, empresa_customer, tmp_path):
    xlsx = _xlsx(
        tmp_path,
        empresa_rows=[
            [None, "Cafetería", "Casa Kutral SPA", "Casa Kutral", "77.138.277-0",
             "Ruta F-30 s/n", "V", "Maitencillo", 56953571459, None],
        ],
        particular_rows=[],
    )
    mapeo = _mapeo(tmp_path, [["CLIENTE EMPRESA", "Casa Kutral", empresa_customer.id]])

    result = update_customer_contacts(xlsx, mapeo, dry_run=True)
    db.session.refresh(empresa_customer)
    assert empresa_customer.rut is None
    assert result.updated_customers == 1


def test_unmatched_name_is_skipped_and_reported(app, empresa_customer, tmp_path):
    xlsx = _xlsx(tmp_path, empresa_rows=[], particular_rows=[])
    mapeo = _mapeo(tmp_path, [["CLIENTE EMPRESA", "No Existe", empresa_customer.id]])

    result = update_customer_contacts(xlsx, mapeo, dry_run=False)
    assert result.updated_customers == 0
    assert len(result.skipped) == 1
    assert "no se encontró" in result.skipped[0][2]


def test_ambiguous_name_within_sheet_is_skipped(app, tmp_path):
    c1 = Customer(name="Roberto Providencia")
    db.session.add(c1)
    db.session.commit()

    xlsx = _xlsx(
        tmp_path,
        empresa_rows=[],
        particular_rows=[
            [None, "Roberto", "Eleodoro Yañez 1329", "Providencia", 56965950563],
            [None, "Roberto", "Otra Calle 123", "La Florida", 56971082391],
        ],
    )
    mapeo = _mapeo(tmp_path, [["CLIENTE PARTICULAR", "Roberto", c1.id]])

    result = update_customer_contacts(xlsx, mapeo, dry_run=False)
    assert result.updated_customers == 0
    assert "ambiguo" in result.skipped[0][2]


def test_unrecognized_comuna_leaves_region_blank_and_warns(app, particular_customer, tmp_path):
    xlsx = _xlsx(
        tmp_path,
        empresa_rows=[],
        particular_rows=[
            [None, "Javier Cayulef", "Alguna calle", "Comuna Desconocida", 56993239737]
        ],
    )
    mapeo = _mapeo(tmp_path, [["CLIENTE PARTICULAR", "Javier Cayulef", particular_customer.id]])

    result = update_customer_contacts(xlsx, mapeo, dry_run=False)
    db.session.refresh(particular_customer)
    assert particular_customer.shipping_region is None
    assert any("no está en la tabla" in w for w in result.warnings)


def test_rut_conflict_is_not_overwritten(app, empresa_customer, tmp_path):
    other = Customer(name="Otro Cliente", rut="77.138.277-0")
    db.session.add(other)
    db.session.commit()

    xlsx = _xlsx(
        tmp_path,
        empresa_rows=[
            [None, "Cafetería", "Casa Kutral SPA", "Casa Kutral", "77.138.277-0",
             None, None, None, None, None],
        ],
        particular_rows=[],
    )
    mapeo = _mapeo(tmp_path, [["CLIENTE EMPRESA", "Casa Kutral", empresa_customer.id]])

    result = update_customer_contacts(xlsx, mapeo, dry_run=False)
    db.session.refresh(empresa_customer)
    assert empresa_customer.rut is None
    assert any("ya está asignado" in w for w in result.warnings)


def test_region_cross_check_warns_on_mismatch(app, empresa_customer, tmp_path):
    xlsx = _xlsx(
        tmp_path,
        empresa_rows=[
            [None, "Cafetería", "Casa Kutral SPA", "Casa Kutral", None,
             None, "RM", "Maitencillo", None, None],
        ],
        particular_rows=[],
    )
    mapeo = _mapeo(tmp_path, [["CLIENTE EMPRESA", "Casa Kutral", empresa_customer.id]])

    result = update_customer_contacts(xlsx, mapeo, dry_run=False)
    db.session.refresh(empresa_customer)
    assert empresa_customer.shipping_region == "Región Metropolitana"
    assert any("no calza" in w for w in result.warnings)


def test_idempotent_second_run_changes_nothing(app, empresa_customer, tmp_path):
    xlsx = _xlsx(
        tmp_path,
        empresa_rows=[
            [None, "Cafetería", "Casa Kutral SPA", "Casa Kutral", "77.138.277-0",
             "Ruta F-30 s/n", "V", "Maitencillo", 56953571459, None],
        ],
        particular_rows=[],
    )
    mapeo = _mapeo(tmp_path, [["CLIENTE EMPRESA", "Casa Kutral", empresa_customer.id]])

    update_customer_contacts(xlsx, mapeo, dry_run=False)
    result2 = update_customer_contacts(xlsx, mapeo, dry_run=False)
    assert result2.updated_customers == 0
