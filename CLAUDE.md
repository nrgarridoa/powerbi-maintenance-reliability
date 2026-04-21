# CLAUDE.md — Dashboard Mantenimiento Minero (Power BI)

> Archivo de contexto para Claude Code. Léelo completo antes de hacer cualquier cosa en este repo.

## 0. TL;DR

Proyecto de portafolio: dashboard Power BI de confiabilidad y mantenimiento para flota minera (camiones, palas, perforadoras). Partió de un caso académico que muchos compañeros tienen igual → el objetivo explícito es **replicar el original y superarlo** con mejoras técnicas, analíticas y de diseño que lo diferencien.

**Stack**: Power BI Desktop (PBIP + TMDL cuando se pueda) · Python para data sintética · Git.
**Datos**: sintéticos, 3 años (2023-2025), generados con distribuciones Weibull realistas. Ya están en `/data/`.
**Estado actual**: modelo rediseñado y data generada. Pendiente: construir el .pbix.

---

## 1. Objetivo y criterios de éxito

El proyecto se considera exitoso cuando:

1. **Replica** todas las páginas del dashboard original (Disponibilidad, Fallas, Productividad Taller, Cumplimiento Plan).
2. **Mejora** el original con al menos 4 de estas diferenciaciones:
   - Página Home ejecutiva con navegación por botones.
   - Análisis de confiabilidad (Weibull, bathtub curve, MTBF por componente).
   - Costo de la no-disponibilidad (lucro cesante).
   - Pareto de fallas (80/20) por costo y por horas perdidas.
   - Ratio PM/CM con benchmark world-class.
   - OEE completo (Disponibilidad × Rendimiento × Calidad).
   - Backlog de OTs con aging (0-7, 8-30, 31-90, +90 días).
   - Análisis de productividad por mecánico.
3. **Arquitectura pro**: formato PBIP + TMDL para versionado en Git, Calculation Groups para Time Intelligence, Field Parameters.
4. **Design system unificado** en todas las páginas (paleta, tipografía, espaciado, jerarquía).
5. **README del repo** tipo case study con contexto de negocio, preguntas respondidas y decisiones de diseño.

**No es éxito**: un clon bonito del dashboard original. Si termina pareciéndose demasiado al caso de clase, perdió.

---

## 2. Decisiones ya tomadas (no volver a cuestionar sin motivo)

| Decisión | Elección | Por qué |
|---|---|---|
| Modelo de datos | Rediseño completo (estrella limpia) | El original tenía snowflake (fallas→mantenimiento) y dos tablas de mantenimiento redundantes |
| Ventana temporal | 3 años (2023-2025) | Permite YoY y tendencias largas |
| Formato de data | CSVs separados por tabla | Simple, legible en Git, fácil de cargar en PBI |
| Data real vs sintética | Sintética pero realista | No hay acceso a data real; es repo personal |
| Contexto de negocio | Minería peruana (referencia: operación tipo Antamina/Las Bambas) | Usuario está en Lima, enriquece el storytelling |
| Idioma del dashboard | Español | Consistente con el original |
| Idioma del código / commits | Español para textos de usuario, inglés para código/commits técnicos | Estándar del portafolio |

---

## 3. Modelo de datos

### Dimensiones (7)

