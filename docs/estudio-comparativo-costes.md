# Estudio comparativo del coste de explotación

- **Aplicación:** Pixel Vault — backend FastAPI + frontend Vue 3 (servido como sitio estático).
- **Proveedores comparados:** Render, AWS, Microsoft Azure y Google Cloud.
- **Fecha de consulta de precios:** 12 de noviembre de 2026.
- **Divisa:** USD. **Impuestos:** no incluidos (el IVA se añade según el país y la condición fiscal del cliente).
- **Región de referencia:** Unión Europea (Irlanda / Oeste de Europa / Bélgica), salvo donde se indique.

> Los precios de nube cambian con frecuencia (AWS modificó su nivel gratuito en 2025 y
> Azure y Google renuevan sus promociones cada año). Este documento es una foto fija a
> la fecha indicada: antes de contratar, recalcula con las calculadoras oficiales
> enlazadas al final.

---

## 1. Resumen ejecutivo

| Escenario | Render | AWS | Azure | Google Cloud |
| --------- | -----: | --: | ----: | -----------: |
| **E1 · Demo / corrección** (uso esporádico) | **0,00** | **≈ 0,00** | **0,00** | **0,00** |
| **E2 · Producción ligera 24/7** (50 000 pet./mes, 5 GB) | **7,00** | **7,00** (Lightsail) · 0,05 (Lambda) | **13,14** (App Service B1) · ≈ 0,43 (Container Apps) | **≈ 0,00** (Cloud Run) · 0,00 (e2-micro EE. UU.) |
| **E3 · Crecimiento** (500 000 pet./mes, 50 GB) | **31,75** | **12,00** (Lightsail) · 17,72 (EC2) | **13,14** (App Service B1) · ≈ 10,00 (Container Apps) | **≈ 13,00** (Cloud Run) |

Cifras en USD/mes, sin IVA, con la arquitectura indicada en cada apartado.

**Conclusiones rápidas**

1. **Para la entrega de clase el coste óptimo es 0**, y las cuatro plataformas lo permiten.
   La combinación actual (Render Free + GitHub Pages) ya cumple y no cuesta nada.
2. **Si se exige disponibilidad 24/7 sin *cold starts* y con poca carga**, lo más barato
   y sencillo es **Render Starter (7 USD)** o **AWS Lightsail (7 USD)**; Azure sube a
   **13,14 USD** con App Service B1 y Google puede quedarse en **0 USD** con Cloud Run
   manteniendo una instancia mínima (min-instances = 1) dentro del nivel gratuito.
3. **A medida que crece el tráfico, Render es el que más se encarece**, porque solo
   incluye 5 GB de tráfico al mes (después 0,15 USD/GB). AWS, Azure y Google incluyen
   100 GB (o 1 TB) de salida, por lo que el tráfico no penaliza.
4. **El coste dominante no es la máquina, es el tiempo de operación.** AWS con EC2
   requiere parchear, securizar y monitorizar una VM; Render es *push to deploy*.
   Valorando una hora de trabajo, la diferencia de 6 USD/mes se amortiza sola.

---

## 2. La aplicación que hay que explotar

| Componente | Tecnología | Consumo real |
| ---------- | ---------- | ------------ |
| Backend | FastAPI + Uvicorn, Python 3.13 | Python + 5 dependencias (`fastapi`, `uvicorn`, `pydantic`, `pyjwt`, `bcrypt`). ~120–180 MB de RAM en reposo, arranque < 3 s |
| Frontend | Vue 3 + Vite, compilado | ~1,2 MB de HTML + JS + CSS (≈ 350 KB comprimido). 100 % estático |
| Datos | En memoria (`app/store.py`) | **Sin base de datos** |
| Autenticación | JWT access + refresh, bcrypt | CPU puntual en login (bcrypt es costoso por diseño) |
| Persistencia | Ninguna | Los datos se pierden al reiniciar |

Consecuencias para el coste:

- **No hay coste de base de datos**, que es normalmente la partida más cara de una app web.
- **El backend es diminuto**: 0,25–0,5 vCPU y 256–512 MB sobran para decenas de usuarios concurrentes.
- **El frontend es gratis en la práctica** en cualquier CDN (1–5 MB, tráfico mínimo).
- **El estado en memoria obliga a una sola instancia**: no se puede escalar horizontalmente
  sin romper la sesión de carrito/pedidos. El ahorro en base de datos se paga en
  disponibilidad (si la instancia se reinicia, se pierden los datos).

