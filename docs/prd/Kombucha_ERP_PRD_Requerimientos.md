# Documento de producto · PRD editable

**Kombucha ERP**

> Migrado desde `Kombucha_ERP_PRD_Requerimientos.docx` (25 agosto 2026) a Markdown para que quede legible y versionable en el repo. Se conserva como referencia — para `client/scoby`, el seguimiento vivo de requerimientos se hace en GitHub Issues (ver el épica [#20](https://github.com/luisurcia/mini_erp/issues/20) y sus 13 issues hijos). Cuando esta rama llegue a su versión final, se generará un PRD nuevo por ingeniería inversa a partir de lo efectivamente construido, en vez de seguir completando la tabla de abajo.

Qué hace hoy el sistema, y un espacio al final de este documento para que agregues los requerimientos nuevos que te gustaría tener — escritos en un formato que Claude Code puede leer directamente para construirlos.

| FECHA | ESTADO | BASE | FORMATO |
|---|---|---|---|
| 25 agosto 2026 | Sistema en producción | Funcionalidad existente | Word — editable |

## 01 Resumen

Kombucha ERP es un sistema web simple para llevar el negocio de una productora artesanal de kombucha: qué sabores y botellas tiene en stock, qué se vende, qué pedidos llegan por Instagram u otros canales antes de convertirse en venta, y quién puede ver o tocar cada cosa. Corre hoy en producción con datos reales de ventas.

Las secciones 1 a 4 describen lo que el sistema ya hace. La sección 5 te explica cómo escribir un requerimiento nuevo — un feature que falta o un cambio a algo existente — para que quede listo para que Claude Code lo construya. La sección 6 es la tabla donde lo escribes.

## 02 Para quién está pensado

Un productor o equipo pequeño de bebidas fermentadas (kombucha u otro producto similar) que hoy maneja stock, ventas y pedidos de forma manual — planillas, WhatsApp, memoria — y quiere un solo lugar donde quede registrado todo, sin la complejidad de un ERP genérico de escritorio.

## 03 Módulos actuales

Siete módulos, ya construidos y en uso.

#### MOD-01 · Inventario — *en producción*

**Sabores, botellas y stock** — Catálogo de sabores y productos, con el stock siempre bajo control.

- ✓ Cada sabor puede tener varios productos (formatos): nombre, SKU único, tamaño en ml y precio.
- ✓ Nivel de reposición configurable por producto, con alerta de stock bajo visible en el dashboard.
- ✓ Reposición manual de stock y ajustes de conteo, cada uno con nota opcional.
- ✓ Historial completo de movimientos por producto: qué entró, qué salió y por qué (venta, reposición o ajuste).
- ✓ El sistema nunca deja vender más de lo que hay disponible.

#### MOD-02 · Ventas — *en producción*

**Registro de ventas reales** — Ventas multi-línea que descuentan stock automáticamente.

- ✓ Una venta puede incluir varios productos en distintas cantidades.
- ✓ Al completarse, el stock se descuenta solo — validado, sin sobreventa.
- ✓ Número de factura y notas libres, opcionales, por venta.
- ✓ IVA opcional por venta, calculado con la tasa configurada a nivel de empresa.
- ✓ Estados: pendiente, completada o cancelada.

#### MOD-03 · Oportunidades — *en producción*

**Pedidos y consultas antes de la venta** — Para lo que llega antes de ser venta: una consulta por DM preguntando precio mayorista, por ejemplo.

- ✓ Origen del contacto: DM de Instagram, sitio web, referido u otro.
- ✓ Embudo con etapas: nuevo → contactado → cotizado → ganado / perdido.
- ✓ Producto y cantidad solicitada, asociados a la oportunidad.
- ✓ Convertir a venta con un clic — genera la venta y descuenta stock automáticamente.
- ✓ Las oportunidades abiertas aparecen listadas en el dashboard.

#### MOD-04 · Clientes — *en producción*

**Ficha básica de cliente** — Un registro simple, compartido entre ventas y oportunidades.

- ✓ Nombre, email, teléfono, usuario de Instagram y notas libres.
- ✓ No distingue hoy entre cliente final y mayorista.

#### MOD-05 · Dashboard — *en producción*

**Métricas del negocio** — Una vista de un vistazo, con filtro por año y mes.

- ✓ Indicadores: productos activos, stock bajo, oportunidades abiertas, ingresos del mes, facturas emitidas, ticket promedio, ventas del año.
- ✓ Gráficos: ventas por producto, ventas por mes, botellas vendidas por mes.
- ✓ Listado directo de productos con stock bajo y últimas oportunidades abiertas.

#### MOD-06 · Usuarios y roles — *en producción*

**Quién ve y quién edita** — Tres niveles de acceso, aplicados tanto en el sistema como en pantalla.

- ✓ Administrador: acceso total, incluida la gestión de usuarios.
- ✓ Editor: crea y edita registros, sin gestión de usuarios.
- ✓ Lector: solo consulta — los botones de edición se ocultan.
- ✓ Cada persona puede cambiar su propia contraseña.

#### MOD-07 · Empresa — *en producción*

**Configuración general** — Ajustes válidos para toda la operación, no por usuario.

- ✓ Tasa de IVA configurable (hoy: 19%) y si aplica por defecto en ventas nuevas.
- ✓ Idioma de toda la plataforma: español o inglés.

## 04 Qué no incluye hoy

Para que la evaluación sea realista, esto es lo que el sistema deliberadamente no hace todavía:

- ✕ Facturación electrónica: el número de factura es un campo de texto libre, no se timbra ni se envía a ningún organismo.
- ✕ Cobro o pagos en línea — no hay pasarela de pago integrada.
- ✕ Órdenes de compra a proveedores — la reposición de stock es manual, sin gestión de proveedores.
- ✕ Múltiples bodegas o sucursales — el stock es uno solo, no por ubicación.
- ✕ Notificaciones automáticas por email o WhatsApp — el stock bajo y las oportunidades se revisan a mano en el dashboard.
- ✕ Tienda online o catálogo público para venta directa al cliente final.
- ✕ App móvil nativa — es una aplicación web, funciona desde el navegador.
- ✕ Una sola empresa por instalación — no está pensado para operar varias marcas desde un mismo sistema.

## 05 Cómo agregar un requerimiento nuevo

Esta sección es para ti si, al revisar los módulos de arriba, pensaste "me falta X" o "esto lo necesito distinto". Escribe cada idea siguiendo este formato en la tabla de la sección 6 — así queda en un lenguaje que Claude Code puede leer y convertir directamente en trabajo, sin ida y vuelta para aclarar qué quisiste decir.

**Los campos de cada requerimiento**

- **Título:** Un nombre corto para identificarlo (3 a 6 palabras).
- **Historia de usuario:** "Como [rol], quiero [qué], para [por qué]". El "para qué" es el más importante: le dice a Claude Code el objetivo real, no solo el mecanismo, y a veces existe una forma más simple de lograrlo.
- **Módulo:** Usa las etiquetas MOD-01 a MOD-07 de este documento, o escribe "nuevo módulo" si no calza en ninguno de los existentes.
- **Prioridad:** Alta, Media o Baja — ayuda a decidir qué se construye primero.
- **Criterios de aceptación:** La parte más importante. Lista corta y verificable de "dado esto, cuando pase esto, entonces debería pasar esto otro". Evita frases vagas como "que funcione bien" o "que sea intuitivo": describe el comportamiento paso a paso, incluidos los casos borde (¿qué pasa si el campo queda vacío? ¿si el stock es cero?).
- **Notas:** Datos concretos si los tienes: nombre y tipo de un campo nuevo, si es obligatorio, ejemplos reales, capturas de pantalla de otro sistema, etc.

**Dos reglas simples**

- Un requerimiento por fila. Si una idea tiene varias partes independientes, sepáralas en varias filas — es más fácil de construir y de revisar.
- Sé específico, no aspiracional. "Sería bueno que algún día se pudiera..." no es accionable; "cuando el stock llega a 0, bloquear el botón de vender" sí lo es.

**Ejemplo ya completado**

La primera fila de la tabla en la sección 6 muestra un requerimiento real, completado como modelo — puedes copiar su estructura para los tuyos.

## 06 Tus requerimientos

Completa una fila por requerimiento. La primera fila (REQ-00) es el ejemplo de la sección anterior — bórrala cuando termines, o déjala como referencia.

| ID | Título | Historia de usuario (Como / Quiero / Para) | Módulo | Prioridad | Criterios de aceptación | Notas |
|---|---|---|---|---|---|---|
| REQ-00 | *Fecha de vencimiento por lote* | *Como dueña de la producción, quiero registrar la fecha de vencimiento de cada lote embotellado, para poder priorizar la venta de lo más antiguo y evitar pérdidas.* | MOD-01 · Inventario | Alta | *1) Al reponer stock se puede indicar una fecha de vencimiento opcional para ese lote. 2) El dashboard muestra alerta cuando un lote vence en <7 días. 3) Si no se indica fecha, el producto funciona igual que hoy.* | *Hoy el inventario no diferencia por lote, solo por producto — puede requerir cambio de modelo de datos.* |
| REQ-01 | | | | | | |
| REQ-02 | | | | | | |
| REQ-03 | | | | | | |
| REQ-04 | | | | | | |
| REQ-05 | | | | | | |
| REQ-06 | | | | | | |
| REQ-07 | | | | | | |
| REQ-08 | | | | | | |

¿Más de 8 requerimientos? Copia la última fila las veces que necesites.
