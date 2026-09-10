# Plan de migración — carga de datos reales de Scoby a producción

> Estado (2026-09-10): **decisiones cerradas con Scoby, herramienta lista**.
> Falta el conteo de inventario (#119) y la ejecución en producción (#120).
> `flask reset-data` (#116) y `flask import-ventas` (#118) ya están desplegados.
> Épica: [#121](https://github.com/luisurcia/mini_erp/issues/121).

## 1. Fuente

`datos a migrar/Migrar.xlsm` — hoja única **`Ventas`**, **1026 filas de datos**
(fila 1 = encabezados), ventas del **2025-06-04 al 2026-09-09**.

**Congelada:** fecha de corte **2026-09-09** (última fila de la planilla). Desde
el corte no se edita más; las ventas del 10-09 en adelante se ingresan a mano en
el ERP (§6, paso 9). El importador acepta el `.xlsm` directo (no hace falta
exportar a `.xlsx`).

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
- `Sale.notes` = col S; para las filas con corrección (§4) se agrega una nota `[Migración] …`
- `Sale.tax_applied` = `True` si `con iva?` empieza con "s" (`si` / `sí` / `Sí`),
  salvo las filas con `force_no_tax` en §4 (rows 2 / 275 / 384 → sin IVA).
- `Sale.tax_rate_applied` = `19` si `tax_applied`, si no `null`.
- `Sale.tax_amount` = `Sale.total_amount − subtotal` (subtotal = Σ líneas).
  Absorbe las ~20 filas con la col `Iva` errónea y deja 0 en las filas sin IVA.
- `Sale.total_amount` = col Q (`total pago`) redondeada a peso, **salvo** las
  filas con `total_amount` fijo en §4 (rows 2 / 224 / 566 / 815 / 871).
- `Sale.payment_status` / `paid_at` / `payment_reference`:
  - col R presente → `paid`, `paid_at` = col R **tal cual** (sin corregir las
    23 fechas previas a la venta), `payment_reference` = `"Migración planilla"`
  - col R ausente → `unpaid`
- Una `SaleItem` por cada columna D–K con valor > 0:
  - `product_id` → producto por nombre corto
  - `quantity` = valor de la celda
  - `unit_price` = col L (`valor unitario`) **redondeada a peso**, igual para todas las líneas de la venta
  - `warehouse_id` = **null** (línea histórica, sin bodega — igual que las líneas previas a #24)

`Sale.subtotal_amount` es una propiedad calculada (Σ `unit_price × quantity`);
para 4 filas (22, 195, 815, 871) no cuadra con el `total_amount` — diferencia
menor, solo visible en el detalle de la venta, no en los agregados (que usan
`total_amount`). El log del import las lista como advertencia.

### 3.2 Clientes

- `name` = col B **normalizada** (trim + colapsar espacios: `"Dafne  Gato"` → `"Dafne Gato"`)
- Dedup **case-insensitive** tras normalizar → **308 nombres en la planilla → 295 clientes**
  (13 se fusionan por diferencias de mayúsculas/espacios). Los casi-duplicados por
  typo (`Gonzales`/`Gonzalez`, `Prisila`/`Prisilla`) quedan separados; Scoby los
  fusiona a mano después.
- `segment_id` = segmento **"Otros"** para todos. RUT / email / teléfono /
  dirección / IG quedan vacíos (Scoby los completa con el tiempo).
- La lista de los 295 clientes va en el log del import para revisión de Scoby.

### 3.3 Productos — 8

Creación directa: `name`, `short_name`, `is_active = True`. SKU derivado
(`product_sku_enabled = 0`). Sin sabor, precio, tamaño.

### 3.4 Inventario inicial — **se carga DESPUÉS de las ventas** (#119)

La planilla no tiene stock, y **la carga de ventas no toca el inventario** (§3.1):
inserta `Sale` / `SaleItem` sin `StockMovement`. Entonces el orden es:

1. `flask reset-data` deja el inventario **vacío** (= 0 en todas las bodegas;
   un producto sin `InventoryItem` se trata como stock 0).
2. `flask import-ventas` carga las 1.026 ventas — el stock sigue en 0.
3. Scoby entrega el **conteo físico de existencias por producto** (a la fecha de
   corte) y se carga como saldo inicial: reposición a Bodega de Fermentación /
   traspaso, o ajuste directo por `(producto, bodega)`. Pocas celdas (8 productos
   × 1–3 bodegas) → alcanza con la UI.

**Por qué las históricas no consumen stock:** esas ventas ya ocurrieron y su
efecto ya está reflejado en el conteo físico de hoy. Si además se descontara el
stock por las 1.026 ventas, se restaría dos veces y el inventario quedaría muy
negativo. El conteo físico **es** el saldo de partida.

**Ventana sin poder vender:** entre el paso 2 y el paso 3, el equipo no puede
registrar ventas nuevas en el ERP (el sistema bloquea vender sin stock). Por eso
el conteo de inventario se carga **el mismo día, justo después** del import,
antes de que empiecen a operar. Scoby debe indicar **a qué bodega** va el stock
(probablemente Principal) y, si lo tienen, el **nivel de reposición** por
producto (para el panel de stock bajo).

## 4. Decisiones (cerradas con Scoby el 2026-09-10)

Implementadas en `ROW_OVERRIDES` / `NOTE_ONLY_ROWS` de `app/migration.py`.

**Generales:**

| Tema | Decisión |
|---|---|
| "Mario" / "Julien" / "Jota" como clientes (98 filas) | Se migran como **clientes normales**, sin marca ni exclusión. |
| Segmento de los ~295 clientes | Todos a **"Otros"**; Scoby reclasifica después. |
| Fecha de corte | **2026-09-09**. El `Migrar.xlsm` actual (última fila 09-09) ya es el definitivo. |
| Referencia de pago | `"Migración planilla"` + `paid_at` de la planilla. |
| Fechas de pago anteriores a la venta (23) | Se importan **tal cual**, sin ajustar. |

**Filas puntuales:**

| Fila(s) | Cliente | Decisión |
|---|---|---|
| 2 | Claudio Milla | `con iva? = "una parte"` → **sin IVA**, `total_amount = $30.240` (el neto). |
| 224 | Mario | 16 unidades (de las columnas de sabor), `total_amount = $16.000`. |
| 887 | Julien | 30 unidades (de las columnas de sabor); se ignora `cantidad = 40`. |
| 22, 34, 35 | Mama amparo / Liliana Lopez / Maria Jesus Allende | Precio unitario **redondeado a peso** (regla que además aplica a todas las filas). |
| 566, 815, 871 | Pedro Philippi / Mariel Saez / Pedro Philippi | Las tres al **neto $30.000, sin IVA**. La diferencia de $5.000 de la 871 es por despacho. |
| 275, 384 | Mauricio Celda / Mario | Marcadas `con iva? = "sí"` sin IVA cobrado → **sin IVA** (no cuentan como factura). |

## 5. Herramienta — `flask import-ventas` (#118, commit `cccbe0d`, desplegado)

```
flask import-ventas <archivo.xlsx|xlsm> [--dry-run]
```

- Lee la hoja `Ventas` con **`openpyxl`** (dependencia agregada, ya instalada en
  producción). Acepta `.xlsm` y `.xlsx`.
- **`--dry-run`** (correr **siempre primero**): recorre todo, arma el log y hace
  rollback — no escribe nada.
- **Guarda:** el import real aborta si la tabla `sales` no está vacía. Se corre
  una sola vez, sobre la BD recién reseteada con `flask reset-data`.
- **Log** en markdown, guardado en `instance/migracion-ventas-<timestamp>-<modo>.md`
  y también impreso: resumen, **reconciliación vs los totales crudos de la
  planilla**, ventas por mes, botellas por producto, las 11 filas con
  tratamiento especial, advertencias (fechas de pago previas, subtotal≠total) y
  la lista de clientes creados.

**Resultado del dry-run contra `Migrar.xlsm` (SHA-256 `bd8b02f0…`):**

| Métrica | Planilla (cruda) | Cargado |
|---|---|---|
| Ventas | 1.026 | **1.026** |
| Líneas de venta | — | 3.443 |
| Clientes | 308 nombres | **295** |
| Σ total | $47.441.444 | **$47.436.854** (Δ −$4.590 por las correcciones de §4) |
| Botellas | 28.732 | **28.732** |
| Facturas | 497 | **495** (−2 por filas 275/384) |
| Pagadas / por pagar | 970 / 56 | **970 / 56** |
| Filas omitidas | — | 0 |

## 6. Secuencia de ejecución en producción (#120)

1. Scoby entrega el conteo físico de inventario (#119) e indica a qué bodega va.
2. **Backup manual** de la BD de producción (además del que hace el pipeline).
3. `flask reset-data` → borra los datos de prueba, deja usuarios + configuración,
   re-siembra bodegas / segmentos / categorías. Inventario queda en 0.
4. Verificar `Company` (IVA 19%, CLP 0 decimales, sabor/precio/SKU/tamaño ocultos,
   nombre corto activo) y que estén las 4 bodegas + segmento "Otros".
5. `flask import-ventas "Migrar.xlsm" --dry-run` → revisar el log (cuadrar con la
   tabla de §5).
6. `flask import-ventas "Migrar.xlsm"` → carga real. **El stock sigue en 0.**
7. **Cargar el conteo de inventario** (§3.4), el **mismo día**, antes de que el
   equipo empiece a operar.
8. **Reconciliación:** log del import vs §5; abrir el Dashboard y contrastar con
   el Excel de Scoby (Valor Total Pago, botellas, facturas, por mes); spot-check
   de 5–10 ventas en la UI (la de "sin IVA / una parte" = Claudio Milla, una
   multi-producto, una por pagar, una de Mario/Julien, la de precio con
   decimales); probar la lista de Ventas, el PDF de por pagar y un ticket de
   despacho.
9. **Ventana de transición:** cargar a mano en el ERP las ventas hechas entre el
   corte (2026-09-09) y este punto. Desde acá, Scoby opera solo en el ERP; la
   planilla queda archivada como respaldo.

### Rollback

Si la reconciliación falla feo: restaurar el backup del paso 2. El import es
todo-o-nada (aborta si `sales` no está vacía), no hay medias cargas.

## 7. Fuera de alcance

- Recetas de insumos (la planilla no las tiene) — los productos quedan sin
  receta; pendiente ya conocido.
- Movimientos de stock históricos / trazabilidad de inventario previa al corte.
- Importar compras (`Purchase`) — la planilla es solo de ventas.
- Corregir la contabilidad de las filas inconsistentes más allá de lo que decida
  Scoby en §4.
