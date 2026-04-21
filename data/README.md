# Dashboard de Mantenimiento Minero — Modelo de Datos

Data sintética para portafolio Power BI. Simula 3 años (2023-2025) de operación de una flota de camiones, palas y perforadoras en una operación minera peruana.

## Filosofía del diseño

A diferencia de la data aleatoria típica, esta simulación busca realismo:

- **Fallas por distribución Weibull** parametrizada por componente (ISO 14224 simplificado). Componentes de desgaste (frenos, neumáticos) tienen β > 2; componentes con fallas aleatorias (electrónica) tienen β ≈ 1.
- **Estacionalidad** leve en fallas eléctricas y de motor durante temporada de lluvias (dic-mar).
- **Correlación edad-fallas positiva** (~0.8): equipos viejos fallan más.
- **Ratio PM/CM de ~30/70**: refleja operación real con oportunidad de mejora (world-class es 80/20).
- **Costos calibrados** con referencias de industria minera para equipo pesado.

## Modelo estrella

```
                      ┌────────────────┐
                      │   Dim_Fecha    │
                      └────────┬───────┘
                               │
       ┌───────────────┬───────┼───────┬──────────────────┐
       │               │       │       │                  │
┌──────▼──────┐  ┌────▼────┐  │  ┌────▼────┐  ┌──────────▼──────────┐
│ Dim_Equipo  │  │ Dim_    │  │  │ Dim_    │  │   Dim_Componente    │
│             │  │ Turno   │  │  │ Actividad│  │ (jerárquica ISO)    │
└──────┬──────┘  └────┬────┘  │  └────┬────┘  └──────────┬──────────┘
       │              │       │       │                  │
       │   ┌──────────┴───────┼───────┴──────┐           │
       │   │                  │              │           │
       │   │          ┌───────▼────┐         │           │
       │   │          │  Dim_      │         │           │
       │   │          │  Mecanico  │         │           │
       │   │          └───────┬────┘         │           │
       │   │                  │              │           │
       │   │                  │              │           │
┌──────▼───▼─────┐  ┌────────▼───┐  ┌───────▼────┐  ┌──▼─────────────┐
│ Fact_Eventos   │  │  Fact_OT   │  │ Fact_Plan_ │  │  Fact_Fallas   │
│  _Operacion    │  │            │  │ Mantenim.  │  │                │
│                │  │            │  │            │  │                │
│                │  └────┬───────┘  └────────────┘  └───────┬────────┘
│                │       │                                  │
└────────────────┘       └──────────── Falla_ID ────────────┘
                                (FK débil, no relación)
```

**Dimensiones** (7): Fecha, Equipo, Componente, CausaRaiz, Actividad, Mecanico, Turno
**Hechos** (4): Eventos_Operacion, Fallas, OT, Plan_Mantenimiento

Todas las relaciones son *many-to-one* desde hechos hacia dimensiones. No hay relaciones hecho-a-hecho. `Fact_OT` tiene `Falla_ID` como FK nullable que se cruza via medida DAX, no via relación física.

## Tablas

### Dimensiones

| Tabla | Filas | Descripción |
|---|---|---|
| `Dim_Fecha` | 1,096 | 2023-01-01 a 2025-12-31, con feriados PE y temporada |
| `Dim_Equipo` | 21 | 9 camiones, 6 palas, 6 perforadoras con costos operativos |
| `Dim_Componente` | 36 | Jerarquía Sistema→Subsistema→Componente + params Weibull |
| `Dim_CausaRaiz` | 16 | Causas agrupadas en 6 categorías (Humano, Material, etc.) |
| `Dim_Actividad` | 20 | Actividades tipificadas (Prev/Pred/Corr/Mayor/Insp) |
| `Dim_Mecanico` | 25 | Plantilla con especialidad, nivel, turno y costo/hora |
| `Dim_Turno` | 2 | Día (07-19) y Noche (19-07) |

### Hechos

| Tabla | Filas | Descripción |
|---|---|---|
| `Fact_Eventos_Operacion` | ~66,000 | Log de estado de cada equipo por turno (Op/Standby/Parada/Mant) |
| `Fact_Fallas` | ~2,770 | Eventos de falla con componente, modo, causa raíz, severidad |
| `Fact_OT` | ~3,600 | OTs unificadas: correctivas + preventivas + predictivas + mayores |
| `Fact_Plan_Mantenimiento` | ~1,230 | Plan de mantenimiento con estado de ejecución |

## KPIs calibrados (validados)

