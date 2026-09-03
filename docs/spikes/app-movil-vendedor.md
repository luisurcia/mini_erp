# Spike — App móvil para vendedores/socios (Ventas, Compras, marcar pagos)

**Tipo:** Spike · **Rama:** `client/scoby` · **Estado:** investigación / estimación, sin código
**Fecha:** 2026-09-03
**Autor:** Arquitecto de Soluciones + Dev Senior (conoce el ERP)

---

## 1. La idea (equipo de Scoby)

Con el ERP ya configurado (clientes, productos, stock), y pensando en el vendedor
que necesita registrar ventas rápido y en los socios que cargan información en el
día a día, se propone una **app móvil** que, una vez autenticado el usuario,
permita:

1. **Ventas** — registrar una venta.
2. **Compras** — registrar un gasto de planta (módulo Compras, #93).
3. **Ventas por pagar → pagadas** — marcar el pago de una venta.

Usuarios de **iPhone**. **Android** podría venir después.

Fuera de alcance de esta primera app: administración de catálogo, inventario,
insumos, recetas, usuarios, empresa, dashboard, top clientes. Esas siguen en la
web.

### Decisiones de alcance ya tomadas (2026-09-03)

- **Son 3 usuarios** (los socios). No es un despliegue masivo.
- **Sin modo offline / desconectado.** Hoy casi siempre hay conexión; no se
  construye cola de sincronización. La app **exige conexión** para cada acción;
  a lo sumo conserva lo que se está escribiendo si el envío falla.
- Con esto, el enfoque queda fijado en **Enfoque A (PWA)**. El Enfoque B (API +
  app de tienda) se mantiene documentado como referencia para una eventual
  Fase 2, pero no es el plan.

---

## 2. Punto de partida: qué hay hoy en el ERP

| Aspecto | Estado actual | Implicancia para una app |
|---|---|---|
| Arquitectura | Flask con render de plantillas en el servidor (`app/blueprints/*/routes.py` devuelven HTML) | **No existe una API JSON.** Todo el back que consuma la app es nuevo. |
| Autenticación | Flask-Login con **cookie de sesión**; CSRF por Flask-WTF | Una app nativa necesita **auth por token** (emitir/refrescar/revocar). Nuevo. |
| Base de datos | SQLite en hosting compartido cPanel (`web-hosting.com`) | Escrituras concurrentes con lock de archivo. Volumen bajo → tolerable, pero es un límite (ver #69/#70). |
| Despliegue | GitHub Actions + SSH a cPanel; el pipeline ya ha sido **frágil** (caídas del host documentadas) | Si la app depende de la API, la caída del host la deja inutilizable. |
| Procesos en background | Solo `cron`. No hay worker ni cola. | Reintentos/colas offline se resuelven en el cliente, no en el server. |
| Seguridad | `SECRET_KEY`/`ADMIN_PASSWORD` con defaults en `config.py` (#54); sin anti-fuerza-bruta ni timeout de sesión (#56); sin cabeceras HTTP (#57) | Exponer el login a Internet para una app **sube la urgencia** del Tramo 0 del epic #53. Dependencia dura. |
| Roles | `admin` / `bodeguero` / `venta`; `venta` ya tiene acceso a Ventas, Productos, Clientes, Top clientes | El rol `venta` cubre casi todo el alcance de la app. **Compras es hoy solo-admin** (`MODULE_PURCHASES`) → decisión pendiente (ver §7). |
| i18n | Catálogos es / en / fr, `pybabel` | Los textos nuevos de la app también hay que traducirlos (es/fr). |
| Datos que necesita la app | clientes, productos ordenados por demanda (`SalesService.active_products_by_demand`), bodegas vendibles + stock (`WarehouseRepository.get_sellable`), config de impuesto/moneda (`Company`), crear venta (`SalesService.record_sale`), listar/marcar pago (`SalesRepository` + `SalesService.register_payment`), crear compra (`PurchaseService`) | La **lógica de negocio ya está en los `*Service`** y se puede reutilizar tal cual desde endpoints nuevos. Esto abarata el back. |

**Conclusión del punto de partida:** no hay barrera arquitectónica. La lógica de
dominio está encapsulada en servicios reutilizables. Lo que falta es **la capa de
exposición (API) y el cliente móvil**, más el endurecimiento de seguridad que de
todos modos está planificado.

---

## 3. Enfoques posibles

### Enfoque A — PWA (web móvil instalable), mismo Flask, sin tienda

Vistas móviles optimizadas dentro de la misma app Flask (o un sub-árbol
`/m/`), con **manifest + service worker** para "agregar a la pantalla de inicio".
Sin API separada (o una mínima para las pantallas dinámicas), sin App Store, sin
cuenta de desarrollador Apple.

- **A favor:** el más barato y rápido; un solo repo y un solo despliegue; Android
  "gratis" desde el día uno; el ERP ya se probó en móvil (issue #49); web push
  disponible en iOS 16.4+ para PWA instalada.
- **En contra:** instalación manual (onboarding de una vez); offline más débil
  (iOS puede purgar el almacenamiento de una PWA tras ~7 días sin uso); no se
  siente 100% "app"; sin acceso pleno a APIs nativas.
- **Encaja cuando:** los usuarios son un puñado de personas internas (los socios /
  el vendedor) y el objetivo es rapidez de captura, no distribución masiva. **Es
  el caso de Scoby.**

### Enfoque B — API REST + app multiplataforma (React Native / Expo)

Capa API JSON en el back Flask + app en Expo (TypeScript), **un solo código para
iOS y Android**. iOS se distribuye por TestFlight (interno). Android se "enciende"
después con costo marginal.

- **A favor:** app real en el teléfono; iOS ahora y Android después casi sin
  código nuevo; buena experiencia offline si se invierte en ello; ecosistema
  maduro.
- **En contra:** capa API nueva completa; cuenta Apple Developer (USD 99/año);
  builds de TestFlight caducan a los 90 días; dos superficies que mantener (API +
  app) para un solo desarrollador.

### Enfoque C — API REST + app nativa iOS (SwiftUI)

Igual back que B, cliente **nativo SwiftUI**. Mejor experiencia iOS posible.

- **En contra:** **Android después = una segunda app desde cero** (~150 h
  extra). Solo tiene sentido si se descarta Android o si la experiencia iOS es
  crítica. **No recomendado** dado que el equipo sí contempla Android.

---

## 4. Estimación de esfuerzo (horas)

> Supuestos: 1 desarrollador senior full-stack que ya conoce el ERP; se
> reutilizan los `*Service` existentes; diseño funcional simple (no se contrata
> UI/UX aparte); pruebas automatizadas en el back y manuales en dispositivo; no
> incluye la negociación de la cuenta Apple ni tiempo de revisión de tienda.
> Las horas incluyen análisis, implementación, pruebas y documentación de cada
> ítem.

### 4.1 Enfoque A — PWA

| Bloque | Detalle | Horas |
|---|---|---:|
| Shell móvil | Layout responsivo, navegación inferior, tema, base de plantillas `/m/` | 16 |
| Sesión larga + login | "Recordar sesión" (30–90 días), endurecer sesión (se cruza con #56), pantalla de login móvil | 10 |
| Endpoints JSON mínimos | Clientes (buscar), productos por demanda, bodegas+stock, config, para las pantallas dinámicas | 12 |
| Pantalla **Ventas** | Buscar cliente, agregar productos, cantidad, precio, bodega, IVA, totales en vivo, enviar — **el rediseño de la grilla producto×bodega para pantalla chica es el ítem duro** | 32 |
| Pantalla **Compras** | Formulario (ítem, proveedor, categoría, monto, fecha, N° doc, notas), enviar | 12 |
| **Ventas por pagar** | Lista filtrable por cliente, buscar por monto, confirmar pago (referencia + fecha), feedback | 16 |
| Manejo de conexión | Conservar lo escrito si el envío falla, aviso "sin conexión", reintento manual (**sin cola offline**) | 4 |
| PWA | Manifest, service worker (solo caché del shell), prompt de instalación iOS, iconos/splash | 12 |
| i18n | Textos nuevos es/fr, ciclo `pybabel` | 4 |
| QA en iPhone real | Safari iOS (teclado, notch, viewport, `100vh`), un par de versiones, correcciones — solo 3 dispositivos objetivo | 14 |
| Pruebas automatizadas | Endpoints + servicios nuevos | 10 |
| Despliegue + docs + cierre del spike | Runbook, README, doc final | 8 |
| **Subtotal** | | **150** |
| Coordinación / gestión + colchón 15 % | | **+22** |
| **Total Enfoque A** | | **≈ 170 h** |

**Rango realista: 150–190 h.**
**Costo con HH \$30.000: 170 × 30.000 = \$5.100.000 CLP** (rango **\$4,5M – \$5,7M**).

> Nota: la baja respecto de la primera versión de este spike (≈190 h) viene de
> (a) descartar la cola offline (−10 h) y (b) QA acotado a 3 dispositivos
> (−4 h).

### 4.2 Enfoque B — API REST + Expo (iOS ahora, Android listo)

**Back — capa API nueva**

| Bloque | Horas |
|---|---:|
| Andamiaje del blueprint API, manejo de errores JSON, versionado (`/api/v1`), CORS | 10 |
| Auth por token: emitir / refrescar / revocar, endpoint de login, middleware, "dispositivos" del usuario | 18 |
| Endpoints: auth, `me`, clientes (listar/buscar/alta mínima), productos por demanda, bodegas+stock, config empresa, ventas (crear/listar/detalle), ventas por pagar, registrar pago, compras (crear/listar) | 24 |
| Serialización + validación de entrada replicando las reglas de los `Form` (reusando servicios) | 12 |
| Rate limiting / throttling de la API + gancho de auditoría (se cruza con #60) | 10 |
| Pruebas de API | 16 |
| **Subtotal back** | **90** |

**App — Expo / React Native (TypeScript)**

| Bloque | Horas |
|---|---:|
| Setup proyecto, navegación, design system, config de entornos, pipeline de build (EAS) | 16 |
| Flujo de auth + almacenamiento seguro del token (Keychain) + refresco automático + logout | 14 |
| Pantalla **Ventas**: buscar cliente, lista de productos (por demanda), constructor de líneas, bodega, cantidad/precio, IVA, totales en vivo, enviar, éxito | 40 |
| Pantalla **Compras**: formulario, categoría, monto, fecha, enviar | 14 |
| **Ventas por pagar**: lista, filtro por cliente, detalle, "marcar pagada" (confirmación + referencia + fecha) | 20 |
| Cola offline / reintento / UI optimista para datos móviles inestables | 20 |
| Estados de error/vacío/carga, pull-to-refresh, UX de validación | 14 |
| i18n (es/fr) | 6 |
| Icono, splash, recursos de tienda | 6 |
| **Subtotal app** | **150** |

**QA + release**

| Bloque | Horas |
|---|---:|
| Pruebas en dispositivos (varios modelos iPhone / versiones iOS) | 20 |
| Alta de cuenta Apple Developer, provisioning, TestFlight interno, distribución | 14 |
| Pasada de corrección de bugs | 24 |
| Docs, runbook, handover, cierre del spike | 8 |
| **Subtotal QA/release** | **66** |

| | Horas |
|---|---:|
| Back 90 + App 150 + QA 66 | 306 |
| Coordinación / gestión + colchón 15 % | +46 |
| **Total Enfoque B** | **≈ 350 h** |

**Rango realista: 300–410 h.**
**Costo con HH \$30.000: 350 × 30.000 = \$10.500.000 CLP** (rango **\$9M – \$12,3M**).

### 4.3 Encender Android más adelante

- **Si se hizo Enfoque A (PWA):** ~0 h de desarrollo. QA en un par de Android +
  ajustes menores: **8–16 h** (\$240.000 – \$480.000).
- **Si se hizo Enfoque B (Expo):** build de Android, alta en Google Play (USD 25
  una vez), QA específico, ajustes de UI: **30–50 h** (\$900.000 –
  \$1.500.000).
- **Si se hubiera hecho Enfoque C (nativo iOS):** segunda app nativa Android:
  **~150 h** (\$4,5M). Este es el motivo para descartar C.

### 4.4 Costos recurrentes (no desarrollo)

| Ítem | Costo | Aplica a |
|---|---|---|
| Apple Developer Program | USD 99 / año (~\$95.000 CLP) | B y C |
| Google Play (una vez) | USD 25 | Android en cualquier enfoque nativo |
| Expo EAS | Plan gratuito suele bastar; ~USD 0 | B |
| Infra extra en el server | \$0 (misma app / mismo hosting) | A; B si la API va en el mismo cPanel |
| Renovar builds TestFlight | Tiempo del dev cada 90 días | B, C |

---

## 5. Recomendación

**Fase 0 — Prototipo (10–15 h, incluido en el total del enfoque elegido).**
Maqueta navegable de la pantalla de Ventas en móvil para validar con el vendedor
**antes** de comprometer el grueso. La grilla producto×bodega es el mayor riesgo
de alcance; hay que verla en un teléfono real con el flujo del vendedor.

**Fase 1 — Enfoque A (PWA), ≈ 170 h / ≈ \$5,1M** (rango 150–190 h / \$4,5M–\$5,7M).
Es el mejor costo/beneficio para Scoby: 3 usuarios internos, objetivo de captura
rápida, un solo repo, Android incluido, sin fricción de tienda, **sin cola
offline** (se exige conexión). Entrega valor en semanas, no meses.
Prerrequisito no negociable: cerrar el **Tramo 0 del epic #53** (#54 secretos por
defecto, #56 anti-fuerza-bruta + timeout, #57 cabeceras) antes de exponer el
login a Internet para uso móvil.

**Fase 2 — Reevaluar.**
Con la PWA en uso real, decidir si una app de tienda (Enfoque B con Expo) agrega
valor suficiente (push más robusto, sensación nativa) para justificar el costo
adicional. Si se decide que sí, la API de la Fase 2 es además la base para el
spike de conciliación bancaria (#82) y para las integraciones de Claude/n8n
(#19).

**Descartar Enfoque C** (nativo iOS) salvo que se abandone Android por completo.

---

## 6. Alcance funcional por pantalla (para cuando se implemente)

### Ventas
- Selección de cliente con **búsqueda** (hoy es un `<select>` plano; en móvil
  necesita buscador por nombre / sobrenombre / RUT).
- Selección de productos: en vez de la grilla completa, un flujo de "agregar
  producto" → elegir producto (orden por demanda), cantidad, bodega (de
  `get_sellable()`), precio unitario.
- Precio: editable por línea (regla actual, #23). Autocompletar con el último
  precio a ese cliente sería un plus (no existe hoy).
- Toggle IVA (default `Company.tax_enabled_default`), totales en vivo
  (subtotal / IVA / total).
- Enviar → `SalesService.record_sale(...)`. Mostrar el N° de venta.
- Advertencia no bloqueante si algún stock queda negativo (comportamiento
  actual).

### Compras
- Formulario: fecha (default hoy), ítem, proveedor, categoría (texto libre),
  N° documento (opcional), monto, "incluye impuesto" (informativo), notas.
- El **correlativo `C-000X` lo asigna el servidor** (`max(sequence)+1`) al
  guardar — la app solo lo muestra en la confirmación.
- Enviar → `PurchaseService.record(...)`.

### Ventas por pagar → pagadas
- Lista de ventas `unpaid`, ordenables/filtrables por cliente y monto.
- Detalle → confirmar pago con **referencia** (obligatoria) y fecha
  (`paid_at`, default hoy) → `SalesService.register_payment(...)`.
- Revertir pago queda **solo-admin** y **solo-web** (no en la app v1).

---

## 7. Decisiones pendientes con el equipo

**Resueltas (2026-09-03):**
- **Modo offline:** NO es requisito. La app exige conexión. (Elimina la cola de
  sincronización del alcance.)
- **Enfoque:** A (PWA). B/C quedan como referencia para una eventual Fase 2 → las
  decisiones sobre distribución iOS y cuenta Apple **no aplican** por ahora.

**Aún por confirmar:**
1. **Compras en la app** es hoy un módulo solo-admin (`MODULE_PURCHASES`). Si un
   socio con rol `venta` debe registrar compras desde la app, hay que:
   - darle el módulo al rol `venta`, o
   - crear un permiso nuevo "registrar compras", o
   - restringir Compras en la app a quienes ya son admin.
   → confirmar quién carga compras en terreno. (Si los 3 usuarios son admin, esto
   no bloquea nada — pero conviene definirlo antes de que existan roles no-admin.)
2. **Alta de clientes desde la app**: ¿un socio puede crear un cliente nuevo
   (nombre + segmento, mínimo actual #74) o solo elegir existentes?
3. **Idiomas en la app**: ¿es/fr como en la web, o solo es?

---

## 8. Riesgos

### 8.1 No existe capa API — superficie nueva completa
Todo el back que consuma la app es nuevo (auth por token, endpoints,
serialización, versionado). El acoplamiento actual vista↔servidor obliga a
construir la capa de exposición desde cero. *Mitigación:* la lógica ya está en
los `*Service`; los endpoints son finos. Aun así es el grueso del Enfoque B.

### 8.2 Seguridad: exponer el login a Internet antes del Tramo 0 (#53)
Hoy: `SECRET_KEY`/`ADMIN_PASSWORD` con defaults (#54), sin anti-fuerza-bruta ni
timeout de sesión (#56), sin cabeceras de seguridad (#57). Una app amplía la
superficie de ataque del login. *Mitigación:* **dependencia dura** — #54/#56/#57
van antes que la app. No es opcional.

### 8.3 Ley 21.719 (vigencia 1 dic 2026)
La app es **otra vía de acceso a datos personales de clientes** (nombre, RUT,
teléfono, dirección, historial). Implica:
- incluir la app en el RAT y en el aviso de privacidad;
- **teléfono perdido = exposición de datos** → tokens de vida corta + logout
  remoto / gestión de dispositivos;
- toda acción desde la app debe quedar en la bitácora de auditoría (#60);
- si se usa un servicio de push de terceros, revisar tratamiento de datos.
*Mitigación:* coordinar con el epic #53; no liberar sin #60 al menos para
Ventas/Clientes.

### 8.4 SQLite + hosting compartido
Escrituras concurrentes con lock de archivo; sin worker para background; el
pipeline de despliegue ya ha fallado por caídas del host. Con la app, una caída
del host = "no puedo vender". *Mitigación:* volumen bajo lo hace tolerable a
corto plazo; a mediano plazo se cruza con #69/#70 (migrar a Postgres/MySQL).
Mantener **siempre** disponible el registro por web como respaldo.

### 8.5 Doble envío / doble venta
Sin cola offline el riesgo baja, pero queda uno: el usuario toca "Guardar", la
respuesta tarda, vuelve a tocar → dos ventas iguales. *Mitigación:* deshabilitar
el botón al primer toque + *idempotency key* por formulario (el server ignora el
segundo envío con la misma clave).

### 8.6 La grilla de Ventas no se traduce a un teléfono
La matriz producto×bodega (#23/#94) es densa para una pantalla chica. Portarla
tal cual fracasa; requiere **rediseño** del flujo de captura. Riesgo de alcance.
*Mitigación:* Fase 0 (prototipo validado con el vendedor) antes del grueso.

### 8.7 Conectividad puntual
Aunque "casi siempre hay conexión", habrá momentos sin señal (ascensor, bodega
del cliente). Al no haber cola offline, la acción simplemente falla. *Mitigación:*
mensaje claro de "sin conexión", conservar lo escrito en el formulario y permitir
reintentar sin volver a tipear. Aceptado como comportamiento esperado, no como
bug.

### 8.8 Un solo mantenedor — factor bus
El Enfoque A mantiene todo en un repo y un despliegue. (El Enfoque B agregaría
una segunda base de código.) Bajo con el enfoque elegido.

### 8.9 Compatibilidad hacia atrás / actualización forzada
Con la app instalada en los teléfonos de los socios, cada cambio de back debe ser
retrocompatible, o se necesita un mecanismo de "actualización obligatoria".
*Mitigación:* versionar la API (`/api/v1`); endpoint de "versión mínima
soportada" que la app consulta al abrir.

### 8.10 Fricción del ecosistema Apple (Enfoque B/C)
Cuenta de desarrollador (D-U-N-S si es de organización), provisioning, builds de
TestFlight que caducan a los 90 días, y revisión de App Store si algún día se
quiere pública. *Mitigación:* TestFlight interno evita la revisión; presupuestar
el trámite de la cuenta (semanas de calendario, no de trabajo).

### 8.11 Falsos positivos al marcar pagos
Dos ventas por el mismo monto y cliente en fechas cercanas: la persona debe
elegir cuál. *Mitigación:* mostrar N° de venta, fecha, factura y monto en la
confirmación; nunca marcar por monto solo.

---

## 9. Resumen ejecutivo

**Plan elegido: Enfoque A — PWA, sin modo offline, 3 usuarios.**

| | Enfoque A — PWA *(elegido)* | Enfoque B — API + Expo *(referencia)* |
|---|---|---|
| Esfuerzo | **≈ 170 h** (150–190) | ≈ 350 h (300–410) |
| Costo (HH \$30.000) | **≈ \$5.100.000** (\$4,5M–\$5,7M) | ≈ \$10.500.000 (\$9M–\$12,3M) |
| Android después | +8–16 h (~\$0,3M) | +30–50 h (~\$1,2M) |
| Costo recurrente | \$0 | USD 99/año Apple |
| Tiempo a valor | Semanas | 2–3 meses |
| App Store | No aplica | TestFlight interno |
| Mantención | 1 repo | API + app |

**Prerrequisitos antes de implementar:**
- Cerrar Tramo 0 del epic #53 (#54, #56, #57).
- Confirmar las decisiones abiertas del §7 (Compras/rol, alta de clientes,
  idiomas).
- Fase 0: prototipo de la pantalla de Ventas validado con el vendedor.

**No es asesoría legal.** Validar los puntos de Ley 21.719 con abogado y con los
reglamentos que dicte la APDP.

---

## 10. Próximos pasos

- [x] Definir enfoque → **Enfoque A (PWA)** y **sin modo offline** (2026-09-03).
- [ ] Responder las decisiones abiertas del §7 (Compras/rol, alta de clientes,
      idiomas).
- [ ] Confirmar prioridad relativa frente al epic #53 y a la promoción del trunk
      (#96) — el Tramo 0 de #53 es prerrequisito.
- [ ] Si hay luz verde: Fase 0 (prototipo de Ventas móvil), luego crear el issue
      de implementación como sub-issue del epic de requerimientos correspondiente,
      enlazado a #53 (seguridad/auditoría) y #52 (notificaciones/push).