| Tabla | PK | Notas |
|---|---|---|
| `Dim_Fecha` | `Fecha` | 2023-01-01 a 2025-12-31. Incluye Anio, Mes, Trimestre, NombreMes (español), EsFinDeSemana, EsFeriadoPE, Temporada (Lluvias/Otoño/Invierno seco/Primavera) |
| `Dim_Equipo` | `Equipo_ID` | 21 equipos: 9 Camiones, 6 Palas, 6 Perforadoras. Incluye Codigo_Equipo, Costo_Hora_Operacion_USD, Costo_Hora_Parada_USD, Criticidad, Zona |
| `Dim_Componente` | `Componente_ID` | 36 componentes con jerarquía Sistema→Subsistema→Componente (ISO 14224 simplificado). **Incluye Beta_Weibull y Eta_Weibull_Hrs** — útiles para análisis de confiabilidad |
| `Dim_CausaRaiz` | `CausaRaiz_ID` | 16 causas agrupadas en 6 categorías (Humano, Material, Diseño, Operación, Mantenimiento, Externo) |
| `Dim_Actividad` | `Actividad_ID` | 20 actividades tipificadas (Preventiva, Predictiva, Correctiva, Mayor, Inspección) con duración y costo estimados |
| `Dim_Mecanico` | `Mecanico_ID` | 25 mecánicos con nombres peruanos, especialidad, nivel, turno, costo/hora |
| `Dim_Turno` | `Turno_ID` | 2 turnos: Día (07-19) y Noche (19-07) |

### Hechos (4)

| Tabla | Granularidad | Filas aprox |
|---|---|---|
| `Fact_Eventos_Operacion` | Un registro por bloque de estado de cada equipo (Operativo/Standby/Parada/Mantenimiento) | ~66,000 |
| `Fact_Fallas` | Un registro por falla detectada | ~2,770 |
| `Fact_OT` | Un registro por OT (unifica Correctivo + Preventivo + Predictivo + Mayor, discriminados por `Tipo_OT`) | ~3,600 |
| `Fact_Plan_Mantenimiento` | Un registro por plan (ejecutado, cancelado, reprogramado, pendiente) | ~1,230 |

### Relaciones (todas *many-to-one* hecho→dimensión)

```
Dim_Fecha ──┬──> Fact_Eventos_Operacion (Fecha)
            ├──> Fact_Fallas (Fecha)
            ├──> Fact_OT (Fecha_Ingreso)
            └──> Fact_Plan_Mantenimiento (Fecha_Programada)

Dim_Equipo ──┬──> Fact_Eventos_Operacion (Equipo_ID)
             ├──> Fact_Fallas (Equipo_ID)
             ├──> Fact_OT (Equipo_ID)
             └──> Fact_Plan_Mantenimiento (Equipo_ID)

Dim_Componente ──> Fact_Fallas (Componente_ID)
Dim_CausaRaiz  ──> Fact_Fallas (CausaRaiz_ID)
Dim_Turno      ──> Fact_Eventos_Operacion (Turno_ID), Fact_Fallas (Turno_ID)
Dim_Actividad  ──┬──> Fact_OT (Actividad_ID)
                 └──> Fact_Plan_Mantenimiento (Actividad_ID)
Dim_Mecanico   ──> Fact_OT (Mecanico_Lider_ID)
```

**Importante**:
- No hay relaciones hecho-a-hecho. `Fact_OT[Falla_ID]` existe pero **NO** debe crearse como relación física — se resuelve via medida DAX si se necesita cruzar.
- `Dim_Fecha` debe marcarse como tabla de fechas en PBI.
- Crear tabla vacía `_Medidas` con una columna dummy para organizar medidas (aparece arriba por el guion bajo).

---

## 4. KPIs calibrados (validados contra benchmarks industria)

La data sintética ya está calibrada para producir estos valores globales:

| KPI | Valor generado | Benchmark industria | Lectura |
|---|---|---|---|
| Disponibilidad | 82.6% | 85-92% | Ligeramente bajo → hay oportunidad (narrativa) |
| Utilización | 94.0% | 75-85% | Alto → flota trabaja intensamente |
| MTBF | 152 hrs | 50-200 hrs | En rango |
| MTTR | 5.7 hrs | 4-12 hrs | En rango |
| % Cumplimiento Plan | 81.2% | 70-85% | En rango |
| Ratio PM/CM | 30/70 | 80/20 (world class) | **Deliberadamente bajo** — da narrativa de mejora continua |
| Costo total 3 años | USD 11.7M | — | Consistente con equipo pesado |