| KPI | Valor | Benchmark industria |
|---|---|---|
| Disponibilidad | 82.6% | 85-92% |
| Utilización | 94.0% | 75-85% |
| MTBF global | 152 hrs | 50-200 hrs |
| MTTR global | 5.7 hrs | 4-12 hrs |
| % Cumplimiento plan | 81.2% | 70-85% |
| Ratio PM/CM | 30/70 | 80/20 (world class) |
| Costo total 3 años | USD 11.7M | — |

## Cómo cargar en Power BI

1. Descarga los 11 CSVs a una carpeta local.
2. En Power BI → **Obtener datos** → **Texto/CSV** → carga los 11 archivos (o usa conector de carpeta).
3. En vista de modelo, crea las relaciones:
   - `Dim_Fecha[Fecha]` → 1:* → todas las tablas de hecho por su columna de fecha
   - `Dim_Equipo[Equipo_ID]` → 1:* → todas las tablas con `Equipo_ID`
   - `Dim_Componente[Componente_ID]` → 1:* → `Fact_Fallas[Componente_ID]`
   - `Dim_CausaRaiz[CausaRaiz_ID]` → 1:* → `Fact_Fallas[CausaRaiz_ID]`
   - `Dim_Actividad[Actividad_ID]` → 1:* → `Fact_OT`, `Fact_Plan_Mantenimiento`
   - `Dim_Mecanico[Mecanico_ID]` → 1:* → `Fact_OT[Mecanico_Lider_ID]`
   - `Dim_Turno[Turno_ID]` → 1:* → `Fact_Eventos`, `Fact_Fallas`
4. Marca `Dim_Fecha` como tabla de fechas.
5. Crea una tabla vacía `_Medidas` para organizar tus medidas DAX.

## Medidas DAX sugeridas (starter pack)

```dax
// --- Horas por tipo de evento ---
Hrs Totales        = SUM(Fact_Eventos_Operacion[Horas_Evento])
Hrs Operativas     = CALCULATE([Hrs Totales], Fact_Eventos_Operacion[Tipo_Evento] = "Operativo")
Hrs Mnt Correctivo = CALCULATE(SUM(Fact_OT[Horas_Taller]), Fact_OT[Tipo_OT] = "Correctivo")
Hrs Standby        = CALCULATE([Hrs Totales], Fact_Eventos_Operacion[Tipo_Evento] = "Standby")

// --- KPIs de confiabilidad ---
Nro Fallas  = COUNTROWS(Fact_Fallas)
MTBF (hrs)  = DIVIDE([Hrs Operativas], [Nro Fallas])
MTTR (hrs)  = DIVIDE([Hrs Mnt Correctivo], [Nro Fallas])

Disponibilidad % =
VAR HrsCalendario = [Hrs Totales]
VAR HrsNoProductivas = CALCULATE([Hrs Totales], Fact_Eventos_Operacion[Tipo_Evento] IN {"Parada no planificada", "Mantenimiento programado"})
RETURN DIVIDE(HrsCalendario - HrsNoProductivas, HrsCalendario)

Utilización % = DIVIDE([Hrs Operativas], [Hrs Operativas] + [Hrs Standby])

// --- Costos ---
Costo Total MTO    = SUM(Fact_OT[Costo_Total_USD])
Costo Mano Obra    = SUM(Fact_OT[Costo_ManoObra_USD])
Costo Repuestos    = SUM(Fact_OT[Costo_Repuestos_USD])

// --- Plan ---
OTs Planificadas = COUNTROWS(Fact_Plan_Mantenimiento)
OTs Ejecutadas   = CALCULATE([OTs Planificadas], Fact_Plan_Mantenimiento[Estado_Plan] = "Ejecutado")
% Cumplimiento   = DIVIDE([OTs Ejecutadas], [OTs Planificadas])

// --- Ratio PM/CM (clave para reliability) ---
Ratio PM/CM =
VAR PM = CALCULATE(COUNTROWS(Fact_OT), Fact_OT[Tipo_OT] IN {"Preventivo","Predictivo","Mayor"})
VAR CM = CALCULATE(COUNTROWS(Fact_OT), Fact_OT[Tipo_OT] = "Correctivo")
RETURN DIVIDE(PM, PM + CM)
```

## Notas sobre el generador

- Script Python: `generate_mining_data.py` (reproducible con seed 42)
- Tiempo de generación: ~20 segundos
- Para modificar el periodo, cambia `FECHA_INICIO` / `FECHA_FIN` al tope del script
- Para agregar más equipos, ajusta el diccionario `multiplicadores` en `generar_dim_equipo()`

---
*Data sintética con fines educativos y de portafolio. Ninguna correspondencia con operaciones reales.*