### Supuestos de carga

| | E1 · Demo | E2 · Producción ligera | E3 · Crecimiento |
| --- | --- | --- | --- |
| Peticiones/mes | 2 000 | 50 000 | 500 000 |
| Usuarios/día | 10 | 100 | 1 000 |
| Salida de red/mes | 1 GB | 5 GB | 50 GB |
| Latencia de arranque en frío | Aceptable | **No aceptable** | No aceptable |
| Disponibilidad | Horario de clase | 24/7 | 24/7 |
| Instancias | 1 | 1 | 1 (estado en memoria) |

---

## 3. Metodología

- **Precio de la máquina:** precio *on-demand* oficial, 730 horas/mes (365 × 24 / 12).
- **Nivel gratuito:** se aplica solo si el uso cabe en sus límites; se indica cuándo caduca.
- **Tráfico:** se cobra la salida a Internet; la entrada es gratuita en todos.
- **Almacenamiento:** disco de arranque de 8–30 GB donde el proveedor no lo incluye.
- **No se incluyen:** dominio (10–15 USD/año, igual en todos), certificados TLS (gratis
  en los cuatro), correo, soporte premium ni el coste del tiempo humano.
- **Región:** se usan precios europeos cuando el proveedor los publica; Google solo
  ofrece su VM gratuita en EE. UU., lo que se señala explícitamente.

**Fuentes principales** (consultadas el 12/11/2026):

- Render: <https://render.com/pricing>
- AWS (precios y calculadora): <https://aws.amazon.com/es/pricing/> · <https://calculator.aws/>
- Azure (precios y calculadora): <https://azure.microsoft.com/es-es/pricing/> · <https://azure.microsoft.com/es-es/pricing/calculator/>
- Google Cloud (precios y calculadora): <https://cloud.google.com/pricing> · <https://cloud.google.com/products/calculator>
- Precios unitarios de AWS: ficheros públicos de precios de AWS (`b0.p.awsstatic.com`).
- Precios unitarios de Azure: API pública *Azure Retail Prices* (`prices.azure.com`).
- Nivel gratuito de Google: <https://cloud.google.com/free/docs/free-cloud-features>

---

## 4. Precios unitarios verificados

### 4.1 Render

| Recurso | Especificaciones | Precio |
| ------- | ---------------- | ------ |
| *Web Service* Free | 512 MB, se duerme a los 15 min | **0 USD/mes** |
| *Web Service* Starter | < 1 CPU, 512 MB | **7 USD/mes** |
| *Web Service* Standard | 1 CPU, 2 GB | **25 USD/mes** |
| *Static Site* | CDN global incluida | **0 USD/mes** |
| Ancho de banda (plan Hobby) | 5 GB incluidos | **0,15 USD/GB** adicional |
| Plan de espacio de trabajo Hobby | — | **0 USD/mes** |

Notas: facturación por segundo; los *Static Sites* no consumen cómputo. El plan Hobby
incluye 500 minutos de *build* al mes (después 5 USD por 1 000).

### 4.2 AWS (Irlanda, `eu-west-1`, Linux)

| Recurso | Especificaciones | Precio |
| ------- | ---------------- | ------ |
| EC2 `t4g.nano` | 2 vCPU (Graviton), 0,5 GB | **3,36 USD/mes** (0,0046 USD/h) |
| EC2 `t4g.micro` | 2 vCPU, 1 GB | **6,72 USD/mes** |
| EC2 `t4g.small` | 2 vCPU, 2 GB | **13,43 USD/mes** |
| EC2 `t3.micro` | 2 vCPU, 1 GB | **8,32 USD/mes** |
| Lightsail | 0,5 GB, 2 vCPU, 20 GB SSD, **1 TB** de tráfico | **5 USD/mes** |
| Lightsail | 1 GB, 2 vCPU, 40 GB SSD, **2 TB** de tráfico | **7 USD/mes** |
| Lightsail | 2 GB, 2 vCPU, 60 GB SSD, **3 TB** de tráfico | **12 USD/mes** |
| Disco EBS `gp3` | — | **0,08 USD/GB-mes** |
| IPv4 pública (EC2) | — | **0,005 USD/h ≈ 3,65 USD/mes** |
| S3 Standard | — | **0,023 USD/GB-mes** |
| CloudFront | 1 TB y 10 M peticiones gratis al mes | después ≈ 0,085 USD/GB |
| Lambda | 1 M peticiones + 400 000 GB-s gratis/mes | después 0,20 USD/M y 0,0000166667 USD/GB-s |
| API Gateway (HTTP API) | — | **1,00 USD/M peticiones** |

