# Documento de producto · PRD

**Scoby ERP** — rama `client/scoby`

> PRD por **ingeniería inversa**: describe lo que la rama `client/scoby` efectivamente hace hoy, reconstruido a partir del código y de lo desplegado en producción (`https://titourcia.com/scobyerp`). Reemplaza como referencia viva a los documentos genéricos `Kombucha_ERP_PRD.md` / `Kombucha_ERP_PRD_Requerimientos.md`, que quedan solo como registro histórico de la evaluación inicial (25 ago 2026).
>
> El seguimiento del trabajo se hizo en GitHub Issues: épicas [#20](https://github.com/luisurcia/mini_erp/issues/20) · [#36](https://github.com/luisurcia/mini_erp/issues/36) · [#47](https://github.com/luisurcia/mini_erp/issues/47) · [#76](https://github.com/luisurcia/mini_erp/issues/76) (personalización base + rondas de ajustes de UX), [#87](https://github.com/luisurcia/mini_erp/issues/87) (quinta ronda: PDF de cobranza, métricas de Dashboard, **flujo de bodegas Fermentación → Principal → distribución**), [#90](https://github.com/luisurcia/mini_erp/issues/90) (feedback: PDF agrupado por cliente, **consumo de insumos al armar**) y [#95](https://github.com/luisurcia/mini_erp/issues/95) (sexta ronda: **módulo de Compras**, columnas del grid de venta ordenadas por lo más vendido) — todas cerradas. Pendientes abiertos: spike de integración bancaria (#82), spike de notificaciones (#52) y modo comparación del Dashboard (#92).

| FECHA | ESTADO | BASE | ORIGEN |
|---|---|---|---|
| 2 septiembre 2026 | En producción | Rama `client/scoby` (commit `3a0693e`) | Ingeniería inversa del código |

---

## 01 Resumen

Scoby ERP es la personalización de Kombucha ERP para **Scoby Kombucha**. Sobre el sistema genérico se rehízo la operación completa de stock y ventas para que calce con cómo trabaja Scoby: un **flujo de bodegas** que sigue la producción real (**Fermentación → Principal → distribución**), una **bodega de insumos** aparte, **precio libre por venta** (no un precio de catálogo fijo), **insumos que se descuentan solos al armar la botella** (cuando entra a fermentación, según la receta de cada producto), **cobranza** (por pagar / pagado con referencia de transferencia), clientes con **RUT y dirección de despacho estructurada**, y **roles por función** (administrador, bodeguero, vendedor). La interfaz está con la identidad visual de Scoby y cada persona la usa en su idioma (español, inglés o francés).

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

### MOD-02 · Inventario — *stock multi-bodega con flujo de producción*

Las bodegas de producto terminado siguen el flujo real de Scoby:

```
producción → Bodega de Fermentación → Bodega Principal → Bodega Julien / Bodega Mario
```

- **Rol de cada bodega** (fijo, no editable):
  - **Bodega de Fermentación** — la botella recién armada (con su botella, etiqueta y tapa) entra acá y reposa. **Es la única donde se puede reponer stock.** Única.
  - **Bodega Principal** — recibe por traspaso desde Fermentación y distribuye hacia Julien / Mario. Única.
  - **Bodega Julien / Bodega Mario** (y futuras) — puntos de distribución. **No se les ingresa stock directo**: solo reciben por traspaso desde Principal.
  - (Además, una **Bodega de Insumos** aparte — ver MOD-03.)
- El stock se lleva por **(producto × bodega)**: una matriz con productos en las filas y las 4 bodegas en las columnas, en orden de flujo. El contenido de las celdas va centrado.
- **Reposición**: solo en la Bodega de Fermentación. En las demás, esa pantalla pasa a ser solo "nivel de reposición" (sin campo de cantidad) + un aviso de que reciben stock por traspaso. El stock igual o menor al nivel se **resalta**.
- **Traspasos permitidos** (validado en el sistema): **Fermentación → Principal** y **Principal → Julien / Mario**. Cualquier otra ruta se rechaza. El formulario acota las opciones de origen y destino según lo que se puede enviar/recibir, muestra el **stock actual** de cada bodega y valida stock suficiente.
- **Gestión de bodegas** (alta de bodegas de distribución / renombrar / activar-desactivar): solo administrador, desde el menú **Configuración**. Fermentación y Principal no se crean desde la UI (son únicas).
- **Historial de movimientos** por producto: reposición, venta, ajuste, traspaso, armado (consumo de insumos) — cada uno con fecha, bodega, cantidad y nota.
- El sistema **no deja vender más producto del que hay** en la bodega elegida.

### MOD-03 · Insumos — *botellas, etiquetas, tapas + consumo al armar*

- Mantenedor de insumos: nombre, unidad, precio unitario, activo/inactivo.
- **Todo el stock de insumos vive en una única "Bodega de Insumos"** (no se puede desactivar). Pantalla de stock con reposición por celda, nivel de reposición y resaltado de bajo stock, igual que Inventario pero de una sola columna.
- **Insumos por producto (receta):** en `Insumos → Insumos por producto` se define, por producto, cuántas unidades de cada insumo consume **por unidad armada**. Un producto sin receta no descuenta nada. Un insumo desactivado que ya está en una receta se sigue descontando. Editar recetas es **solo administrador** (es configuración de dato maestro, igual que el catálogo de productos); el bodeguero sí administra el catálogo de insumos y su stock.
- **Consumo automático al armar:** cuando entra stock de un producto a la **Bodega de Fermentación** (la reposición = el armado de la botella), se busca la receta y se descuenta de la Bodega de Insumos la botella + etiqueta + tapa por cada unidad ingresada. Queda registrado como movimiento de insumo de tipo *armado*. **La venta ya no toca los insumos** — la botella terminada que se vende ya los lleva.
- El consumo **nunca bloquea la reposición**: si un insumo queda en negativo, el stock entra igual y en la pantalla de reposición aparece un **aviso** con la lista de faltantes (además del resaltado de bajo stock en la pantalla de insumos).

### MOD-04 · Ventas — *grilla bodega × producto, precio libre, IVA, cobranza*

- **Ingreso en grilla:** filas = bodegas donde se vende (**Principal + Julien + Mario**, no Fermentación), columnas = productos. Se ingresa la cantidad por celda, así una misma venta puede sacar el mismo producto de más de una bodega (se guarda como líneas separadas).
- **Las columnas de producto se ordenan por lo más vendido** en los últimos 90 días (más unidades = más a la izquierda); las que no tuvieron ventas en ese periodo quedan al final en orden alfabético. Así el producto más habitual queda a mano sin scroll.
- **Una fila de precio unitario por producto**, libre — el precio de venta lo pone el vendedor (varía por cliente/cantidad, no por bodega). Escribir el precio en la primera columna (la del más vendido) lo copia al resto de la fila.
- **Fecha de venta editable** (por defecto hoy), **N° de factura** opcional. No se pide estado ni notas al ingresar (la venta ya ocurrió → se crea como completada).
- **IVA opcional** por venta, con la tasa configurada en Empresa. El total y el IVA se **previsualizan en vivo** mientras se ingresa. El IVA se redondea a la unidad de la moneda (0 decimales para CLP).
- Al guardar: **descuenta el stock de producto** de cada bodega elegida. **No toca los insumos** (eso ocurre al armar — ver MOD-03).
- **Lista de Ventas:** # · fecha · cliente · N° factura · estado · pago · **IVA (Sí/No)** · total. Filtro por estado de pago (Todas / Por pagar / Pagado) y botón **"Descargar PDF de ventas por pagar"** — un PDF agrupado por cliente (ventas más antiguas arriba, subtotal por cliente y total a cobrar) que se comparte semanalmente con los socios para la cobranza.
- **Estado de pago:** cada venta es *por pagar* o *pagada* (eje aparte del estado de despacho). En el detalle de la venta:
  - Si está por pagar: formulario "Registrar pago" con **número de transferencia/referencia obligatorio** + fecha.
  - Si está pagada: se muestra la referencia y la fecha de pago, y **solo el administrador** puede revertir el pago.
  - Registrar un pago lo puede hacer un vendedor o un administrador; revertirlo, solo administrador.

### MOD-05 · Clientes — *RUT, dirección de despacho, segmentación*

- Campos: **nombre**, **sobrenombre**, **RUT** (único), **segmento**, email, teléfono, **usuario de Instagram**, **dirección de despacho estructurada** (calle, número, ciudad, comuna, región), notas.
- **Datos mínimos para crear un cliente: nombre + segmento.** El resto es opcional, incluido el RUT (no todo cliente se factura; se puede completar después). Los campos obligatorios se marcan con **asterisco rojo** y una leyenda; el selector de segmento arranca en "— Selecciona un segmento —" para que sea una elección consciente.
- La dirección se muestra compuesta en una línea; comuna/región son texto libre (sin catálogo oficial por ahora).
- La **lista de Clientes** muestra solo Nombre, Segmento y RUT; el detalle completo se ve al editar.
- **Segmentos de cliente** (Persona natural / Comercio / Distribuidor / Otros): catálogo simple administrado desde Empresa. Los segmentos se **desactivan**, no se borran; al editar un cliente, su segmento actual sigue seleccionable aunque esté inactivo.

### MOD-06 · Top clientes — *reemplazó a Oportunidades*

- El módulo de Oportunidades del sistema genérico **se eliminó** en `client/scoby`. En su lugar: ranking de los **10 clientes por consumo** (monto total, botellas, número de ventas, fecha de última compra).
- Filtros: **año + mes**, o **"Todo el tiempo"**; y **filtro por segmento** (independiente del filtro de fecha).

### MOD-07 · Dashboard — *KPIs de Scoby, alineados a su Excel*

- **Filtros multi-selección de año y mes** arriba de la página, como una tabla dinámica de Excel:
  - Cada uno es un desplegable con **casillas** — se marcan varios años y/o varios meses a la vez — más un botón **"Aplicar"** que recarga.
  - Cada desplegable tiene atajos **"Seleccionar todos"** y **"Limpiar"**.
  - **Sin filtro = todo.** Por defecto (primera carga) el Dashboard muestra **todos los años y todos los meses**. La etiqueta del desplegable dice "Todos los años" / el valor único / "N años" (y equivalente para meses).
  - Todo se agrega sobre la **unión** de lo seleccionado (años × meses). El estado queda en la URL (`?year=2025&year=2026&month=9`), así se puede compartir o recargar.
- **6 indicadores**, en el orden del Excel de Scoby, todos del periodo filtrado:
  1. **Valor Total Pago** — suma del total (con IVA) de las ventas del periodo.
  2. **Total de Botellas** — unidades sumadas de todas las líneas.
  3. **Número de tickets** — cantidad de ventas.
  4. **Número de Facturas** — ventas que llevan IVA (una venta con IVA = factura; sin IVA = boleta).
  5. **Botellas promedio por venta**.
  6. **Valor unitario neto promedio** — promedio simple del precio unitario (neto) de todas las líneas del periodo, cada línea cuenta una vez.
- **4 gráficos** en cuadrícula 2×2, todos respetan ambos filtros:
  - **Participación de ventas por producto** (torta) — reparto del monto neto por producto.
  - **Total de ventas por producto** (barras) — monto neto por producto, con el nombre corto en el eje.
  - **Total de tickets** por mes (barras) — cantidad de ventas por mes.
  - **Total de botellas vendidas** por mes (barras) — unidades por mes.
  - Los dos gráficos "por mes" muestran solo los meses seleccionados en el eje (los 12 si no se marcó ninguno), sumados sobre los años elegidos; el título lista esos años.
- Listado de **productos con stock bajo** (producto / disponible / nivel de reposición) — es el stock actual, no depende del filtro de fecha.
- El Dashboard es visible para **todos los roles** (es la página de aterrizaje común).

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

### MOD-10 · Compras — *libro de gastos de planta con correlativo*

- Registro de los **gastos de gestión de planta que no son insumo de producción** — alcohol gel, un repuesto de máquina, artículos de aseo/oficina. Es un **libro de gastos**, no un módulo de stock: no hay existencias, ni bodega, ni consumo. Distinto de MOD-03 Insumos (esos entran en la receta del producto).
- Cada compra lleva un **código correlativo global** (`C-0001`, `C-0002`, …) que nunca se reinicia.
- Campos: fecha · ítem · proveedor (texto libre) · categoría (texto libre, opcional) · N° de factura · monto · marca *"el monto incluye IVA"* (solo informativa, no calcula nada) · notas.
- **No se elimina una compra, se anula:** conserva su número, queda tachada en la lista y sale del total. Se puede volver a activar.
- **Lista con filtro año / mes** y el **total del periodo** al pie — para la revisión de fin de mes.
- **Solo administrador** (dato financiero, mismo criterio que el catálogo de productos).
- Enhancements a futuro: mantenedor de proveedores y de categorías, adjuntar el archivo de la factura, exportar el reporte a PDF/Excel.

### Transversal

- **Navegación:** el navbar muestra los módulos operativos (Dashboard, Inventario, Insumos, **Compras** —solo administrador—, Ventas, Top clientes, Clientes) y dos menús desplegables:
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
- ✕ **Notificaciones proactivas** (email / SMS / Slack) — el stock bajo o negativo de insumos y de producto se ve en pantalla (aviso al reponer Fermentación + resaltado), no llega un mensaje. → spike [#52](https://github.com/luisurcia/mini_erp/issues/52).
- ✕ **Integración con la cuenta bancaria** para conciliar transferencias con ventas por pagar → spike [#82](https://github.com/luisurcia/mini_erp/issues/82).
- ✕ **Órdenes de compra / reposición sugerida** — la reposición de stock y de insumos es manual. (El módulo Compras registra gastos de planta ya hechos, no genera órdenes ni lleva un catálogo de proveedores.)
- ✕ **Anular / editar / devolver una venta** — no hay pantalla para eso; si se construyera, debería devolver también el stock de producto.
- ✕ **Precios por segmento / lista de precios** — el precio se ingresa a mano en cada venta.
- ✕ **Pagos parciales / abonos** — el estado de pago es binario (por pagar / pagado).
- ✕ **Lotes y vencimiento** — el stock se lleva por producto, no por lote ni fecha de embotellado.
- ✕ **Catálogos oficiales de comuna/región de Chile** — son texto libre.
- ✕ **Modo comparación en el Dashboard** (p. ej. Sep 2025 vs Sep 2026 lado a lado) — hoy el filtro multi-selección suma los periodos, no los compara → [#92](https://github.com/luisurcia/mini_erp/issues/92).
- ✕ **Tienda online / catálogo público**, **app móvil nativa**, **multiempresa**.

## 05 Diferencias respecto del producto genérico (Kombucha ERP)

`main` sigue siendo el ERP genérico. En `client/scoby` se agregó/cambió:

| Área | Genérico | Scoby |
|---|---|---|
| Bodegas | Una sola, stock global | Flujo Fermentación → Principal → distribución + una de insumos; reposición solo a Fermentación, traspasos por el flujo |
| Precio de venta | Precio de catálogo del producto | Libre por línea de venta; catálogo opcional |
| Ingreso de venta | Lista de líneas producto+cantidad | Grilla bodega × producto |
| Insumos | No existía como consumo | Módulo Insumos + receta por producto + descuento automático **al armar** (entrada a Fermentación) |
| Cobranza | No existía | Estado por pagar / pagado + referencia; PDF de ventas por pagar agrupado por cliente |
| Compras / gastos | No existía | Libro de gastos de planta con correlativo global, categoría, anulación y total mensual (solo admin) |
| Dashboard | KPIs genéricos, filtro de un año | 6 KPIs del Excel de Scoby (Valor Total Pago, Total de Botellas, N° de tickets, N° de Facturas, botellas y valor unitario promedio) + filtros multi-selección de año y mes (unión, tipo tabla dinámica) + 4 gráficos 2×2 |
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

- **Recetas de insumos en producción:** los productos existentes están **sin receta**. Ahora que el consumo ocurre al armar (entrada a Fermentación), el equipo puede cargar en `Insumos → Insumos por producto` cuántos insumos lleva cada kombucha y a partir de ahí cada reposición de Fermentación descontará botella + etiqueta + tapa.
- **Bodega de Fermentación en producción:** la que el equipo había creado a mano ("En Fermentación") se renombró a **"Bodega de Fermentación"** y quedó con su rol de flujo; conviene confirmar en `Configuración → Bodegas` que el stock que tuviera se conservó.
- **Datos de usuarios en producción:** los 4 usuarios existentes (admin, Mario, Eduardo, Julien) tienen nombre/apellido en blanco y quedaron todos con rol `admin`; conviene cargar sus nombres y reasignarles rol `bodeguero` / `venta` según corresponda. Al hacerlo, tener presente que `bodeguero` y `venta` ya **no** ven el catálogo de productos ni las recetas (pasaron a solo administrador).
- **Notificaciones** — ver spike [#52](https://github.com/luisurcia/mini_erp/issues/52).
- **Housekeeping de traducciones:** los tres catálogos arrastran entradas obsoletas (`#~`) del módulo Oportunidades eliminado; `pybabel compile` las ignora, pero conviene limpiarlas.
- **Dashboard — modo comparación** (#92) pendiente de definición con el cliente antes de implementar.

---

*Scoby ERP — PRD por ingeniería inversa · rama `client/scoby` · commit `3a0693e` · 2 septiembre 2026*
