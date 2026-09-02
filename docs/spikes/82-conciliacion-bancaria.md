# Spike #82 — Conciliación de transferencias bancarias con ventas por pagar

**Tipo:** Spike · **Rama:** `client/scoby` · **Estado:** investigación cerrada, sin código
**Fecha:** 2026-09-02

---

## 1. Objetivo

Evaluar si el ERP puede integrarse con la cuenta bancaria de Scoby para que, al
llegar una **transferencia entrante**, el sistema **sugiera a qué venta "por
pagar" corresponde**, y con la confirmación de una persona la marque **pagada**
dejando como referencia el **identificador de la transacción del banco**.

No se busca (todavía) marcar pagos de forma 100% automática.

## 2. Cómo funciona hoy (#51)

- `Sale.payment_status` = `unpaid` / `paid`.
- Al registrar el pago, una persona escribe a mano `payment_reference` (el
  número de transferencia) y opcionalmente la fecha (`paid_at`).
- Existe la lista de ventas por pagar y el PDF (#81, #88).
- No hay ninguna conexión con el banco. El dato de "llegó la plata" vive solo
  en la cabeza / el correo / la cartola de quien cobra.

## 3. Proveedores de Open Finance en Chile

Chile tiene Ley Fintec (21.521) y un Sistema de Finanzas Abiertas en
implementación gradual por la CMF. Mientras tanto, los agregadores operan con
credenciales del portal bancario del usuario.

| Proveedor | Qué ofrece para este caso | Bancos (empresa) | Modelo | Notas |
|---|---|---|---|---|
| **Fintoc** | Producto *Movements / Data*: lee la cartola y entrega cada movimiento normalizado. Webhook `movement.created`. También tiene "Conciliación bancaria" como producto empaquetado. | Banco de Chile, Santander, Itaú, BICE, Scotiabank, BCI, BancoEstado, Security (+ SII). Cuentas empresa soportadas (portales/credenciales de empresa). | El usuario crea un *Link* autorizando con sus credenciales del banco; Fintoc refresca periódicamente (frecuencia según plan) y/o notifica por webhook. | El más maduro y usado en Chile. Doc pública y SDK. Autorizado por la CMF como emisor de prepago. |
| **Floid** | APIs bancarias + producto "Conciliación de pagos" que cruza en tiempo real movimientos vs. registros internos. Además valida cuentas (RUT + N° + banco) y RUT contra Registro Civil / SII. | Cobertura amplia de bancos chilenos. | Igual que Fintoc: conexión con credenciales, entrega de balances y movimientos normalizados. | Fuerte en validación de identidad/cuentas, útil si además se quiere verificar el RUT del emisor. |
| **Khipu** | Históricamente iniciación de pagos por transferencia con notificación instantánea (webhook al confirmar). Tiene lectura de cartola (`banking`) para Banco de Chile y otros, y producto de conciliación. | Depende del producto; la lectura de cartola tiene menos cobertura que Fintoc. | Webhook al confirmar el pago cuando el cobro se inicia *a través de* Khipu; la lectura de cartola es aparte. | Encaja mejor si Scoby empujara a sus clientes a pagar con un link Khipu (cambia el flujo comercial). Para "el cliente transfiere como siempre", el producto relevante es la lectura de cartola. |
| **Cartola / API directa del banco** | — | — | Casi ningún banco chileno expone API pública para pyme. Banconexión etc. son portales web. | Descartado salvo que el banco de Scoby ofrezca algo puntual. |
| **Correo de aviso del banco** | Parsear el mail "recibiste una transferencia" | — | Polling de una casilla IMAP + regex. | Frágil (cambia el formato, se pierde, no trae RUT), pero costo ~0. Último recurso o puente temporal. |

## 4. Datos por transferencia entrante — ¿alcanzan para conciliar?

Del objeto *Movement* de Fintoc (representativo del resto):

| Campo | Sirve para |
|---|---|
| `amount` (+ `currency`) | **Match principal**: monto exacto vs. `Sale.total_amount`. |
| `post_date` / `transaction_date` | Ventana de fechas (p. ej. ± 5 días de la venta o desde la emisión de la factura). |
| `sender_account.holder_name` | Match difuso contra `Customer.name` / `nickname`. |
| `sender_account.holder_id` | **RUT del emisor** → match fuerte contra `Customer.rut` (cuando esté cargado). |
| `sender_account.number` / `institution` | Aprender la cuenta de cada cliente para futuros matches. |
| `description` | Glosa: a veces trae el N° de factura o el nombre; match por texto. |
| `reference_id` | **Identificador del banco** → queda como `payment_reference`. |
| `type` = `transfer` | Filtrar solo transferencias entrantes (amount > 0, `recipient_account` = cuenta de Scoby). |

**Conclusión:** monto + fecha + (RUT del emisor **o** nombre **o** glosa) es
suficiente para *sugerir* con buena precisión. La advertencia de Fintoc es que
los datos del emisor **a veces vienen nulos o incorrectos** (depende del banco),
por eso la confirmación humana no es opcional en la v1.

## 5. Modelo de conexión

- **Autorización:** una persona de Scoby (con acceso al portal *empresa* del
  banco) crea el Link una vez, ingresando sus credenciales en el widget del
  proveedor. El ERP nunca ve la clave del banco; guarda solo el *link token*.
- **Actualización:** webhook `movement.created` (ideal) + un *polling* de
  respaldo 1–2 veces al día por si se pierde un webhook.
- **Reconexión:** los Links se caen cuando el banco pide re-MFA o cambia la
  clave → hay que manejar el estado "link caído" y avisar (se conecta con #52).

## 6. Costo (referencial — **confirmar con cotización**)

- El **1% + IVA** que se publicita de Fintoc es de **iniciación de pagos**
  (el cliente paga con Fintoc), **no** de leer movimientos.
- El producto *Data / Movements* se cobra aparte (típicamente cargo mensual por
  cuenta conectada y/o por refresco). Fintoc no publica esa tarifa; hay que
  pedirla.
- Floid y Khipu, mismo esquema: cotización directa.
- Orden de magnitud esperable para 1 cuenta: **cargo mensual bajo (decenas de
  USD) + posible costo por consulta**. A validar.
- Alternativa correo IMAP: costo de infraestructura ~0, costo de desarrollo y
  mantención alto en frationalidad.

## 7. Seguridad y Ley 21.719

La ley entra en vigencia el **1 dic 2026**. Esta integración agrega datos
personales sensibles del punto de vista reputacional (movimientos bancarios,
RUT y nombre de terceros que transfieren) → se coordina con el **epic #53**.

- **Minimización:** guardar solo lo necesario para conciliar. No almacenar la
  cartola completa ni movimientos que no son transferencias entrantes. Descartar
  los que no matchean tras N días.
- **Base de licitud:** ejecución de contrato (cobro de una venta). Documentar en
  el RAT (#64 / TRZ-2).
- **Encargado de tratamiento:** contrato de encargo con el proveedor
  (Fintoc/Floid/Khipu). Revisar dónde procesan y alojan los datos.
- **Transferencia internacional:** si el proveedor procesa fuera de Chile, aplica
  el régimen de transferencia internacional (INT-1, #72).
- **Credenciales del banco:** nunca tocan el ERP. El *link token* es un secreto
  → mismo tratamiento que una API key (fuera del repo, idealmente cifrado en
  reposo cuando exista, #71).
- **Trazabilidad:** cada match sugerido, aceptado o rechazado y cada marca de
  "pagado" via banco debe quedar en la bitácora de auditoría (#60 / TRZ-1).
- **Datos de terceros:** el emisor de la transferencia puede no ser el cliente
  (paga un familiar, la empresa). Guardar nombre/RUT del emisor solo si aporta a
  la conciliación y con retención acotada.

## 8. Lógica de conciliación propuesta (v1 — sugerir + confirmar)

1. Llega un movimiento entrante tipo `transfer`.
2. El sistema busca ventas `unpaid` candidatas:
   - `amount` == `Sale.total_amount` (match exacto; permitir tolerancia 0 en la v1).
   - `movement.date` dentro de una ventana respecto a `sale_date` / emisión.
   - opcional refuerzo: `holder_id` == `Customer.rut`, o `holder_name` ~ `Customer.name`, o la glosa contiene el `invoice_number`.
3. Se genera una **sugerencia de conciliación** con un puntaje:
   - 1 candidata clara → propuesta directa (aún requiere click de confirmación).
   - varias → lista para que la persona elija.
   - ninguna → el movimiento queda "sin asignar" en una bandeja.
4. Al **confirmar**, se llama a `SalesService.register_payment(sale_id, reference=movement.reference_id, paid_at=movement.date)` y el movimiento queda ligado a esa venta.
5. Movimientos sin match tras N días → se archivan/descartan según política de retención.

**Nunca** marcar `paid` sin confirmación humana en la v1. Una v2 podría
auto-confirmar cuando el match es inequívoco (monto exacto + RUT del emisor ==
RUT del cliente + una sola candidata).

## 9. Arquitectura aproximada en el ERP (para cuando se implemente)

Modelos nuevos (borrador):

- `BankConnection` — proveedor, link token (secreto), estado (`active` /
  `needs_reauth`), última sincronización.
- `BankMovement` — datos normalizados del movimiento (monto, fechas, emisor,
  glosa, `external_id`, `raw` acotado), estado (`unmatched` / `suggested` /
  `matched` / `discarded`), `sale_id` nullable.
- `ReconciliationSuggestion` (o campos en `BankMovement`) — venta candidata +
  puntaje + quién/cuándo confirmó o rechazó.

Piezas:

- `webhook /bank/webhook` (verificación de firma del proveedor) → encola el movimiento.
- Job de polling de respaldo (cron ya existe en el server).
- `BankReconciliationService` — genera sugerencias, aplica la confirmación
  reusando `SalesService.register_payment`.
- Pantalla **"Conciliación bancaria"** dentro de Ventas: bandeja de movimientos,
  sugerencias, acción confirmar/rechazar, movimientos sin asignar.
- Permiso: módulo `SALES` (ver) + `admin` para confirmar, o un permiso nuevo.
- Auditoría: enganchar con #60.
- Alertas de "link caído" / "movimiento sin match" → #52.

## 10. Recomendación

1. **Proveedor: Fintoc**, producto *Movements / Data* (o su paquete de
   Conciliación bancaria). Razones: mejor cobertura de bancos empresa en Chile,
   documentación y SDK públicos, webhook de movimientos, ya es estándar de
   mercado. **Floid** como segunda opción, atractiva si además se quiere validar
   RUT/identidad del emisor. **Khipu** solo si Scoby decide cobrar con links de
   pago (otro proyecto).
2. **Alcance v1:** solo lectura de movimientos + conciliación **asistida**
   (sugerir, la persona confirma). Sin pagos automáticos, sin iniciación de
   pagos.
3. **Prerrequisitos antes de implementar:**
   - Cotización formal de Fintoc (y Floid) para 1 cuenta empresa.
   - Definir con Scoby qué banco y quién administra la conexión.
   - Cargar los **RUT de los clientes** (hoy opcional, #74) — es el mejor
     campo de match; sin él la precisión baja.
   - Coordinar con el epic #53: bitácora (#60), RAT/base de licitud (#64),
     contrato de encargo, retención.
4. **Estimación gruesa de desarrollo (v1):** 2–3 semanas (modelos + webhook +
   servicio de matching + pantalla + auditoría + pruebas), sin contar la
   negociación comercial con el proveedor.

## 11. Riesgos

- **Datos del emisor nulos/erróneos** según el banco → el match por RUT/nombre
  puede fallar; el de monto+fecha es el piso.
- **Links que se caen** (re-MFA, cambio de clave) → necesita monitoreo y un
  flujo de reconexión claro, si no la conciliación "deja de funcionar" en
  silencio.
- **Costo recurrente** que hoy no está cotizado.
- **Cumplimiento:** sube el perfil de datos del ERP justo antes de la vigencia
  de la ley; no hacerlo sin la bitácora (#60) y el contrato de encargo.
- **Falsos positivos:** dos ventas por el mismo monto en fechas cercanas →
  siempre debe decidir una persona en la v1.
- **Dependencia de un tercero** para una función de caja: si el proveedor tiene
  un incidente, se vuelve al registro manual (que se mantiene siempre disponible).

## 12. Próximos pasos

- [ ] Pedir cotización a Fintoc (Movements/Conciliación) y a Floid.
- [ ] Confirmar con Scoby: banco, cuenta, responsable de la conexión.
- [ ] Empujar la carga de RUT de clientes (#74).
- [ ] Si hay luz verde comercial: crear el issue de implementación (v1 asistida)
      como sub-issue del epic de requerimientos, enlazado a #52 y #53.

---

## Fuentes

- [Guía de conciliación bancaria para empresas — Fintoc](https://fintoc.com/guias/guia-conciliacion-bancaria-empresas)
- [Conciliación bancaria — Fintoc](https://fintoc.com/cl/productos/conciliacion-bancaria)
- [Movement Object — Fintoc docs](https://docs.fintoc.com/reference/movements-object)
- [Get bank movements — Fintoc docs](https://docs.fintoc.com/docs/guides-bank-movements)
- [Products and Institutions (Movements) — Fintoc docs](https://docs.fintoc.com/docs/products-and-institutions-movements)
- [Receive transfers — Fintoc docs](https://docs.fintoc.com/guides/transfers/inbound-transfers)
- [APIs Bancarias & Conciliaciones en Chile — Floid](https://www.floid.io/servicios/apis-bancarias-y-conciliaciones)
- [Conciliación de Pagos Automática y Segura — Floid](https://www.floid.io/servicios/conciliacion-de-pagos)
- [Validación cuentas bancarias en Chile — Floid](https://www.floid.io/servicios/validacion-de-cuentas)
- [API de Pagos Instantáneos — Khipu docs](https://docs.khipu.com/en/payment-solutions/instant-payments/description)
- [Khipu docs](https://docs.khipu.com/en)
- [Fintoc Chile 2026: Cobros por Transferencia al 1% + IVA — CómoCobro](https://comocobro.cl/medios-de-pago/fintoc)
- [Los planes de Fintoc para 2026 — Diario Financiero](https://www.df.cl/mercados/banca-fintech/los-planes-de-fintoc-para-2026-nuevo-sistema-operativo-de-pagos-y)