Nota importante: desde 2024 **toda IPv4 pública de EC2 se cobra** (3,65 USD/mes), así que
una instancia "gratuita" ya no lo es. En el nivel gratuito nuevo (desde 2025) las cuentas
nuevas reciben **hasta 200 USD en créditos durante 6 meses**, no los 12 meses de `t2.micro`
del programa anterior.

### 4.3 Microsoft Azure (`westeurope`, Linux)

| Recurso | Especificaciones | Precio |
| ------- | ---------------- | ------ |
| App Service **F1** | 1 GB, 60 min de CPU/día, 165 MB/día de salida | **0 USD/mes** |
| App Service **B1** | 1 *core*, 1,75 GB, 10 GB de disco | **13,14 USD/mes** (0,018 USD/h) |
| App Service **P0v3** | 1 *core*, 4 GB | **64,97 USD/mes** |
| Static Web Apps **Free** | 100 GB de tráfico, 0,5 GB de almacenamiento | **0 USD/mes** |
| Static Web Apps **Standard** | 100 GB, SLA, entornos de staging | **9 USD/mes** |
| Container Apps (consumo) | vCPU activa | **0,000034 USD/vCPU-s** (≈ 0,12 USD/vCPU-h) |
| Container Apps (consumo) | memoria activa | **0,000004 USD/GiB-s** |
| Container Apps (consumo) | peticiones | **0,56 USD/M** |
| Container Apps (consumo) | vCPU/RAM en reposo (*idle*) | **0,000004 USD** por vCPU-s / GiB-s |
| VM `B1s` | 1 vCPU, 1 GB | **8,76 USD/mes** (0,012 USD/h) |

Container Apps incluye **180 000 vCPU-s, 360 000 GiB-s y 2 M peticiones gratis al mes**
por suscripción, lo que hace que una instancia mínima pequeña cueste prácticamente 0.
Azure regala **200 USD durante 30 días** y mantiene gratis 65+ servicios; los estudiantes
tienen **Azure for Students (100 USD sin tarjeta)**.

### 4.4 Google Cloud

| Recurso | Especificaciones | Precio |
| ------- | ---------------- | ------ |
| Cloud Run (por petición) | CPU activa | **0,000024 USD/vCPU-s** |
| Cloud Run (por petición) | memoria activa | **0,0000025 USD/GiB-s** |
| Cloud Run (por petición) | peticiones | **0,40 USD/M** |
| Cloud Run (por petición) | CPU/RAM en reposo (min-instances) | **0,0000025 USD** por vCPU-s / GiB-s |
| Cloud Run · nivel gratuito | 180 000 vCPU-s, 360 000 GiB-s, 2 M peticiones/mes | **0 USD/mes** |
| Compute Engine `e2-micro` | 2 vCPU compartidas, 1 GB | **≈ 6,11 USD/mes** (0,008467 USD/h) |
| Compute Engine `e2-micro` · nivel gratuito | 1 instancia/mes en `us-central1`, `us-west1` o `us-east1` | **0 USD/mes** |
| Disco `pd-standard` | — | **≈ 0,04 USD/GB-mes** |
| Cloud Storage Standard | — | **≈ 0,020 USD/GB-mes** |
| Firebase Hosting (Spark) | 10 GB de almacenamiento, 360 MB/día de tráfico | **0 USD/mes** |
| Salida a Internet (nivel Premium) | — | **≈ 0,12 USD/GB** (1 GB gratis solo desde Norteamérica) |

Google regala **300 USD durante 90 días** a cuentas nuevas y mantiene el nivel gratuito
de forma indefinida (no caduca, a diferencia de AWS).

---

## 5. Escenario E1 — Demo / corrección (coste 0)

Objetivo: que el profesor pueda abrir la aplicación y probarla, sin pagar nada.