**Correlación edad-fallas**: 0.81 (positiva → equipos viejos fallan más, como debe ser).

---

## 5. Estructura del repo

```
/
├── CLAUDE.md                      (este archivo)
├── README.md                      (README público del repo — pendiente redactar)
├── .gitignore                     (ignorar .pbix en favor de PBIP)
├── data/
│   ├── Dim_Fecha.csv
│   ├── Dim_Equipo.csv
│   ├── Dim_Componente.csv
│   ├── Dim_CausaRaiz.csv
│   ├── Dim_Actividad.csv
│   ├── Dim_Mecanico.csv
│   ├── Dim_Turno.csv
│   ├── Fact_Eventos_Operacion.csv
│   ├── Fact_Fallas.csv
│   ├── Fact_OT.csv
│   ├── Fact_Plan_Mantenimiento.csv
│   └── README.md                  (documentación del modelo + diagrama)
├── scripts/
│   └── generate_mining_data.py    (generador reproducible, seed=42)
├── pbi/
│   └── Dashboard_Mantenimiento.pbip   (pendiente crear)
├── docs/
│   ├── decisiones_diseno.md       (pendiente)
│   ├── medidas_dax.md             (pendiente)
│   └── images/                    (screenshots del dashboard final)
└── reference/
    └── original_screenshots/      (capturas del dashboard original, para comparación)
```

---

## 6. Starter pack de medidas DAX

Ya definidas conceptualmente. Pegar en `_Medidas` cuando se cree el PBIX.

```dax
// ===== HORAS POR TIPO DE EVENTO =====
Hrs Totales        = SUM(Fact_Eventos_Operacion[Horas_Evento])
Hrs Operativas     = CALCULATE([Hrs Totales], Fact_Eventos_Operacion[Tipo_Evento] = "Operativo")
Hrs Standby        = CALCULATE([Hrs Totales], Fact_Eventos_Operacion[Tipo_Evento] = "Standby")
Hrs Parada NoPlan  = CALCULATE([Hrs Totales], Fact_Eventos_Operacion[Tipo_Evento] = "Parada no planificada")
Hrs Mnt Programado = CALCULATE([Hrs Totales], Fact_Eventos_Operacion[Tipo_Evento] = "Mantenimiento programado")
Hrs Mnt Correctivo = CALCULATE(SUM(Fact_OT[Horas_Taller]), Fact_OT[Tipo_OT] = "Correctivo")

// ===== CONFIABILIDAD =====
Nro Fallas  = COUNTROWS(Fact_Fallas)
MTBF (hrs)  = DIVIDE([Hrs Operativas], [Nro Fallas])
MTTR (hrs)  = DIVIDE([Hrs Mnt Correctivo], [Nro Fallas])

Disponibilidad % =
VAR HrsCalendario = [Hrs Totales]
VAR HrsNoProductivas = [Hrs Parada NoPlan] + [Hrs Mnt Programado]
RETURN DIVIDE(HrsCalendario - HrsNoProductivas, HrsCalendario)

Utilización % = DIVIDE([Hrs Operativas], [Hrs Operativas] + [Hrs Standby])

// ===== COSTOS =====
Costo Total MTO    = SUM(Fact_OT[Costo_Total_USD])
Costo Mano Obra    = SUM(Fact_OT[Costo_ManoObra_USD])
Costo Repuestos    = SUM(Fact_OT[Costo_Repuestos_USD])

Costo No Disponibilidad =
SUMX(
    Fact_Fallas,
    RELATED(Dim_Equipo[Costo_Hora_Parada_USD]) * Fact_Fallas[Horas_Parada_Equipo]
)

// ===== PLAN =====
OTs Planificadas = COUNTROWS(Fact_Plan_Mantenimiento)
OTs Ejecutadas   = CALCULATE([OTs Planificadas], Fact_Plan_Mantenimiento[Estado_Plan] = "Ejecutado")
OTs Canceladas   = CALCULATE([OTs Planificadas], Fact_Plan_Mantenimiento[Estado_Plan] = "Cancelado")
OTs Reprogramadas= CALCULATE([OTs Planificadas], Fact_Plan_Mantenimiento[Estado_Plan] = "Reprogramado")
% Cumplimiento   = DIVIDE([OTs Ejecutadas], [OTs Planificadas])

// ===== RATIO PM/CM (KPI CLAVE DE REL. ENG.) =====
OTs PM = CALCULATE(COUNTROWS(Fact_OT), Fact_OT[Tipo_OT] IN {"Preventivo","Predictivo","Mayor"})
OTs CM = CALCULATE(COUNTROWS(Fact_OT), Fact_OT[Tipo_OT] = "Correctivo")
Ratio PM/CM = DIVIDE([OTs PM], [OTs PM] + [OTs CM])

// ===== PRODUCTIVIDAD TALLER =====
Horas Hombre     = SUM(Fact_OT[Horas_Hombre])
AVG Reparación   = AVERAGE(Fact_OT[Horas_Taller])
Productividad    = DIVIDE([Horas Hombre], [Horas Taller Total])

// ===== TIME INTELLIGENCE (pendiente: migrar a Calculation Group) =====
MTBF YoY % = DIVIDE([MTBF (hrs)] - CALCULATE([MTBF (hrs)], SAMEPERIODLASTYEAR(Dim_Fecha[Fecha])), CALCULATE([MTBF (hrs)], SAMEPERIODLASTYEAR(Dim_Fecha[Fecha])))
```

