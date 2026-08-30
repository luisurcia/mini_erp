# Documento de producto · PRD

**Kombucha ERP**

> Migrado desde `Kombucha_ERP_PRD.pdf` (25 agosto 2026) a Markdown para que quede legible y versionable en el repo. **Referencia histórica de la evaluación inicial — describe el sistema genérico antes de la personalización de Scoby.** Para el estado actual de la rama `client/scoby`, ver **[`Scoby_ERP_PRD.md`](Scoby_ERP_PRD.md)** (PRD por ingeniería inversa). El seguimiento del trabajo está en GitHub Issues (épicas [#20](https://github.com/luisurcia/mini_erp/issues/20), [#36](https://github.com/luisurcia/mini_erp/issues/36), [#47](https://github.com/luisurcia/mini_erp/issues/47)).

Qué hace hoy el sistema, tal como está operando en producción — para que un productor de kombucha lo revise y nos diga qué funcionalidades le sirven, cuáles le sobran y cuáles le faltan.

| FECHA | ESTADO | BASE | PREPARADO PARA |
|---|---|---|---|
| 25 agosto 2026 | En producción | Funcionalidad existente | Evaluación de usuario |

## 01 Resumen

Kombucha ERP es un sistema web simple para llevar el negocio de una productora artesanal de kombucha: qué sabores y botellas tiene en stock, qué se vende, qué pedidos llegan por Instagram u otros canales antes de convertirse en venta, y quién puede ver o tocar cada cosa. Nació a partir de un caso real de un productor de kombucha y hoy corre con datos reales de ventas.

Este documento no es una propuesta desde cero: describe lo que el sistema ya hace, módulo por módulo, para que puedas evaluarlo contra tu propia operación y decirnos qué te sirve tal cual, qué le falta y qué directamente no necesitarías.

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

- ✓ Indicadores: productos activos, stock bajo, oportunidades abiertas, ingresos del mes, facturas emitidas, ticket promedio, ventas totales del año.
- ✓ Gráficos: ventas por producto (monto y % del total), ventas por mes, botellas vendidas por mes.
- ✓ Listado directo de productos con stock bajo y últimas oportunidades abiertas.

#### MOD-06 · Usuarios y roles — *en producción*

**Quién ve y quién edita** — Tres niveles de acceso, aplicados tanto en el sistema como en lo que se ve en pantalla.

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

## 05 Tu turno: ayúdanos a validarlo

No hace falta responder por escrito — sirve como guía para la conversación. Lo que más nos interesa es dónde este sistema calza con tu operación real y dónde se queda corto.

**General**

- ¿Estos siete módulos cubren cómo manejas hoy tu negocio, o falta algo grande que no está aquí?
- ¿Con qué frecuencia revisarías el dashboard: a diario, semanal, una vez al mes?
- ¿Cuántas personas de tu equipo necesitarían entrar al sistema, y con qué rol cada una?

**Inventario**

- ¿Manejas más de un formato o envase por sabor? ¿El modelo actual (sabor → producto → tamaño) te calza?
- La kombucha es un producto vivo: ¿necesitas controlar fecha de embotellado o vencimiento, algo que hoy no existe?

**Ventas**

- ¿Te basta un número de factura como referencia, o necesitas facturación electrónica real desde el día uno?
- ¿Vendes con distintos medios de pago (efectivo, transferencia, tarjeta) que debieras poder registrar?

**Oportunidades y clientes**

- ¿Tus consultas llegan sobre todo por Instagram, o hay otros canales que falte agregar como origen?
- ¿Necesitas diferenciar clientes mayoristas de clientes finales, por ejemplo con precios distintos?

**Para cerrar**

De todo lo descrito: ¿cuáles son las 3 funcionalidades que más valor te darían primero? ¿Y hay algo en la lista que de plano no usarías nunca?

---

*Kombucha ERP — Documento de producto · Basado en la versión en producción · agosto 2026*