| Proveedor | Arquitectura | Coste/mes | Comentario |
| --------- | ------------ | --------: | ---------- |
| **Render** | Web Service Free + Static Site Free | **0,00** | Se duerme a los 15 min; el primer acceso tarda 30–60 s |
| **AWS** | Lambda + API Gateway HTTP + S3 + CloudFront | **≈ 0,00** | Todo dentro del nivel gratuito permanente |
| **Azure** | App Service F1 + Static Web Apps Free | **0,00** | Límite de 60 min de CPU/día: suficiente para una demo |
| **Google Cloud** | Cloud Run (0 instancias mínimas) + Firebase Hosting | **0,00** | Escala a cero; *cold start* de ~1 s |

**Coste real del despliegue actual:** Render Free (backend) + GitHub Pages (frontend) = **0 USD/mes**.
GitHub Pages no es uno de los cuatro proveedores, pero es la opción más sencilla para el
frontend porque el repositorio ya está en GitHub y el despliegue es automático con Actions.

**Riesgos de E1:** los cuatro se duermen o limitan; los datos en memoria se pierden en cada
reinicio y el *cold start* de Render es el más lento (hasta 60 s). Para una corrección en
directo, conviene "despertar" la app 2 minutos antes.

---

## 6. Escenario E2 — Producción ligera 24/7

50 000 peticiones/mes, 5 GB de salida, una región europea, sin *cold starts*.

### 6.1 Opciones "siempre encendidas" (PaaS o VM)

| Proveedor | Arquitectura | Cómputo | Tráfico | **Total/mes** |
| --------- | ------------ | ------: | ------: | ------------: |
| **Render** | Web Service Starter (0,5 CPU / 512 MB) + Static Site | 7,00 | 0,00 (5 GB incluidos) | **7,00** |
| **AWS** | Lightsail 1 GB (2 vCPU / 40 GB / 2 TB) + S3/CloudFront | 7,00 | 0,00 | **7,00** |
| **AWS** | EC2 `t4g.nano` + 8 GB `gp3` + IPv4 pública | 3,36 + 0,64 + 3,65 | 0,00 (100 GB gratis) | **7,65** |
| **Azure** | App Service B1 Linux | 13,14 | 0,00 (100 GB gratis) | **13,14** |
| **Azure** | VM `B1s` + disco de 32 GB | 8,76 + ≈ 2,40 | 0,00 | **≈ 11,20** |
| **Google Cloud** | `e2-micro` en `us-central1` (nivel gratuito) | 0,00 | 1 GB gratis | **0,00** \* |
| **Google Cloud** | `e2-micro` en Europa + 30 GB de disco | 6,11 + 1,20 | ≈ 0,60 | **≈ 7,90** |

\* Solo en EE. UU. (`us-central1`, `us-west1`, `us-east1`) y con 1 GB de salida al mes;
latencia desde España de ~100–150 ms. No tiene SLA.

### 6.2 Opciones serverless (escalan a cero o pagan solo uso)

| Proveedor | Arquitectura | Cálculo | **Total/mes** |
| --------- | ------------ | ------- | ------------: |
| **AWS** | Lambda (512 MB) + API Gateway HTTP | 5 000 GB-s y 50 000 pet. dentro del nivel gratuito; API GW 0,05 | **≈ 0,05** |
| **AWS** | App Runner 0,25 vCPU / 0,5 GB | 0,25 × 0,064 × 730 + 0,5 × 0,007 × 730 | **14,24** |
| **Azure** | Container Apps, min = 1, 0,25 vCPU / 0,5 GiB | 7,99 de uso − 7,56 de nivel gratuito | **≈ 0,43** |
| **Google Cloud** | Cloud Run, min = 1, 0,25 vCPU / 512 MiB | 4,93 + uso − 5,22 de nivel gratuito | **≈ 0,00** |

**Lectura:** el precio "de tarifa" de una instancia siempre encendida es parecido en los
cuatro (7–14 USD/mes), pero **los modelos serverless con instancia mínima gratuita
(Cloud Run y Container Apps) bajan a casi cero** porque el nivel gratuito cubre el reposo.

### 6.3 Coste por 1 000 peticiones (E2)

| Proveedor | Coste/1 000 pet. |
| --------- | ---------------: |
| Render Starter | 0,14 USD |
| AWS Lightsail | 0,14 USD |
| AWS Lambda | 0,001 USD |
| Azure App Service B1 | 0,26 USD |
| Azure Container Apps | 0,009 USD |
| Google Cloud Run | ≈ 0,00 USD |

---

## 7. Escenario E3 — Crecimiento (500 000 peticiones/mes, 50 GB)