---

## 7. Roadmap

**Fase 1 — Fundación** (≈día 1)
- [x] Diseño modelo estrella
- [x] Generación de data sintética validada
- [ ] Crear repo con estructura definida en sección 5
- [ ] Cargar los 11 CSVs en Power BI Desktop
- [ ] Crear relaciones según sección 3
- [ ] Marcar `Dim_Fecha` como tabla de fechas
- [ ] Crear tabla `_Medidas` vacía
- [ ] Pegar medidas DAX del starter pack
- [ ] Guardar como `.pbip` (File → Save As → Power BI project)

**Fase 2 — Replicar original** (≈días 2-3)
- [ ] Página "Disponibilidad y Utilización" (replicar)
- [ ] Página "Análisis Fallas" (replicar)
- [ ] Página "Productividad Taller" (replicar)
- [ ] Página "Cumplimiento Plan Mantenimiento" (replicar)

**Fase 3 — Diferenciación** (≈días 4-7)
- [ ] **Página Home ejecutiva** (nueva): KPIs clave + botones de navegación + narrativa dinámica
- [ ] **Página Reliability Engineering** (nueva): Weibull por componente, bathtub, MTBF por sistema, ratio PM/CM con benchmark
- [ ] **Página Cost Analysis** (nueva): Pareto por costo, lucro cesante, costo por tipo de mantenimiento, costo por equipo
- [ ] **Página Backlog & Taller** (nueva): aging de OTs, productividad por mecánico, cuellos de botella
- [ ] Design system unificado (paleta, tipografía, espaciado, iconos)
- [ ] Drill-through Equipo → detalle
- [ ] Tooltip pages personalizados
- [ ] Calculation Groups para Time Intelligence
- [ ] Field Parameters para selector dinámico de métrica

**Fase 4 — Pulido** (≈día 8)
- [ ] README del repo tipo case study
- [ ] Screenshots de cada página en `docs/images/`
- [ ] Documentar decisiones de diseño en `docs/decisiones_diseno.md`
- [ ] `.gitignore` correcto (ignorar .pbix, conservar solo PBIP)
- [ ] Deploy a Power BI Service (opcional pero suma)

---

## 8. Convenciones

