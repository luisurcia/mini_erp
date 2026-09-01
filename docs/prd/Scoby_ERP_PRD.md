# Documento de producto · PRD

**Scoby ERP** — rama `client/scoby`

> PRD por **ingeniería inversa**: describe lo que la rama `client/scoby` efectivamente hace hoy, reconstruido a partir del código y de lo desplegado en producción (`https://titourcia.com/scobyerp`). Reemplaza como referencia viva a los documentos genéricos `Kombucha_ERP_PRD.md` / `Kombucha_ERP_PRD_Requerimientos.md`, que quedan solo como registro histórico de la evaluación inicial (25 ago 2026).
>
> El seguimiento del trabajo se hizo en GitHub Issues: épica [#20](https://github.com/luisurcia/mini_erp/issues/20) (personalización base, 15 sub-issues), épica [#36](https://github.com/luisurcia/mini_erp/issues/36) (segunda ronda, 8 sub-issues), épica [#47](https://github.com/luisurcia/mini_erp/issues/47) (tercera ronda, 4 sub-issues) y épica [#76](https://github.com/luisurcia/mini_erp/issues/76) (cuarta ronda, 6 sub-issues: ajustes de UX y reorganización del menú) — todas cerradas.

| FECHA | ESTADO | BASE | ORIGEN |
|---|---|---|---|
| 31 agosto 2026 | En producción | Rama `client/scoby` (commit `8bac182`) | Ingeniería inversa del código |

---

## 01 Resumen

Scoby ERP es la personalización de Kombucha ERP para **Scoby Kombucha**. Sobre el sistema genérico se rehízo la operación completa de stock y ventas para que calce con cómo trabaja Scoby: **una bodega de insumos y varias de distribución**, **precio libre por venta** (no un precio de catálogo fijo), **insumos que se descuentan solos según la receta de cada producto**, **cobranza** (por pagar / pagado con referencia de transferencia), clientes con **RUT y dirección de despacho estructurada**, y **roles por función** (administrador, bodeguero, vendedor). La interfaz está con la identidad visual de Scoby y cada persona la usa en su idioma (español, inglés o francés).

Corre en producción con datos reales, en su propio ambiente (independiente del de Kombucha ERP genérico).

## 02 Para quién está pensado

El equipo de Scoby Kombucha: producción/bodega, ventas y administración. Reemplaza el manejo por planillas y mensajería de: qué hay en cada bodega, qué insumos quedan, qué se vendió, qué está cobrado y quién le compra más.

## 03 Módulos

### MOD-01 · Productos — *catálogo*

El mantenedor del producto terminado, separado del stock (el stock vive en Inventario). Es **mantención poco frecuente**: se llega desde el menú **Configuración** del navbar y **solo el administrador** tiene acceso (bodeguero y vendedor no lo necesitan — el selector de productos de la venta funciona igual sin ese permiso).

- Campos: **sabor**, **nombre**, **nombre corto** (para columnas angostas), **SKU** único, **tamaño (ml)**, **precio unitario**, activo/inactivo.
- Casi todos los campos son **opcionales de mostrar**: desde Empresa se puede apagar Sabor, Nombre corto, Tamaño, SKU y Precio. Scoby dobla el sabor dentro del nombre y no usa precio de catálogo (lo pone por venta), así que esos campos pueden ir ocultos.
- Al ocultar un campo, el formulario deja de pedirlo y el sistema lo deriva solo (p. ej. genera un SKU).
- Los productos se **desactivan**, no se borran (siguen referenciados por ventas históricas).
- Un producto nace con stock 0 en todas las bodegas hasta que alguien lo reponga.

### MOD-02 · Inventario — *stock multi-bodega*

- **Varias bodegas de distribución** (hoy: Bodega Julien, Bodega Mario, Bodega Principal) + **una bodega de insumos** (ver MOD-03). El tipo de bodega es fijo.
- El stock se lleva por **(producto × bodega)**: una matriz con productos en las filas y bodegas de distribución en las columnas.
- Por celda: **reposición** de stock y **nivel de reposición** editable. El stock igual o menor al nivel se **resalta** en la pantalla.
- **Traspaso de stock entre bodegas de distribución**: al elegir producto + bodega origen + bodega destino, la pantalla muestra el **stock actual** de cada una (en rojo si la cantidad ingresada supera lo disponible en el origen). Valida stock suficiente y que origen ≠ destino.
- **Gestión de bodegas** (alta / renombrar / activar-desactivar): solo administrador, desde el menú **Configuración** del navbar.
- **Historial de movimientos** por producto: reposición, venta, ajuste, traspaso — cada uno con fecha, bodega, cantidad y nota.
- El sistema **no deja vender más producto del que hay** en la bodega elegida.

### MOD-03 · Insumos — *botellas, etiquetas, tapas + consumo por venta*

- Mantenedor de insumos: nombre, unidad, precio unitario, activo/inactivo.
- **Todo el stock de insumos vive en una única "Bodega de Insumos"** (no se puede desactivar). Pantalla de stock con reposición por celda, nivel de reposición y resaltado de bajo stock, igual que Inventario pero de una sola columna.
- **Insumos por producto (receta):** en `Insumos → Insumos por producto` se define, por producto, cuántas unidades de cada insumo consume por unidad vendida. Un producto sin receta no descuenta nada. Un insumo desactivado que ya está en una receta se sigue descontando. Editar recetas es **solo administrador** (es configuración de dato maestro, igual que el catálogo de productos); el bodeguero sí administra el catálogo de insumos y su stock.
- **Consumo automático en la venta:** al guardar una venta, por cada línea se busca la receta del producto, se suma por insumo entre todas las líneas y se descuenta de la Bodega de Insumos. Queda registrado como movimiento de insumo asociado a esa venta.
- El consumo de insumos **nunca bloquea la venta**: si un insumo queda en negativo, la venta se registra igual y aparece un **aviso** con la lista de faltantes (además del resaltado de bajo stock en la pantalla de insumos).

### MOD-04 · Ventas — *grilla bodega × producto, precio libre, IVA, cobranza*

- **Ingreso en grilla:** filas = bodegas de distribución, columnas = productos. Se ingresa la cantidad por celda, así una misma venta puede sacar el mismo producto de más de una bodega (se guarda como líneas separadas).
- **Una fila de precio unitario por producto**, libre — el precio de venta lo pone el vendedor (varía por cliente/cantidad, no por bodega). Escribir el precio en la primera columna lo copia al resto de la fila.
- **Fecha de venta editable** (por defecto hoy), **N° de factura** opcional. No se pide estado ni notas al ingresar (la venta ya ocurrió → se crea como completada).
- **IVA opcional** por venta, con la tasa configurada en Empresa. El total y el IVA se **previsualizan en vivo** mientras se ingresa. El IVA se redondea a la unidad de la moneda (0 decimales para CLP).
- Al guardar: **descuenta el stock de producto** de cada bodega y **descuenta los insumos** según receta.
- **Estado de pago:** cada venta es *por pagar* o *pagada* (eje aparte del estado de despacho). En la lista de Ventas hay columna de pago y filtro (Todas / Por pagar / Pagado). En el detalle de la venta:
  - Si está por pagar: formulario "Registrar pago" con **número de transferencia/referencia obligatorio** + fecha.
  - Si está pagada: se muestra la referencia y la fecha de pago, y **solo el administrador** puede revertir el pago.
  - Registrar un pago lo puede hacer un vendedor o un administrador; revertirlo, solo administrador.

### MOD-05 · Clientes — *RUT, dirección de despacho, segmentación*

- Campos: **nombre**, **sobrenombre**, **RUT** (único), **segmento**, email, teléfono, **usuario de Instagram**, **dirección de despacho estructurada** (calle, número, ciudad, comuna, región), notas.
- **Datos mínimos para crear un cliente: nombre + segmento.** El resto es opcional, incluido el RUT (no todo cliente se factura; se puede completar después). Los campos obligatorios se marcan con **asterisco rojo** y una leyenda; el selector de segmento arranca en "— Selecciona un segmento —" para que sea una elección consciente.
- La dirección se muestra compuesta en una línea; comuna/región son texto libre (sin catálogo oficial por ahora).
- **Segmentos de cliente** (Persona natural / Comercio / Distribuidor / Otros): catálogo simple administrado desde Empresa. Los segmentos se **desactivan**, no se borran; al editar un cliente, su segmento actual sigue seleccionable aunque esté inactivo.

### MOD-06 · Top clientes — *reemplazó a Oportunidades*

- El módulo de Oportunidades del sistema genérico **se eliminó** en `client/scoby`. En su lugar: ranking de los **10 clientes por consumo** (monto total, botellas, número de ventas, fecha de última compra).
- Filtros: **año + mes**, o **"Todo el tiempo"**; y **filtro por segmento** (independiente del filtro de fecha).

### MOD-07 · Dashboard — *KPIs de Scoby*

- Filtros de **año y mes** arriba de la página. Por defecto: año más reciente con ventas, **todos los meses**.
- 3 indicadores: **venta neta**, **venta promedio**, **botellas promedio por venta** — todos del periodo filtrado.
- Gráficos: participación de ventas por producto (torta, del periodo); ventas por mes y botellas vendidas por mes (barras, del año completo).
- Listado de **productos con stock bajo**.

### MOD-08 · Usuarios y roles — *acceso por función y por módulo*

- Tres roles: **Administrador**, **Bodeguero**, **Vendedor** (reemplazaron a Administrador/Editor/Lector).
  - **Bodeguero:** Inventario, Insumos (stock).
  - **Vendedor:** Ventas, Top clientes, Clientes.
  - **Administrador:** todo, más el **catálogo de productos**, las **recetas de insumos**, la **gestión de bodegas**, Usuarios y Empresa — todo lo que es dato maestro / mantención poco frecuente, agrupado en el menú **Configuración**.
- El acceso se aplica **de verdad**: un rol sin un módulo recibe error 403 si entra por URL directa, no solo se le oculta el menú.
- El catálogo de productos es **solo administrador** porque es dato maestro (se toca pocas veces, y un cambio se propaga a inventario, ventas, recetas y reportes). El vendedor no lo necesita: el selector de productos de la venta no depende de ese permiso.
- El usuario tiene **nombre y apellido** (se muestran en vez del `usuario` de login) e **idioma propio**.
- Cada persona cambia su propia contraseña y su propio idioma.

### MOD-09 · Empresa — *configuración global*

Solo administrador, desde el menú **Configuración** del navbar.

- **IVA:** tasa configurable (hoy 19%) y si aplica por defecto en ventas nuevas.
- **Moneda:** código, símbolo y **cantidad de decimales** (por defecto CLP / `$` / **0 decimales** — sin centavos en toda la app). Todos los montos se formatean con esta configuración y el redondeo del IVA la respeta.
- **Campos del producto:** los toggles de mostrar/ocultar Sabor, Nombre corto, Tamaño, SKU, Precio.
- **Idioma por defecto de la empresa** (lo hereda quien no eligió idioma propio).
- **Segmentos de cliente:** alta / renombrar / activar-desactivar.

### Transversal

- **Navegación:** el navbar muestra los módulos operativos (Dashboard, Inventario, Insumos, Ventas, Top clientes, Clientes) y dos menús desplegables:
  - **Configuración** (solo administrador): Productos, Gestionar bodegas, Usuarios, Empresa — las secciones de mantención poco frecuente.
  - **Menú de cuenta** bajo el nombre y rol del usuario: Idioma, Cambiar contraseña, Cerrar sesión.
  - "Dashboard" se llama así en los tres idiomas también en español (antes "Panel").
- **Campos obligatorios:** en los formularios se marcan con **asterisco rojo** después de la etiqueta.
- **Idioma por usuario:** español, inglés o **francés**. El idioma propio del usuario gana sobre el de la empresa. Afecta la interfaz completa (menús, KPIs, gráficos, meses, mensajes), el formato de números y las etiquetas de código (roles, estados, motivos de movimiento). Los datos ingresados (nombres de segmentos, bodegas, productos, insumos, clientes) quedan como se escribieron.
- **Identidad visual Scoby:** nombre "Scoby ERP" en login/navbar/título, paleta corporativa (crema, tinta, rosa + acentos teal/mostaza/naranja), tema claro fijo.
- **Móvil:** la aplicación es responsive; los controles y el menú están ajustados para verse bien en celular (Android/iPhone).

## 04 Qué no incluye hoy

- ✕ **Facturación electrónica** — el N° de factura es texto libre, no se timbra ni se envía a ningún organismo.
- ✕ **Pagos en línea / pasarela** — el pago se registra a mano con su número de transferencia; no hay cobro integrado.
- ✕ **Notificaciones proactivas** (email / SMS / Slack) — el stock bajo o negativo de insumos y de producto se ve en pantalla (aviso al guardar la venta + resaltado), no llega un mensaje. → spike [#52](https://github.com/luisurcia/mini_erp/issues/52).
- ✕ **Órdenes de compra / proveedores** — la reposición de stock y de insumos es manual.
- ✕ **Anular / editar / devolver una venta** — no hay pantalla para eso; si se construyera, debería devolver también producto e insumos.
- ✕ **Precios por segmento / lista de precios** — el precio se ingresa a mano en cada venta.
- ✕ **Pagos parciales / abonos** — el estado de pago es binario (por pagar / pagado).
- ✕ **Lotes y vencimiento** — el stock se lleva por producto, no por lote ni fecha de embotellado.
- ✕ **Catálogos oficiales de comuna/región de Chile** — son texto libre.
- ✕ **Tienda online / catálogo público**, **app móvil nativa**, **multiempresa**.

## 05 Diferencias respecto del producto genérico (Kombucha ERP)

`main` sigue siendo el ERP genérico. En `client/scoby` se agregó/cambió:

| Área | Genérico | Scoby |
|---|---|---|
| Bodegas | Una sola, stock global | Varias de distribución + una de insumos |
| Precio de venta | Precio de catálogo del producto | Libre por línea de venta; catálogo opcional |
| Ingreso de venta | Lista de líneas producto+cantidad | Grilla bodega × producto |
| Insumos | No existía como consumo | Módulo Insumos + receta por producto + descuento automático en la venta |
| Cobranza | No existía | Estado por pagar / pagado + referencia |
| Pre-venta | Módulo Oportunidades (embudo) | Eliminado → vista Top 10 clientes por consumo |
| Cliente | Nombre, email, teléfono, IG, notas | + RUT, sobrenombre, segmento, dirección de despacho estructurada; mínimo para crear = nombre + segmento |
| Roles | admin / editor / lector | admin / bodeguero / vendedor, por módulo, con 403 real; catálogo de productos y recetas = solo admin |
| Menú | Todos los ítems sueltos en el navbar | Menú "Configuración" (mantención) + menú de cuenta bajo el nombre del usuario |
| Idioma | es / en, a nivel empresa | es / en / fr, por usuario |
| Moneda | Formato fijo con decimales | Configurable; CLP con 0 decimales por defecto |
| Marca | "Kombucha ERP" neutro | "Scoby ERP" + paleta corporativa |

## 06 Operación

- **Aplicación web** (Flask), sin app nativa. Se usa desde el navegador, también en celular.
- **Producción:** ambiente propio en el hosting cPanel compartido (`server120.web-hosting.com`, cuenta `titoeyzy`), independiente del de Kombucha ERP genérico.
  - URL: `https://titourcia.com/scobyerp`
  - Python 3.12, base de datos **SQLite** propia (`~/scobyerp/instance/mini_erp.db`).
  - **Despliegue automático** desde la rama `client/scoby` vía GitHub Actions (corre los tests, hace backup de la base, actualiza el código, aplica migraciones de esquema y reinicia la app). Ambiente de GitHub separado (`scoby-production`).
- **Migraciones:** el esquema se actualiza solo en cada deploy (`flask init-db` → `_upgrade_schema`); las cargas nuevas usan `flask seed-demo` (datos de demo).

## 07 Pendientes conocidos

- **Recetas de insumos en producción:** los productos existentes se migraron **sin receta**. Hasta que el equipo configure en `Insumos → Insumos por producto` qué insumos consume cada kombucha, las ventas en producción no descuentan insumos. El stock de insumos ya está consolidado en la Bodega de Insumos.
- **Datos de usuarios en producción:** los 4 usuarios existentes (admin, Mario, Eduardo, Julien) tienen nombre/apellido en blanco y quedaron todos con rol `admin`; conviene cargar sus nombres y reasignarles rol `bodeguero` / `venta` según corresponda. Al hacerlo, tener presente que `bodeguero` y `venta` ya **no** ven el catálogo de productos ni las recetas (pasaron a solo administrador).
- **Notificaciones** — ver spike [#52](https://github.com/luisurcia/mini_erp/issues/52).
- **Bug francés pendiente** de housekeeping en los catálogos de traducción (entradas obsoletas del módulo Oportunidades eliminado).

---

*Scoby ERP — PRD por ingeniería inversa · rama `client/scoby` · commit `8bac182` · 31 agosto 2026*