| Proveedor | Arquitectura | Cómputo | Tráfico | **Total/mes** |
| --------- | ------------ | ------: | ------: | ------------: |
| **Render** | Standard (1 CPU / 2 GB) | 25,00 | 45 GB × 0,15 = 6,75 | **31,75** |
| **AWS** | Lightsail 2 GB (3 TB incluidos) | 12,00 | 0,00 | **12,00** |
| **AWS** | EC2 `t4g.small` + 8 GB + IPv4 | 13,43 + 0,64 + 3,65 | 0,00 (100 GB) | **17,72** |
| **Azure** | App Service B1 | 13,14 | 0,00 (100 GB) | **13,14** |
| **Azure** | Container Apps, min = 1, 0,5 vCPU / 1 GiB | 17,55 − 7,56 | 0,00 | **≈ 10,00** |
| **Google Cloud** | Cloud Run, min = 1, 1 vCPU / 512 MiB | 18,21 − 5,22 | 6,00 (50 GB × 0,12) | **≈ 13,00** |

**Aquí se invierte la clasificación:** Render pasa a ser el más caro por el ancho de banda
(5 GB incluidos frente a 100 GB o 1 TB de los demás) y por el salto de precio del plan
(25 USD por 1 CPU / 2 GB).

---

## 8. Comparativa a 12 y 36 meses (solo infraestructura)

| Opción | USD/mes | 12 meses | 36 meses |
| ------ | ------: | -------: | -------: |
| Render Free (demo) | 0,00 | 0 | 0 |
| Render Starter (24/7) | 7,00 | 84 | 252 |
| AWS Lambda + API Gateway | 0,05 | 0,60 | 1,80 |
| AWS Lightsail 1 GB | 7,00 | 84 | 252 |
| AWS EC2 `t4g.nano` | 7,65 | 91,80 | 275,40 |
| Azure Container Apps (min = 1) | 0,43 | 5,16 | 15,48 |
| Azure App Service B1 | 13,14 | 157,68 | 473,04 |
| Google Cloud Run (min = 1) | ≈ 0,00 | ≈ 0 | ≈ 0 |
| Google Cloud `e2-micro` (Europa) | 7,90 | 94,80 | 284,40 |

No se aplican descuentos por compromiso (reservas de 1 o 3 años), que en AWS, Azure y
Google pueden rebajar el cómputo un 30–60 % si se renuncia a la flexibilidad.

---

## 9. Costes ocultos y trampas habituales

### Render

- **Solo 5 GB de tráfico** en el plan Hobby; a partir de ahí, 0,15 USD/GB (el más caro de los cuatro).
- El plan Free **se duerme a los 15 minutos** y tarda 30–60 s en despertar.
- **No hay autoescalado horizontal** en Hobby (sí en Pro, 25 USD/mes de plan + cómputo).
- El plan Hobby tiene **500 minutos de build**; un monorepo con builds frecuentes puede agotarlos.
- Sin SLA en Hobby; el SLA exigible empieza en Enterprise.

### AWS

- **IPv4 pública de EC2: 3,65 USD/mes** desde febrero de 2024. Una `t4g.nano` "barata"
  pasa de 3,36 a 7,01 USD solo por tener IP.
- **El nuevo nivel gratuito dura 6 meses** (200 USD en créditos), no 12. Fuera de eso,
  `t2.micro`/`t3.micro` se factura.
- **Salida de datos:** 100 GB/mes gratis; después ≈ 0,09 USD/GB (más CloudFront aparte).
- **Gestión:** IAM, grupos de seguridad, actualizaciones del sistema, CloudWatch, copias…
  es el proveedor con más superficie operativa.
- **Lambda + FastAPI** exige un adaptador (`Mangum`) y cambia el modelo de ejecución
  (sin estado entre peticiones, límite de 15 min).
- **ALB** (balanceador) cuesta ≈ 16–20 USD/mes: usarlo con Fargate dispara la factura.

### Microsoft Azure

- **App Service F1** tiene 60 minutos de CPU **al día**: si se agotan, el sitio deja de
  responder hasta el día siguiente. No sirve para producción real.
- **App Service B1** no incluye *slots* de despliegue ni autoescalado; para eso, S2 o P1v3.
- Los precios publicados en EUR pueden diferir de los de EE. UU.; la factura incluye IVA
  si el cliente no aporta NIF intracomunitario.
- **Container Apps** cobra el entorno y las réplicas mínimas: hay que vigilar el número
  de réplicas y la configuración de escalado.