**Nomenclatura**
- Dimensiones: `Dim_PascalCase`
- Hechos: `Fact_PascalCase_con_guion_bajo`
- Tabla de medidas: `_Medidas` (guion bajo al inicio para que aparezca arriba)
- Medidas DAX: `PascalCase con espacios` (ej: `MTBF (hrs)`, `Costo Total MTO`)
- Columnas calculadas: `PascalCase sin espacios`

**Estilo DAX**
- Usar `VAR` para medidas con más de una línea.
- Siempre `DIVIDE` en lugar de `/` para evitar división por cero.
- Comentarios con `//` para medidas importantes.
- Indentación con 4 espacios.

**Git**
- Commits en inglés, imperativo: `add reliability page`, `fix mtbf measure`.
- Nunca commitear `.pbix` — solo `.pbip` + carpetas de definición.

---

## 9. Gotchas y cosas que NO hacer

1. **NO crear relación física `Fact_OT[Falla_ID]` → `Fact_Fallas[Falla_ID]`**. Es relación hecho-a-hecho, mala práctica. Si se necesita cruzar, usar medida DAX con `TREATAS` o `LOOKUPVALUE`.

2. **NO usar `.pbix` si se puede usar `.pbip`**. Para versionado en Git, PBIP es mucho mejor (archivos TMDL legibles). Habilitar en: Opciones → Vista previa → Formato de proyecto de Power BI.

3. **NO tocar `generate_mining_data.py` sin actualizar el seed**. Si se regenera con seed diferente, cambian todos los números — romperá screenshots y documentación.

4. **NO hacer visuales de "tarjeta grande con número solo"**. El original abusa de eso. Acompañar cada KPI con: variación vs periodo anterior, benchmark, o sparkline.

5. **NO reproducir la estética inconsistente del original** (páginas mezcladas entre fondo oscuro y fondo claro peach). Un solo design system.

6. **NO usar emojis en los títulos de visuales**. Sí en iconos SVG o fuentes de iconos.

7. **Cuidado con `Fact_Eventos_Operacion`**: son ~66k filas, el archivo CSV pesa 6.4 MB. Al cargarlo en Power Query, asegurarse de que los tipos de dato se detecten bien (especialmente `Fecha_Hora_Inicio` y `Fecha_Hora_Fin` como datetime).

8. **La data tiene seed=42 y estacionalidad sutil**. Si en el análisis los gráficos "no muestran nada", no cambiar el seed — la estacionalidad es intencionalmente realista (no caricaturesca).

---

## 10. Referencias útiles

- **ISO 14224** (Reliability data collection for equipment in oil/gas/mining) — la taxonomía de componentes se inspira en esta norma
- **Fórmulas MTBF/MTTR**: Hrs Operativas / Nro Fallas (no Hrs Calendario)
- **Weibull β interpretation**: β<1 mortalidad infantil · β=1 aleatorio · β>1 desgaste
- **World-class maintenance ratios**: 80% proactivo (PM+PdM) / 20% reactivo (CM)
- **Paleta sugerida** (dark premium): fondo `#0F1115`, superficies `#1A1D24`, texto primario `#E6E8EB`, acento teal `#3BA99C`, alerta rojo `#E06C75`, warning ámbar `#D19A66`

---

## 11. Historial de decisiones en chat previo

Para contexto, estas son las preguntas ya resueltas:

- **¿Rediseñar o respetar modelo original?** → Rediseño completo
- **¿Ventana temporal?** → 3 años (2023-2025)
- **¿Formato de datos?** → CSVs separados por tabla
- **¿Data real o sintética?** → Sintética (repo personal)
- **¿Contexto de negocio?** → Minería peruana

Pendientes de confirmar con el usuario:
- Estética visual final (dark premium / light minimalista / industrial-minero). Sugerencia actual: dark premium.
- Si migramos a PBIP desde el inicio o trabajamos en PBIX y migramos al final.
- Si hay deploy a Power BI Service.
