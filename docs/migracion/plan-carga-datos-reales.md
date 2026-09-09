# Plan de migración — carga de datos reales de Scoby a producción

> Estado: **planificación** (2026-09-09). No implementado. Épica GitHub asociada:
> ver el issue enlazado. Requiere `flask reset-data` (#116) ejecutado antes.

## 1. Fuente

`datos a migrar/Migrar.xlsm` — hoja única **`Ventas`**, **1026 filas de datos**
(fila 1 = encabezados), ventas del **2025-06-04 al 2026-09-09**.

La planilla **sigue viva** (la última fila es de hoy). Antes de migrar hay que
**congelarla**: Scoby fija una fecha de corte, deja de editarla, y exporta un
`.xlsx` limpio (sin macros). Las ventas entre el corte y el go-live se ingresan
a mano en el ERP.

### Columnas

| Col | Nombre | Uso en la migración |
|---|---|---|
| A | `Fecha` | `Sale.sale_date` (fecha, hora 00:00) |
| B | `cliente` | Nombre del cliente (texto libre) → `Customer.name` |
| C | `cantidad` | Total de unidades. **Solo de control** — se ignora; el detalle real está en D–K (tiene 2 typos). |
| D–K | `P J M O C EL FM GB` | Unidades por producto → una `SaleItem` por columna con cantidad > 0 |
| L | `valor unitario` | Precio único de la venta → `SaleItem.unit_price` para **todas** las líneas de esa venta |
| M | `valor total Neto` | Neto de la venta (= Σ unidades × valor unitario, salvo redondeos) |
| N | `con iva?` | `si` / `sí` / `no` / `una parte` → `Sale.tax_applied` |
| O | `Iva` | Monto de IVA. **No confiable** (~20 filas con valores obsoletos/erróneos). Se recalcula como `total pago − neto`. |
| P | `N° Factura` | `Sale.invoice_number` (texto libre tal cual: `F 256`, `Boleta 2`, `252`, `B17034`) |
| Q | `total pago` | **Fuente de verdad del dinero** → `Sale.total_amount` |
| R | `Fecha de pago` | Presente → venta **pagada** (`paid_at`); ausente → **por pagar** |
| S | `Comentario` | `Sale.notes` (solo 10 filas la usan) |
| T, U | (sin nombre) | Vacías, se ignoran |

### Mapa de productos (sabor abreviado → nombre)

`Company.product_flavor_enabled = 0` y `product_price_enabled = 0` en producción,
`product_short_name_enabled = 1`. Los productos se crean con **nombre + nombre
corto**, sin sabor, sin precio de catálogo, sin SKU ni tamaño (el SKU se deriva).

| Corto | Nombre | Botellas en la planilla |
|---|---|---|
| `P` | Kombucha Pomelo | 3.730 |
| `J` | Kombucha Jengibre | 6.600 |
| `M` | Kombucha Maracuyá | 6.785 |
| `O` | Kombucha Original | 4.647 |
| `C` | Café | 879 |
| `EL` | Kombucha Edición Limitada | 1.308 |
| `FM` | Kombucha Frambuesa | 1.502 |
| `GB` | Ginger Beer | 3.281 |

## 2. Totales de control (para reconciliar post-carga)

| Métrica | Valor |
|---|---|
| Filas de venta | 1.026 |
| Σ `total pago` | **$47.441.444** (hay $0,4 de fracción por 3 filas con precio unitario decimal) |
| Σ `neto` | $42.662.616 |
| Σ IVA (`pago − neto`) | $4.778.828 |
| Botellas (Σ D–K) | **28.732** |
| Facturas (`con iva?` = si/sí) | 497 |
| Ventas pagadas / por pagar | 970 / **56** |
| Clientes distintos | **308** (182 con una sola compra) |

## 3. Modelo de la carga

### 3.1 Ventas — inserción directa por ORM, **sin tocar stock**

Las ventas históricas **no consumen inventario**: se insertan `Sale` +
`SaleItem` directo, **sin `StockMovement`**, sin llamar a
`SalesService.record_sale` ni a `Sale.recalculate_total()`. El stock real se
carga aparte (§3.4).

Por cada fila:

- `Sale.customer_id` → cliente (creado/buscado por nombre normalizado)
- `Sale.status = "completed"`
- `Sale.sale_date` = col A
- `Sale.invoice_number` = col P (texto, o null)
- `Sale.notes` = col S (o null); para la fila "una parte" se antepone `IVA parcial (planilla original)`
- `Sale.tax_applied`:
  - `no` → `False`
  - `si` / `sí` → `True`
  - `una parte` → `True` (1 fila, ver §4)
- `Sale.tax_rate_applied` = `19` si `tax_applied`, salvo "una parte" → `null`
- `Sale.tax_amount` = `total pago − neto` (col Q − col M). Maneja bien las ~20
  filas con la col `Iva` errónea, las 2 filas "IVA marcado pero no cobrado"
  (queda 0) y la fila "una parte" (queda 1.590).
- `Sale.total_amount` = col Q (`total pago`)
- `Sale.payment_status` / `paid_at` / `payment_reference`:
  - col R presente → `paid`, `paid_at` = col R, `payment_reference` = `"Migración planilla"` (o null — a confirmar)
  - col R ausente → `unpaid`
- Una `SaleItem` por cada columna D–K con valor > 0:
  - `product_id` → producto por nombre corto
  - `quantity` = valor de la celda
  - `unit_price` = col L (`valor unitario`), igual para todas las líneas de la venta
  - `warehouse_id` = **null** (línea histórica, sin bodega — igual que las líneas previas a #24)

`Sale.subtotal_amount` es una propiedad calculada (Σ `unit_price × quantity`);
para las filas donde eso no cuadra con el neto (2 filas, §4) hay una diferencia
menor que solo se ve en el detalle de la venta, no en los agregados (que usan
`total_amount`).

### 3.2 Clientes — 308

- `name` = col B **normalizada** (trim + colapsar espacios dobles: `"Dafne  Gato"` → `"Dafne Gato"`)
- Dedup **exacto** tras normalizar
- `segment_id` = segmento **"Otros"** por defecto (a confirmar — ver §4). El
  resto de los campos (RUT, email, teléfono, dirección, IG) quedan **vacíos**;
  Scoby los completa con el tiempo (mínimo del sistema para crear = nombre + segmento).
- La lista completa de 308 nombres se entrega a Scoby para revisión previa
  (posibles duplicados no exactos, nombres internos — ver §4).

### 3.3 Productos — 8

Creación directa: `name`, `short_name`, `is_active = True`. SKU derivado
(`product_sku_enabled = 0`). Sin sabor, precio, tamaño.

### 3.4 Inventario inicial — **dato aparte, lo entrega Scoby**

La planilla no tiene stock. Scoby debe entregar el **conteo real de existencias
por producto** al momento del corte. Se carga como reposición a la Bodega de
Fermentación o como ajuste directo por `(producto, bodega)`. Sub-issue propio;
bloquea el go-live pero no la carga de ventas.

## 4. Decisiones a confirmar con Scoby

| # | Tema | Filas | Propuesta |
|---|---|---|---|
| 1 | **"Mario" / "Julien" / "Jota" como clientes** — son también usuarios del ERP. 42 + 41 + 15 = 98 filas. ¿Ventas reales o consignación / traspaso a socios? | 98 | Si es consignación: decidir si se migran como cliente igual, se excluyen, o se marcan con un segmento aparte. Afectan los KPIs de venta. |
| 2 | **`con iva?` = "una parte"** (Claudio Milla, 2025-06-04): IVA parcial de $1.590 sobre neto $30.240. | 1 | `tax_applied = True`, `tax_amount = 1.590` exacto, `tax_rate_applied = null`, nota "IVA parcial". Cuenta como 1 factura en el Dashboard. |
| 3 | **Segmento de los 308 clientes** — sin dato. | 308 | Todos a **"Otros"**; Scoby reclasifica. (Alternativa: crear segmento "Sin clasificar".) |
| 4 | **`cantidad` ≠ Σ columnas de sabor** | 2 | **Mario 2025-09-30**: cols suman 16, `cantidad`/`neto` dicen 14 → decisión de Scoby (¿sobran 2 unidades en las columnas o falta ajustar el neto?). **Julien 2026-07-13**: cols suman 30, `neto` = 30.000 → usar **30**, ignorar `cantidad` = 40 (typo). |
| 5 | **`valor unitario` con decimales** (Mama amparo $2.158,33; Liliana Lopez y Maria Jesus Allende $1.466,4) | 3 | Importar con decimales tal cual (el neto es entero) o redondear el unitario. |
| 6 | **`con iva?` = "no" pero `total pago` ≠ `neto`** (Pedro Philippi ×2, Mariel Saez — diferencias de ±$5.000) | 3 | Parecen pagos adelantados / a cuenta. Decisión por fila: ¿`total_amount` = `total pago` (lo efectivamente movido) o = `neto`? |
| 7 | **`con iva?` = "sí" pero IVA $0** (Mauricio Celda $143.000; Mario $10.000) | 2 | Se importan con `tax_applied = True`, `tax_amount = 0`. ¿O corresponde `tax_applied = False`? |
| 8 | **`Fecha de pago` anterior a `Fecha`** | 23 | 22 son de 1 día (probable typo inocuo); Dafne Gato es de ~90 días. ¿Importar tal cual (fidelidad) o ajustar `paid_at = max(paid_at, sale_date)`? |
| 9 | **Referencia de pago** — la planilla no la tiene. | 970 | `payment_reference = "Migración planilla"` para todas las pagadas (o dejarla null). |
| 10 | **Fecha de corte** de la planilla y ventana de transición. | — | Scoby define; desde el corte no se toca más el Excel. |

## 5. Herramienta

Comando `flask import-ventas <archivo.xlsx> [--dry-run]`:

- Lee el `.xlsx` con **`openpyxl`** (nueva dependencia — precedente: `reportlab`
  en #81; instala como wheel en el hosting sin problema). Alternativa: Scoby
  exporta CSV y se usa `csv` de stdlib (más frágil con fechas/acentos).
- `--dry-run`: valida y reporta (filas OK, filas con inconsistencia, totales a
  reconciliar) **sin escribir**. Se corre primero, siempre.
- **Guardas:** aborta si la tabla `sales` no está vacía (se corre una sola vez,
  sobre la BD recién reseteada por `flask reset-data`).
- Las ~9 filas de §4 se resuelven con un pequeño archivo de correcciones
  (overrides por número de fila) o se corrigen en el `.xlsx` antes de exportar.
- Reporte final: filas insertadas, clientes creados, Σ `total_amount`, Σ
  botellas, N° de facturas, por pagar — para comparar 1:1 con §2.

## 6. Secuencia de ejecución en producción

1. Scoby congela la planilla (fecha de corte) y entrega el `.xlsx` + el conteo
   de inventario inicial.
2. Resolver las decisiones de §4; preparar el archivo de correcciones si hace falta.
3. Backup manual de la BD de producción (además del que hace el pipeline).
4. `flask reset-data` (deja solo usuarios + configuración).
5. Verificar configuración de `Company` (IVA 19%, CLP 0 decimales, toggles de
   producto) y que estén las bodegas / segmentos / categorías base.
6. `flask import-ventas archivo.xlsx --dry-run` → revisar el reporte.
7. `flask import-ventas archivo.xlsx` → carga real.
8. Cargar el inventario inicial.
9. **Reconciliación:** comparar los totales del reporte contra §2; abrir el
   Dashboard y contrastar con el Excel de Scoby (Valor Total Pago, botellas,
   facturas, por mes); spot-check de 5–10 ventas en la UI (incluida la de "IVA
   parcial" y alguna multi-producto).
10. Ventana de transición: las ventas hechas entre el corte y este punto se
    ingresan a mano en el ERP. Desde acá, Scoby opera solo en el ERP.

## 7. Fuera de alcance

- Recetas de insumos (la planilla no las tiene) — los productos quedan sin
  receta; pendiente ya conocido.
- Movimientos de stock históricos / trazabilidad de inventario previa al corte.
- Importar compras (`Purchase`) — la planilla es solo de ventas.
- Corregir la contabilidad de las filas inconsistentes más allá de lo que decida
  Scoby en §4.