- El crédito de bienvenida (**200 USD**) caduca a los **30 días**; los 12 meses de
  servicios gratuitos solo aplican a cuentas nuevas.

### Google Cloud

- **El `e2-micro` gratuito solo existe en tres regiones de EE. UU.** En Europa se paga
  (≈ 6,11 USD/mes) y **no incluye** el disco ni la salida.
- La salida de Cloud Run usa el **nivel Premium** (≈ 0,12 USD/GB) y el GB gratuito solo
  aplica desde Norteamérica: servir desde `europe-west1` no lo aprovecha.
- **Cloud Run con `min-instances = 0`** pierde el estado en memoria en cada arranque;
  con `min-instances = 1` se paga el reposo (aunque el nivel gratuito lo cubre en este caso).
- El crédito de **300 USD** caduca a los **90 días**; si no se pasa a cuenta de pago,
  los recursos se borran.

### Comunes a todos

- **Sin base de datos no hay persistencia:** cualquier reinicio, despliegue o *scale to zero*
  borra usuarios, carrito y pedidos. Si se añade persistencia, el coste sube (ver §10).
- **Un solo proceso:** el estado en memoria impide escalar horizontalmente. Dos instancias
  = dos tiendas distintas.
- **Dominio y DNS:** 10–15 USD/año, igual en los cuatro; TLS es gratis.
- **Soporte:** incluido solo en planes básicos (chat/foro). Un SLA con respuesta garantizada
  se paga aparte (o exige plan Enterprise).

---

## 10. Si en el futuro se añade persistencia

| Proveedor | Servicio | Coste aproximado |
| --------- | -------- | ---------------: |
| Render | Postgres (256 MB–1 GB) | 0 USD (free) – 6 USD/mes |
| AWS | RDS `db.t4g.micro` + 20 GB | ≈ 13–15 USD/mes |
| Azure | PostgreSQL Flexible `B1ms` + 32 GB | ≈ 13–15 USD/mes |
| Google Cloud | Cloud SQL `db-f1-micro` + 10 GB | ≈ 10–12 USD/mes |

Añadir base de datos **duplica o triplica** el coste en E2 y elimina la ventaja de los
niveles gratuitos, por lo que conviene mantener el almacén en memoria mientras el proyecto
sea académico (es una decisión de diseño ya documentada en `README.md`).

---

## 11. Comparativa cualitativa

| Criterio | Render | AWS | Azure | Google Cloud |
| -------- | ------ | --- | ----- | ------------ |
| Facilidad de despliegue | ★★★★★ (git push) | ★★☆☆☆ | ★★★☆☆ | ★★★★☆ |
| Tiempo de puesta en marcha | 15 min | 2–8 h | 1–3 h | 1–3 h |
| Mantenimiento mensual | ≈ 0 h | 1–4 h (si hay VM) | 0,5–1 h | 0,5–1 h |
| *Cold start* | 30–60 s (free) | ~0,5–1 s (Lambda) | ~1–3 s (CA) | ~0,5–1 s |
| Escalado automático | Hobby no / Pro sí | Sí (Lambda, ASG) | Sí | Sí (nativo) |
| Tráfico incluido | 5 GB | 100 GB / 1 TB CF | 100 GB | 1 GB (EE. UU.) |
| Nivel gratuito | Permanente | **6 meses** (nuevo) | 12 meses + siempre gratis | **Permanente** |
| Crédito inicial | — | 200 USD / 6 meses | 200 USD / 30 días | 300 USD / 90 días |
| Región europea | Sí | Sí | Sí | Sí (VM gratis no) |
| Bloqueo (*lock-in*) | Medio | Bajo | Medio | Medio-bajo |
| Documentación / comunidad | Buena | Excelente | Buena | Excelente |
| Precio a gran escala | Caro (tráfico) | Muy bueno | Bueno | Muy bueno |

**Lectura cualitativa**

- **Render** es el que menos tiempo cuesta: conectas el repositorio y despliega. Ideal para
  el proyecto y para equipos pequeños. Su punto débil es el tráfico y el precio al crecer.
- **AWS** es el más potente y el más barato a escala, pero también el que más exige:
  IAM, redes, parches y una curva de aprendizaje que en un trabajo de clase no aporta.
- **Azure** encaja si el centro o la empresa ya usa Microsoft (cuentas, Entra ID, GitHub
  Education). App Service es cómodo, pero el plan gratuito es demasiado limitado.
- **Google Cloud** es el que mejor combina precio y comodidad: Cloud Run escala a cero,
  el nivel gratuito es permanente y la CLI/consola son claras. Su asterisco es la región
  gratuita de `e2-micro` (solo EE. UU.) y el coste de salida.

---

## 12. Recomendación

| Situación | Recomendación |
| --------- | ------------- |
| **Entrega del trabajo / corrección** | Mantener **Render Free + GitHub Pages**: 0 USD y ya está funcionando |
| **Demo 24/7 con arranque inmediato y poco tráfico** | **Render Starter (7 USD)** o **Google Cloud Run con `min-instances = 1` (≈ 0 USD)** |
| **Presupuesto mínimo absoluto** | **Google Cloud Run** (nivel gratuito permanente) o **`e2-micro` gratuito** si se acepta EE. UU. |
| **Máximo control y coste a largo plazo** | **AWS Lightsail (7–12 USD)** por precio/prestaciones, o **EC2** si se necesita VPC y servicios gestionados |
| **Entorno corporativo Microsoft** | **Azure App Service B1 (13,14 USD)**; Container Apps si se quiere escalado a cero |

**Para este proyecto en concreto**, la recomendación es:

1. **Ahora:** dejar el despliegue como está (Render Free + GitHub Pages). Coste 0 y cumple
   todos los requisitos de la entrega.
2. **Si se pide "producción real":** pasar el backend a **Render Starter (7 USD/mes)**,
   que elimina el *cold start* y mantiene el mismo flujo de despliegue, o migrarlo a
   **Cloud Run** con `min-instances = 1` si se quiere coste ≈ 0 y se acepta el *lock-in* de Google.
3. **No migrar a AWS** solo por precio: con 50 000 peticiones al mes, el ahorro frente a
   Render es de unos pocos dólares y el coste en horas de configuración es mucho mayor.

### Cómo recalcular

- **Render:** precio del plan + (GB de salida − 5) × 0,15.
- **AWS EC2:** (horas × precio/hora) + (GB de disco × 0,08) + 3,65 (IPv4) + salida extra.
- **AWS Lambda:** (GB × segundos × 0,0000166667) + (millones de peticiones × 0,20)
  + API Gateway (millones × 1,00), aplicando el nivel gratuito.
- **Azure App Service:** horas × 0,018 (B1 Linux).
- **Azure Container Apps:** (vCPU-s activos × 0,000034) + (vCPU-s en reposo × 0,000004)
  + (GiB-s × 0,000004) + (millones de peticiones × 0,56) − nivel gratuito.
- **Cloud Run:** (vCPU-s × 0,000024) + (GiB-s × 0,0000025) + (millones × 0,40) − nivel gratuito.
- **e2-micro:** horas × 0,008467 + disco + salida.

### Buenas prácticas de control de coste

- Activar **alertas de presupuesto** (AWS Budgets, Azure Cost Management, presupuestos de
  GCP, avisos de facturación de Render) con umbral en 1 USD.
- Etiquetar todos los recursos (`proyecto=pixel-vault`, `entorno=demo`).
- Elegir **región europea** para latencia y para cumplir el RGPD.
- No dejar IPs públicas ni bases de datos abiertas.
- Apagar o destruir los recursos al terminar la asignatura (especialmente en AWS y Azure,
  donde los créditos caducan y luego se factura).
- Revisar la factura el primer mes: los precios de lista no siempre coinciden con lo que
  se factura (impuestos, redondeos, servicios auxiliares como logs o discos).

---

## Anexo · Enlaces oficiales

| Proveedor | Precios | Calculadora |
| --------- | ------- | ----------- |
| Render | <https://render.com/pricing> | — |
| AWS | <https://aws.amazon.com/es/pricing/> | <https://calculator.aws/> |
| Azure | <https://azure.microsoft.com/es-es/pricing/> | <https://azure.microsoft.com/es-es/pricing/calculator/> |
| Google Cloud | <https://cloud.google.com/pricing> | <https://cloud.google.com/products/calculator> |

Niveles gratuitos:

- AWS Free Tier: <https://aws.amazon.com/free/>
- Azure Free: <https://azure.microsoft.com/en-us/pricing/free-services>
- Google Cloud Free Tier: <https://cloud.google.com/free/docs/free-cloud-features>
- Render Free: <https://render.com/docs/free>
