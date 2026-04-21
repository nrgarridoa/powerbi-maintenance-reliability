"""
Generador de Data Sintética - Dashboard Mantenimiento Minero
=============================================================
Genera datasets realistas para un modelo estrella de Power BI
enfocado en confiabilidad y mantenimiento de flota minera.

Características:
- Distribuciones Weibull por componente (ISO 14224 simplificado)
- Estacionalidad (lluvias en sierra peruana: dic-mar)
- Correlaciones: equipos más viejos → más fallas, más costo
- Operación 24/7 con turnos día/noche
- 3 años de data (2023-2025)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta, time
import random
import os

# Semilla para reproducibilidad
np.random.seed(42)
random.seed(42)

OUTPUT_DIR = "/home/claude/output_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# CONFIGURACIÓN GLOBAL
# ============================================================

FECHA_INICIO = datetime(2023, 1, 1)
FECHA_FIN = datetime(2025, 12, 31)
DIAS_TOTALES = (FECHA_FIN - FECHA_INICIO).days + 1

# ============================================================
# DIM_FECHA
# ============================================================

def generar_dim_fecha():
    print("Generando Dim_Fecha...")
    fechas = pd.date_range(FECHA_INICIO, FECHA_FIN, freq='D')

    meses_es = {
        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
        5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
        9: 'setiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
    }
    dias_es = {
        0: 'lunes', 1: 'martes', 2: 'miércoles', 3: 'jueves',
        4: 'viernes', 5: 'sábado', 6: 'domingo'
    }

    # Feriados peruanos recurrentes (aproximado)
    feriados_fijos = [
        (1, 1), (5, 1), (6, 29), (7, 28), (7, 29),
        (8, 30), (10, 8), (11, 1), (12, 8), (12, 25)
    ]

    def es_feriado(fecha):
        return (fecha.month, fecha.day) in feriados_fijos

    def temporada(fecha):
        # Hemisferio sur + contexto minero peruano
        m = fecha.month
        if m in [12, 1, 2, 3]:
            return 'Lluvias'
        elif m in [4, 5]:
            return 'Otoño'
        elif m in [6, 7, 8]:
            return 'Invierno seco'
        else:
            return 'Primavera'

    df = pd.DataFrame({
        'Fecha': fechas,
        'Anio': fechas.year,
        'Mes': fechas.month,
        'NombreMes': [meses_es[m] for m in fechas.month],
        'Trimestre': fechas.quarter,
        'Semana': fechas.isocalendar().week,
        'Dia': fechas.day,
        'NombreDia': [dias_es[d] for d in fechas.dayofweek],
        'EsFinDeSemana': fechas.dayofweek >= 5,
        'AnioMes': fechas.strftime('%Y-%m'),
        'EsFeriadoPE': [es_feriado(f) for f in fechas],
        'Temporada': [temporada(f) for f in fechas],
    })

    df.to_csv(f"{OUTPUT_DIR}/Dim_Fecha.csv", index=False)
    print(f"  ✓ {len(df)} fechas generadas")
    return df


# ============================================================
# DIM_EQUIPO
# ============================================================

def generar_dim_equipo():
    print("Generando Dim_Equipo...")

    # Catálogo realista de equipos mineros
    # Formato: (tipo, modelo, marca, costo_hora_op_usd, costo_hora_parada_usd, horas_nominales_anuales)
    catalogo = [
        ('Camión',      'CAT 797F',            'Caterpillar', 280,  1800, 7500),
        ('Camión',      'CAT 793F',            'Caterpillar', 240,  1500, 7500),
        ('Camión',      'Komatsu 930E',        'Komatsu',     260,  1700, 7500),
        ('Pala',        'CAT 6060',            'Caterpillar', 850,  5200, 7000),
        ('Pala',        'Komatsu PC8000',      'Komatsu',     780,  4800, 7000),
        ('Pala',        'Liebherr R9800',      'Liebherr',    820,  5000, 7000),
        ('Perforadora', '320XPC P&H',          'Komatsu',     420,  2600, 6800),
        ('Perforadora', 'Pit Viper 271',       'Epiroc',      380,  2400, 6800),
        ('Perforadora', 'DM45',                'Epiroc',      350,  2200, 6800),
    ]

    equipos = []
    equipo_id = 1
    # Multiplicamos para tener ~18 equipos (varios del mismo modelo)
    multiplicadores = {'Camión': 3, 'Pala': 2, 'Perforadora': 2}

    # Nombres peruanos para area/zona
    zonas = ['Tajo Norte', 'Tajo Sur', 'Tajo Central']

    for tipo, modelo, marca, costo_op, costo_parada, horas_nom in catalogo:
        n_copias = multiplicadores[tipo]
        for i in range(n_copias):
            anio_fab = np.random.choice(range(2014, 2023), p=[0.05, 0.08, 0.10, 0.12, 0.15, 0.15, 0.15, 0.12, 0.08])
            edad = 2025 - anio_fab

            # Criticidad basada en tipo
            if tipo == 'Pala':
                criticidad = 'Alta'
            elif tipo == 'Camión':
                criticidad = np.random.choice(['Alta', 'Media'], p=[0.4, 0.6])
            else:
                criticidad = np.random.choice(['Alta', 'Media'], p=[0.3, 0.7])

            codigo_prefix = {'Camión': 'CAM', 'Pala': 'PAL', 'Perforadora': 'PER'}[tipo]
            codigo = f"{codigo_prefix}-{equipo_id:03d}"

            equipos.append({
                'Equipo_ID': equipo_id,
                'Codigo_Equipo': codigo,
                'Tipo_Equipo': tipo,
                'Modelo': modelo,
                'Marca': marca,
                'Anio_Fabricacion': anio_fab,
                'Edad_Anios': edad,
                'Horas_Nominales_Anuales': horas_nom,
                'Costo_Hora_Operacion_USD': costo_op + np.random.randint(-20, 20),
                'Costo_Hora_Parada_USD': costo_parada + np.random.randint(-100, 100),
                'Criticidad': criticidad,
                'Zona': np.random.choice(zonas),
                'Area': 'Mina',
                'Estado_Actual': np.random.choice(['Operativo', 'En Mantenimiento'], p=[0.92, 0.08])
            })
            equipo_id += 1

    df = pd.DataFrame(equipos)
    df.to_csv(f"{OUTPUT_DIR}/Dim_Equipo.csv", index=False)
    print(f"  ✓ {len(df)} equipos generados ({df['Tipo_Equipo'].value_counts().to_dict()})")
    return df


# ============================================================
# DIM_COMPONENTE (ISO 14224 simplificado)
# ============================================================

def generar_dim_componente():
    print("Generando Dim_Componente...")

    # (Sistema, Subsistema, Componente, Tipo_Aplicable, Beta_Weibull, Eta_Weibull_hrs, Costo_Repuesto_USD_promedio)
    # Beta < 1: infantil | Beta = 1: aleatorio | Beta > 1: desgaste
    componentes = [
        # Motor Diesel (desgaste claro)
        ('Motor Diesel', 'Bloque motor',    'Pistones',              'Todos',       2.3, 4500, 8500),
        ('Motor Diesel', 'Bloque motor',    'Cigüeñal',              'Todos',       2.5, 6000, 12000),
        ('Motor Diesel', 'Alimentación',    'Inyectores',            'Todos',       1.8, 3500, 2200),
        ('Motor Diesel', 'Lubricación',     'Bomba de aceite',       'Todos',       2.0, 4200, 1800),
        ('Motor Diesel', 'Refrigeración',   'Radiador',              'Todos',       1.5, 3800, 3500),
        ('Motor Diesel', 'Turbo',           'Turbocompresor',        'Todos',       2.1, 4000, 6500),

        # Sistema Eléctrico (más aleatorio)
        ('Sistema Eléctrico', 'Generación', 'Alternador',            'Todos',       1.2, 2800, 2500),
        ('Sistema Eléctrico', 'Almacenaje', 'Baterías',              'Todos',       2.8, 2200, 800),
        ('Sistema Eléctrico', 'Distribución','Cableado principal',   'Todos',       1.1, 3500, 1200),
        ('Sistema Eléctrico', 'Control',    'PLC/ECU',               'Todos',       1.0, 4000, 4500),
        ('Sistema Eléctrico', 'Motores',    'Motor eléctrico tracción','Pala',      1.4, 5500, 15000),

        # Sistema Hidráulico
        ('Sistema Hidráulico', 'Potencia',   'Bomba hidráulica principal','Todos',  1.9, 3800, 7500),
        ('Sistema Hidráulico', 'Actuadores', 'Cilindros hidráulicos','Todos',       2.0, 4200, 3800),
        ('Sistema Hidráulico', 'Mangueras',  'Mangueras alta presión','Todos',      1.6, 2500, 450),
        ('Sistema Hidráulico', 'Válvulas',   'Válvulas de control',   'Todos',      1.7, 3200, 2100),
        ('Sistema Hidráulico', 'Filtrado',   'Filtros hidráulicos',   'Todos',      3.0, 1500, 280),

        # Transmisión / Tren de potencia
        ('Transmisión', 'Caja',      'Caja de cambios',      'Camión',      2.1, 4500, 18000),
        ('Transmisión', 'Diferencial','Diferencial',         'Camión',      2.2, 5000, 12000),
        ('Transmisión', 'Convertidor','Convertidor de par',  'Camión',      1.9, 4200, 9500),

        # Frenos (desgaste fuerte)
        ('Sistema de Frenos', 'Servicio',  'Pastillas de freno',  'Camión',       3.2, 2200, 650),
        ('Sistema de Frenos', 'Servicio',  'Discos de freno',     'Camión',       2.8, 3500, 1800),
        ('Sistema de Frenos', 'Retardo',   'Retardador',          'Camión',       2.0, 4000, 5500),

        # Neumáticos (desgaste muy claro)
        ('Neumáticos',  'OTR',      'Neumático delantero',  'Camión',      3.5, 4500, 28000),
        ('Neumáticos',  'OTR',      'Neumático trasero',    'Camión',      3.3, 4000, 28000),

        # Estructura
        ('Estructura',  'Chasis',   'Chasis principal',     'Todos',       1.8, 9000, 25000),
        ('Estructura',  'Tolva',    'Tolva',                'Camión',      2.0, 7500, 18000),
        ('Estructura',  'Orugas',   'Cadenas de oruga',     'Pala',        2.7, 5000, 35000),
        ('Estructura',  'Orugas',   'Rodillos',             'Pala',        2.4, 4500, 2800),

        # Implementos específicos
        ('Implemento',  'Excavación','Cucharón',            'Pala',        2.5, 3500, 45000),
        ('Implemento',  'Excavación','Dientes de cucharón', 'Pala',        3.8, 1200, 1800),
        ('Implemento',  'Perforación','Broca',              'Perforadora', 2.9, 1800, 4500),
        ('Implemento',  'Perforación','Torre',              'Perforadora', 1.7, 6000, 22000),
        ('Implemento',  'Perforación','Martillo',           'Perforadora', 2.3, 3500, 8500),
        ('Implemento',  'Perforación','Compresor de aire',  'Perforadora', 2.0, 4000, 6500),

        # Otros
        ('Cabina',      'Confort',  'Aire acondicionado',   'Todos',       1.3, 3500, 1800),
        ('Cabina',      'Operador', 'Asiento',              'Todos',       1.8, 6000, 2200),
    ]

    df = pd.DataFrame(componentes, columns=[
        'Sistema', 'Subsistema', 'Componente', 'Tipo_Equipo_Aplicable',
        'Beta_Weibull', 'Eta_Weibull_Hrs', 'Costo_Repuesto_Promedio_USD'
    ])
    df.insert(0, 'Componente_ID', range(1, len(df) + 1))

    df.to_csv(f"{OUTPUT_DIR}/Dim_Componente.csv", index=False)
    print(f"  ✓ {len(df)} componentes generados ({df['Sistema'].nunique()} sistemas)")
    return df


# ============================================================
# DIM_CAUSA_RAIZ
# ============================================================

def generar_dim_causa_raiz():
    print("Generando Dim_CausaRaiz...")

    causas = [
        ('Humano',         'Error de operación',               'Operación fuera de parámetros por el operador'),
        ('Humano',         'Error humano',                     'Error no intencional del personal'),
        ('Humano',         'Error de montaje',                 'Instalación incorrecta en mantenimiento anterior'),
        ('Material',       'Fatiga de material',               'Desgaste normal del material'),
        ('Material',       'Defecto de fabricación',           'Material defectuoso desde origen'),
        ('Material',       'Repuestos no originales',          'Uso de repuestos no OEM'),
        ('Diseño',         'Subdimensionamiento',              'Componente insuficiente para la carga'),
        ('Operación',      'Sobrecarga de trabajo',            'Operación por encima de la capacidad nominal'),
        ('Operación',      'Uso intensivo',                    'Horas de operación superiores a la planificación'),
        ('Operación',      'Condiciones extremas de terreno',  'Operación en terreno más agresivo de lo normal'),
        ('Operación',      'Condiciones climáticas',           'Lluvias, temperaturas extremas, polvo'),
        ('Mantenimiento',  'Falta de mantenimiento preventivo','Incumplimiento del plan preventivo'),
        ('Mantenimiento',  'Mantenimiento deficiente',         'Mantenimiento ejecutado sin calidad'),
        ('Mantenimiento',  'Deficiencia en inspección',        'Falla no detectada durante inspección'),
        ('Externo',        'Contaminación de fluidos',         'Contaminación de aceite, combustible o refrigerante'),
        ('Externo',        'Impacto/Colisión',                 'Daño por impacto externo'),
    ]

    df = pd.DataFrame(causas, columns=['Categoria_Causa', 'Causa_Raiz', 'Descripcion'])
    df.insert(0, 'CausaRaiz_ID', range(1, len(df) + 1))

    df.to_csv(f"{OUTPUT_DIR}/Dim_CausaRaiz.csv", index=False)
    print(f"  ✓ {len(df)} causas raíz")
    return df


# ============================================================
# DIM_ACTIVIDAD
# ============================================================

def generar_dim_actividad():
    print("Generando Dim_Actividad...")

    # (Tipo, Nombre, Duracion_Est_Hrs, Costo_Est_USD)
    actividades = [
        # Preventivas
        ('Preventiva',  'Cambio de aceite',             4,   1200),
        ('Preventiva',  'Cambio de filtros',            3,   800),
        ('Preventiva',  'Inspección general',           5,   500),
        ('Preventiva',  'Engrase general',              2,   300),
        ('Preventiva',  'Ajuste de frenos',             4,   900),
        ('Preventiva',  'Revisión sistema hidráulico',  6,   1500),
        ('Preventiva',  'Revisión sistema eléctrico',   5,   1100),
        # Predictivas
        ('Predictiva',  'Análisis de aceite',           2,   400),
        ('Predictiva',  'Termografía',                  3,   600),
        ('Predictiva',  'Análisis de vibraciones',      3,   700),
        ('Predictiva',  'Inspección con ultrasonido',   4,   900),
        # Correctivas (se derivan de la falla)
        ('Correctiva',  'Reparación por falla',         8,   3500),
        ('Correctiva',  'Reemplazo de componente',      10,  8500),
        ('Correctiva',  'Ajuste por falla menor',       3,   1200),
        # Mayor / Overhaul
        ('Mayor',       'Overhaul de motor',            80,  85000),
        ('Mayor',       'Overhaul de transmisión',      60,  55000),
        ('Mayor',       'Reconstrucción de cucharón',   40,  35000),
        ('Mayor',       'Mantenimiento mayor 10K hrs',  120, 150000),
        # Inspección
        ('Inspección',  'Inspección pre-turno',         0.5, 80),
        ('Inspección',  'Inspección semanal',           2,   300),
    ]

    df = pd.DataFrame(actividades, columns=[
        'Tipo_Actividad', 'Nombre_Actividad',
        'Duracion_Estimada_Hrs', 'Costo_Estimado_USD'
    ])
    df.insert(0, 'Actividad_ID', range(1, len(df) + 1))

    df.to_csv(f"{OUTPUT_DIR}/Dim_Actividad.csv", index=False)
    print(f"  ✓ {len(df)} actividades")
    return df


# ============================================================
# DIM_MECANICO
# ============================================================

def generar_dim_mecanico():
    print("Generando Dim_Mecanico...")

    nombres_pe = [
        'Carlos Quispe Mamani', 'José Huamán Roque', 'Luis Condori Flores',
        'Miguel Rojas Palomino', 'Jorge Vilca Chávez', 'Pedro Apaza Coaquira',
        'Juan Ccahuana Huanca', 'Víctor Chambi Mendoza', 'Raúl Salcedo Puma',
        'Andrés Mamani Laura', 'César Ticona Gutiérrez', 'Fernando Cárdenas Ríos',
        'Martín Quintana Soto', 'Alberto Cuba Villena', 'Óscar Pacheco Mejía',
        'Rodrigo Zapata Núñez', 'Daniel Barrientos Tejada', 'Iván Flores Ayala',
        'Javier Paredes Salas', 'Ernesto Loayza Vera', 'Nilton Espinoza Romero',
        'Walter Aguirre Cáceres', 'Hugo Portocarrero Díaz', 'Manuel Zevallos Cruz',
        'Ricardo Atoche Montoya',
    ]

    mecanicos = []
    for i, nombre in enumerate(nombres_pe, 1):
        especialidad = np.random.choice(
            ['Mecánica', 'Eléctrica', 'Hidráulica', 'Soldadura', 'Multipropósito'],
            p=[0.35, 0.20, 0.20, 0.10, 0.15]
        )
        nivel = np.random.choice(
            ['Junior', 'Semi-Senior', 'Senior', 'Supervisor'],
            p=[0.25, 0.35, 0.30, 0.10]
        )
        turno = np.random.choice(['Día', 'Noche', 'Rotativo'], p=[0.45, 0.35, 0.20])

        costo_hora = {'Junior': 15, 'Semi-Senior': 22, 'Senior': 32, 'Supervisor': 45}[nivel]
        costo_hora += np.random.randint(-3, 4)

        antig = {'Junior': np.random.randint(1,4),
                 'Semi-Senior': np.random.randint(3,8),
                 'Senior': np.random.randint(7,15),
                 'Supervisor': np.random.randint(10,22)}[nivel]

        mecanicos.append({
            'Mecanico_ID': i,
            'Nombre_Completo': nombre,
            'Especialidad': especialidad,
            'Nivel': nivel,
            'Turno_Habitual': turno,
            'Antiguedad_Anios': antig,
            'Costo_Hora_USD': costo_hora,
        })

    df = pd.DataFrame(mecanicos)
    df.to_csv(f"{OUTPUT_DIR}/Dim_Mecanico.csv", index=False)
    print(f"  ✓ {len(df)} mecánicos")
    return df


# ============================================================
# DIM_TURNO
# ============================================================

def generar_dim_turno():
    print("Generando Dim_Turno...")
    df = pd.DataFrame([
        {'Turno_ID': 1, 'Nombre_Turno': 'Día',   'Hora_Inicio': '07:00', 'Hora_Fin': '19:00'},
        {'Turno_ID': 2, 'Nombre_Turno': 'Noche', 'Hora_Inicio': '19:00', 'Hora_Fin': '07:00'},
    ])
    df.to_csv(f"{OUTPUT_DIR}/Dim_Turno.csv", index=False)
    print(f"  ✓ {len(df)} turnos")
    return df


# ============================================================
# FACT_EVENTOS_OPERACION
# Simula día a día por equipo qué estaba haciendo
# ============================================================

def generar_fact_eventos(dim_equipo, dim_fecha):
    print("Generando Fact_Eventos_Operacion (esto toma ~15s)...")

    eventos = []
    evento_id = 1

    tipos_evento = ['Operativo', 'Standby', 'Parada no planificada', 'Mantenimiento programado']
    causas_parada = {
        'Operativo': ['-'],
        'Standby': ['Sin carga', 'Cambio de turno', 'Refrigerio operador', 'Espera de operador'],
        'Parada no planificada': ['Falla mecánica', 'Falla eléctrica', 'Falla hidráulica',
                                   'Falta de operador', 'Clima adverso', 'Falta de combustible'],
        'Mantenimiento programado': ['Preventivo programado', 'Inspección', 'Cambio de aceite',
                                      'Mantenimiento mayor']
    }

    for _, equipo in dim_equipo.iterrows():
        eq_id = equipo['Equipo_ID']
        edad = equipo['Edad_Anios']
        tipo = equipo['Tipo_Equipo']

        # Factor de disponibilidad por edad (equipos viejos menos disponibles)
        factor_disp = max(0.70, 0.92 - (edad - 3) * 0.015)

        # Probabilidades base por tipo de evento (ajustadas por edad)
        p_operativo = factor_disp * 0.85
        p_standby = 0.08
        p_parada = (1 - factor_disp) * 0.6 + 0.03
        p_mant = 1 - p_operativo - p_standby - p_parada
        probs = np.array([p_operativo, p_standby, p_parada, max(0.01, p_mant)])
        probs = probs / probs.sum()

        # Generar eventos día a día (para eficiencia, un evento por turno de 12 hrs)
        for _, fila_fecha in dim_fecha.iterrows():
            fecha = fila_fecha['Fecha']

            # Ajuste estacional: en lluvias más paradas no planificadas
            probs_ajust = probs.copy()
            if fila_fecha['Temporada'] == 'Lluvias':
                probs_ajust[2] *= 1.4  # más paradas
                probs_ajust[0] *= 0.95
                probs_ajust = probs_ajust / probs_ajust.sum()

            # Cada día se divide en eventos. Para simplificar: 2-4 eventos por día
            n_eventos_dia = np.random.choice([2, 3, 4], p=[0.3, 0.5, 0.2])
            horas_restantes = 24.0
            hora_actual = 0.0

            for i in range(n_eventos_dia):
                if horas_restantes <= 0.5:
                    break

                tipo_evt = np.random.choice(tipos_evento, p=probs_ajust)

                # Duración del evento
                if tipo_evt == 'Operativo':
                    dur = np.random.uniform(4, min(12, horas_restantes))
                elif tipo_evt == 'Standby':
                    dur = np.random.uniform(0.5, min(3, horas_restantes))
                elif tipo_evt == 'Parada no planificada':
                    dur = np.random.uniform(1, min(8, horas_restantes))
                else:  # Mantenimiento programado
                    dur = np.random.uniform(2, min(10, horas_restantes))

                if i == n_eventos_dia - 1:  # último del día, consume lo que queda
                    dur = horas_restantes

                causa = np.random.choice(causas_parada[tipo_evt])

                fecha_inicio = fecha + timedelta(hours=hora_actual)
                fecha_fin = fecha_inicio + timedelta(hours=dur)

                turno_id = 1 if hora_actual < 12 else 2

                eventos.append({
                    'Evento_ID': evento_id,
                    'Equipo_ID': eq_id,
                    'Fecha': fecha.date(),
                    'Turno_ID': turno_id,
                    'Fecha_Hora_Inicio': fecha_inicio,
                    'Fecha_Hora_Fin': fecha_fin,
                    'Tipo_Evento': tipo_evt,
                    'Causa_Parada': causa,
                    'Horas_Evento': round(dur, 2),
                })
                evento_id += 1
                hora_actual += dur
                horas_restantes -= dur

    df = pd.DataFrame(eventos)
    df.to_csv(f"{OUTPUT_DIR}/Fact_Eventos_Operacion.csv", index=False)
    print(f"  ✓ {len(df):,} eventos generados")
    return df


# ============================================================
# FACT_FALLAS
# Usa Weibull por componente para generar fallas realistas
# ============================================================

def generar_fact_fallas(dim_equipo, dim_componente, dim_causa, dim_fecha):
    print("Generando Fact_Fallas (basado en Weibull por componente)...")

    fallas = []
    falla_id = 1

    # Mapeo de componente → modos de falla típicos
    modos_falla_por_sistema = {
        'Motor Diesel':        ['Recalentamiento', 'Pérdida de potencia', 'Fuga de aceite',
                                'Vibraciones excesivas', 'Ruido anormal'],
        'Sistema Eléctrico':   ['Cortocircuito', 'Falla eléctrica', 'Pérdida de señal',
                                'Sobrecarga', 'Falla de arranque'],
        'Sistema Hidráulico':  ['Fuga hidráulica', 'Pérdida de presión', 'Recalentamiento aceite',
                                'Vibraciones excesivas', 'Rotura de cilindro'],
        'Transmisión':         ['Fallo transmisión', 'Desgaste de engranajes',
                                'Recalentamiento', 'Ruido anormal', 'Patinamiento'],
        'Sistema de Frenos':   ['Falla de frenos', 'Desgaste excesivo', 'Fuga de fluido',
                                'Vibración al frenar'],
        'Neumáticos':          ['Desgaste prematuro', 'Pinchadura', 'Fatiga estructural',
                                'Desbalance'],
        'Estructura':          ['Fatiga estructural', 'Fatiga en orugas', 'Fisura',
                                'Deformación'],
        'Implemento':          ['Desgaste de broca', 'Fractura de diente', 'Desgaste cuchara',
                                'Fatiga de material', 'Rotura'],
        'Cabina':              ['Falla de A/C', 'Falla de controles', 'Falla de pantalla'],
    }

    for _, equipo in dim_equipo.iterrows():
        eq_id = equipo['Equipo_ID']
        tipo_eq = equipo['Tipo_Equipo']
        edad = equipo['Edad_Anios']

        # Filtrar componentes aplicables a este tipo de equipo
        comp_aplica = dim_componente[
            (dim_componente['Tipo_Equipo_Aplicable'] == tipo_eq) |
            (dim_componente['Tipo_Equipo_Aplicable'] == 'Todos')
        ].copy()

        # Factor de deterioro por edad: equipo más viejo = eta más bajo = fallas más frecuentes
        factor_edad = max(0.6, 1.0 - (edad - 5) * 0.04)

        # Para cada componente, simular fallas durante los 3 años
        horas_operativas_totales = DIAS_TOTALES * 16  # ~16 hrs operativas promedio/día

        for _, comp in comp_aplica.iterrows():
            beta = comp['Beta_Weibull']
            eta = comp['Eta_Weibull_Hrs'] * factor_edad
            comp_id = comp['Componente_ID']
            sistema = comp['Sistema']
            modos = modos_falla_por_sistema.get(sistema, ['Falla general'])

            # Simular tiempos entre fallas con Weibull
            # Método: generar samples hasta exceder horas_operativas_totales
            horas_acumuladas = 0
            while horas_acumuladas < horas_operativas_totales:
                # Weibull sample
                u = np.random.random()
                ttf = eta * (-np.log(1 - u)) ** (1/beta)  # tiempo hasta falla
                horas_acumuladas += ttf

                if horas_acumuladas >= horas_operativas_totales:
                    break

                # Convertir horas operativas a fecha calendario
                dia_calendario = int(horas_acumuladas / 16)
                if dia_calendario >= DIAS_TOTALES:
                    break

                fecha_falla = FECHA_INICIO + timedelta(days=dia_calendario)

                # Hora del día (aleatoria)
                hora = np.random.randint(0, 24)
                minuto = np.random.randint(0, 60)
                fecha_hora_falla = fecha_falla.replace(hour=hora, minute=minuto)

                # Ajuste estacional: en lluvias más fallas relacionadas a clima
                mes = fecha_falla.month
                # En meses no-lluvia, reducir probabilidad de fallas eléctricas/motor (filtro positivo)
                if mes not in [12, 1, 2, 3] and sistema in ['Sistema Eléctrico', 'Motor Diesel']:
                    if np.random.random() < 0.25:
                        continue  # descarta 25% de estas fallas fuera de lluvias

                # Severidad: depende del componente y algo aleatorio
                # Componentes caros/críticos → más probabilidad de Alta/Crítica
                costo_repuesto = comp['Costo_Repuesto_Promedio_USD']
                if costo_repuesto > 20000:
                    severidad = np.random.choice(['Media', 'Alta', 'Crítica'], p=[0.3, 0.5, 0.2])
                elif costo_repuesto > 5000:
                    severidad = np.random.choice(['Baja', 'Media', 'Alta', 'Crítica'], p=[0.15, 0.45, 0.30, 0.10])
                else:
                    severidad = np.random.choice(['Baja', 'Media', 'Alta'], p=[0.40, 0.45, 0.15])

                # Horas de parada: según severidad + componente
                base_parada = {'Baja': 2, 'Media': 6, 'Alta': 16, 'Crítica': 48}[severidad]
                horas_parada = base_parada * np.random.uniform(0.7, 1.5)

                # Causa raíz según sistema
                if sistema == 'Motor Diesel' and severidad in ['Alta', 'Crítica']:
                    causa_ids = dim_causa[dim_causa['Categoria_Causa'].isin(['Material', 'Mantenimiento'])]['CausaRaiz_ID'].values
                elif sistema == 'Neumáticos':
                    causa_ids = dim_causa[dim_causa['Categoria_Causa'].isin(['Operación', 'Material'])]['CausaRaiz_ID'].values
                elif mes in [12, 1, 2, 3]:
                    causa_ids = dim_causa[dim_causa['Causa_Raiz'].isin(['Condiciones climáticas', 'Condiciones extremas de terreno'])]['CausaRaiz_ID'].values
                    if len(causa_ids) == 0:
                        causa_ids = dim_causa['CausaRaiz_ID'].values
                else:
                    causa_ids = dim_causa['CausaRaiz_ID'].values

                causa_id = np.random.choice(causa_ids)
                modo = np.random.choice(modos)
                detectada = np.random.choice(['Operador', 'Inspección', 'Monitoreo remoto'],
                                             p=[0.55, 0.30, 0.15])
                turno_id = 1 if 7 <= hora < 19 else 2

                fallas.append({
                    'Falla_ID': falla_id,
                    'Equipo_ID': eq_id,
                    'Componente_ID': comp_id,
                    'CausaRaiz_ID': causa_id,
                    'Turno_ID': turno_id,
                    'Fecha': fecha_falla.date(),
                    'Fecha_Hora_Falla': fecha_hora_falla,
                    'Modo_Falla': modo,
                    'Severidad': severidad,
                    'Horas_Parada_Equipo': round(horas_parada, 2),
                    'Detectada_Por': detectada,
                })
                falla_id += 1

    df = pd.DataFrame(fallas)
    df = df.sort_values('Fecha_Hora_Falla').reset_index(drop=True)
    df['Falla_ID'] = range(1, len(df) + 1)
    df.to_csv(f"{OUTPUT_DIR}/Fact_Fallas.csv", index=False)
    print(f"  ✓ {len(df):,} fallas generadas")
    print(f"    Severidad: {df['Severidad'].value_counts().to_dict()}")
    return df


# ============================================================
# FACT_OT (unifica correctivos, preventivos, predictivos, mayores)
# ============================================================

def generar_fact_ot(dim_equipo, dim_actividad, dim_mecanico, dim_componente,
                     fact_fallas):
    print("Generando Fact_OT (correctivos + preventivos + predictivos + mayores)...")

    ots = []
    ot_id = 1

    # === 1. OTs Correctivas: una por cada falla ===
    # (algunas fallas menores no generan OT, son reparación inmediata)
    actividades_correctivas = dim_actividad[dim_actividad['Tipo_Actividad'] == 'Correctiva']
    mecanicos_ids = dim_mecanico['Mecanico_ID'].values
    costos_mano_obra = dim_mecanico.set_index('Mecanico_ID')['Costo_Hora_USD'].to_dict()

    for _, falla in fact_fallas.iterrows():
        # Fallas Baja a veces no generan OT
        if falla['Severidad'] == 'Baja' and np.random.random() < 0.3:
            continue

        # Seleccionar actividad correctiva según severidad
        if falla['Severidad'] == 'Crítica':
            actividad = actividades_correctivas[actividades_correctivas['Nombre_Actividad'] == 'Reemplazo de componente'].iloc[0]
        elif falla['Severidad'] == 'Alta':
            actividad = actividades_correctivas.sample(1, weights=[1, 3, 1][:len(actividades_correctivas)] if len(actividades_correctivas)==3 else None).iloc[0]
        else:
            actividad = actividades_correctivas[actividades_correctivas['Nombre_Actividad'] == 'Ajuste por falla menor'].iloc[0] if (actividades_correctivas['Nombre_Actividad'] == 'Ajuste por falla menor').any() else actividades_correctivas.iloc[0]

        # Fecha de ingreso: entre 0 y 24 hrs después de la falla
        delay_hrs = np.random.exponential(6)  # cola larga, la mayoría rápido
        fecha_ingreso = pd.Timestamp(falla['Fecha_Hora_Falla']) + timedelta(hours=delay_hrs)

        # Duración real (puede variar de la estimada)
        dur_est = actividad['Duracion_Estimada_Hrs']
        dur_real = dur_est * np.random.uniform(0.7, 1.8)  # a veces rápido, a veces demora
        fecha_salida = fecha_ingreso + timedelta(hours=dur_real)

        # Mecánicos asignados
        n_mec = np.random.choice([1, 2, 3, 4], p=[0.2, 0.4, 0.3, 0.1])
        mec_lider = np.random.choice(mecanicos_ids)

        horas_hombre = dur_real * n_mec
        costo_mo = horas_hombre * costos_mano_obra[mec_lider] * np.random.uniform(0.9, 1.1)

        # Costo repuestos: relacionado al componente
        comp = dim_componente[dim_componente['Componente_ID'] == falla['Componente_ID']].iloc[0]
        costo_base = comp['Costo_Repuesto_Promedio_USD']
        factor_sev = {'Baja': 0.15, 'Media': 0.4, 'Alta': 0.75, 'Crítica': 1.0}[falla['Severidad']]
        costo_rep = costo_base * factor_sev * np.random.uniform(0.8, 1.2)

        # Estado: mayoría cerradas, algunas abiertas si son recientes
        if fecha_salida > datetime(2025, 11, 1):
            estado = np.random.choice(['Abierta', 'En Proceso', 'Cerrada'], p=[0.3, 0.3, 0.4])
        else:
            estado = np.random.choice(['Cerrada', 'Cancelada'], p=[0.95, 0.05])

        cumple_plazo = dur_real <= dur_est * 1.15

        ots.append({
            'OT_ID': ot_id,
            'Equipo_ID': falla['Equipo_ID'],
            'Falla_ID': falla['Falla_ID'],
            'Actividad_ID': actividad['Actividad_ID'],
            'Mecanico_Lider_ID': int(mec_lider),
            'Fecha_Ingreso': fecha_ingreso,
            'Fecha_Salida': fecha_salida,
            'Tipo_OT': 'Correctivo',
            'Estado_OT': estado,
            'Horas_Taller': round(dur_real, 2),
            'Horas_Planificadas': dur_est,
            'Num_Mecanicos': n_mec,
            'Horas_Hombre': round(horas_hombre, 2),
            'Costo_ManoObra_USD': round(costo_mo, 2),
            'Costo_Repuestos_USD': round(costo_rep, 2),
            'Costo_Total_USD': round(costo_mo + costo_rep, 2),
            'Cumple_Plazo': cumple_plazo,
        })
        ot_id += 1

    # === 2. OTs Preventivas: plan estructurado por equipo ===
    actividades_pm = dim_actividad[dim_actividad['Tipo_Actividad'] == 'Preventiva']

    for _, equipo in dim_equipo.iterrows():
        # Cada equipo: ~1 preventivo cada 250 horas operativas = ~11 al año
        n_pm_anual = 11
        for anio in [2023, 2024, 2025]:
            for i in range(n_pm_anual):
                dia_del_anio = int((i + 0.5) * (365 / n_pm_anual)) + np.random.randint(-5, 6)
                try:
                    fecha_ingreso = datetime(anio, 1, 1) + timedelta(days=dia_del_anio)
                except:
                    continue
                if fecha_ingreso > FECHA_FIN:
                    continue

                actividad = actividades_pm.sample(1).iloc[0]
                dur_est = actividad['Duracion_Estimada_Hrs']
                dur_real = dur_est * np.random.uniform(0.85, 1.15)
                fecha_salida = fecha_ingreso + timedelta(hours=dur_real)

                n_mec = np.random.choice([1, 2, 3], p=[0.3, 0.5, 0.2])
                mec_lider = np.random.choice(mecanicos_ids)
                horas_hombre = dur_real * n_mec
                costo_mo = horas_hombre * costos_mano_obra[mec_lider]
                costo_rep = actividad['Costo_Estimado_USD'] * 0.7 * np.random.uniform(0.8, 1.2)

                # Estado preventivos: casi todos cerrados
                estado = np.random.choice(['Cerrada', 'Cancelada', 'Abierta'], p=[0.90, 0.07, 0.03])

                ots.append({
                    'OT_ID': ot_id,
                    'Equipo_ID': equipo['Equipo_ID'],
                    'Falla_ID': None,
                    'Actividad_ID': actividad['Actividad_ID'],
                    'Mecanico_Lider_ID': int(mec_lider),
                    'Fecha_Ingreso': fecha_ingreso,
                    'Fecha_Salida': fecha_salida,
                    'Tipo_OT': 'Preventivo',
                    'Estado_OT': estado,
                    'Horas_Taller': round(dur_real, 2),
                    'Horas_Planificadas': dur_est,
                    'Num_Mecanicos': n_mec,
                    'Horas_Hombre': round(horas_hombre, 2),
                    'Costo_ManoObra_USD': round(costo_mo, 2),
                    'Costo_Repuestos_USD': round(costo_rep, 2),
                    'Costo_Total_USD': round(costo_mo + costo_rep, 2),
                    'Cumple_Plazo': dur_real <= dur_est * 1.1,
                })
                ot_id += 1

    # === 3. OTs Predictivas: menos frecuentes ===
    actividades_pred = dim_actividad[dim_actividad['Tipo_Actividad'] == 'Predictiva']
    for _, equipo in dim_equipo.iterrows():
        n_pred_anual = 6
        for anio in [2023, 2024, 2025]:
            for i in range(n_pred_anual):
                dia = int((i + 0.5) * (365 / n_pred_anual)) + np.random.randint(-10, 10)
                fecha_ingreso = datetime(anio, 1, 1) + timedelta(days=dia)
                if fecha_ingreso > FECHA_FIN or fecha_ingreso < FECHA_INICIO:
                    continue

                actividad = actividades_pred.sample(1).iloc[0]
                dur_est = actividad['Duracion_Estimada_Hrs']
                dur_real = dur_est * np.random.uniform(0.9, 1.2)
                fecha_salida = fecha_ingreso + timedelta(hours=dur_real)

                n_mec = np.random.choice([1, 2], p=[0.6, 0.4])
                mec_lider = np.random.choice(mecanicos_ids)
                horas_hombre = dur_real * n_mec
                costo_mo = horas_hombre * costos_mano_obra[mec_lider]
                costo_rep = actividad['Costo_Estimado_USD'] * 0.3 * np.random.uniform(0.8, 1.2)

                estado = np.random.choice(['Cerrada', 'Cancelada'], p=[0.93, 0.07])

                ots.append({
                    'OT_ID': ot_id,
                    'Equipo_ID': equipo['Equipo_ID'],
                    'Falla_ID': None,
                    'Actividad_ID': actividad['Actividad_ID'],
                    'Mecanico_Lider_ID': int(mec_lider),
                    'Fecha_Ingreso': fecha_ingreso,
                    'Fecha_Salida': fecha_salida,
                    'Tipo_OT': 'Predictivo',
                    'Estado_OT': estado,
                    'Horas_Taller': round(dur_real, 2),
                    'Horas_Planificadas': dur_est,
                    'Num_Mecanicos': n_mec,
                    'Horas_Hombre': round(horas_hombre, 2),
                    'Costo_ManoObra_USD': round(costo_mo, 2),
                    'Costo_Repuestos_USD': round(costo_rep, 2),
                    'Costo_Total_USD': round(costo_mo + costo_rep, 2),
                    'Cumple_Plazo': dur_real <= dur_est * 1.15,
                })
                ot_id += 1

    # === 4. OTs Mayores: pocas pero costosas ===
    actividades_mayor = dim_actividad[dim_actividad['Tipo_Actividad'] == 'Mayor']
    for _, equipo in dim_equipo.iterrows():
        # 1-2 mayores por equipo en 3 años
        n_mayor = np.random.choice([1, 2], p=[0.6, 0.4])
        for _ in range(n_mayor):
            anio = np.random.choice([2023, 2024, 2025])
            dia = np.random.randint(1, 360)
            fecha_ingreso = datetime(anio, 1, 1) + timedelta(days=dia)

            actividad = actividades_mayor.sample(1).iloc[0]
            dur_est = actividad['Duracion_Estimada_Hrs']
            dur_real = dur_est * np.random.uniform(0.9, 1.3)
            fecha_salida = fecha_ingreso + timedelta(hours=dur_real)

            n_mec = np.random.choice([3, 4, 5, 6], p=[0.2, 0.4, 0.3, 0.1])
            mec_lider = np.random.choice(mecanicos_ids)
            horas_hombre = dur_real * n_mec
            costo_mo = horas_hombre * costos_mano_obra[mec_lider]
            costo_rep = actividad['Costo_Estimado_USD'] * 0.8 * np.random.uniform(0.85, 1.15)

            estado = np.random.choice(['Cerrada', 'En Proceso'], p=[0.85, 0.15])

            ots.append({
                'OT_ID': ot_id,
                'Equipo_ID': equipo['Equipo_ID'],
                'Falla_ID': None,
                'Actividad_ID': actividad['Actividad_ID'],
                'Mecanico_Lider_ID': int(mec_lider),
                'Fecha_Ingreso': fecha_ingreso,
                'Fecha_Salida': fecha_salida,
                'Tipo_OT': 'Mayor',
                'Estado_OT': estado,
                'Horas_Taller': round(dur_real, 2),
                'Horas_Planificadas': dur_est,
                'Num_Mecanicos': n_mec,
                'Horas_Hombre': round(horas_hombre, 2),
                'Costo_ManoObra_USD': round(costo_mo, 2),
                'Costo_Repuestos_USD': round(costo_rep, 2),
                'Costo_Total_USD': round(costo_mo + costo_rep, 2),
                'Cumple_Plazo': dur_real <= dur_est * 1.2,
            })
            ot_id += 1

    df = pd.DataFrame(ots).sort_values('Fecha_Ingreso').reset_index(drop=True)
    df['OT_ID'] = range(1, len(df) + 1)
    df.to_csv(f"{OUTPUT_DIR}/Fact_OT.csv", index=False)
    print(f"  ✓ {len(df):,} OTs generadas")
    print(f"    Por tipo: {df['Tipo_OT'].value_counts().to_dict()}")
    print(f"    Por estado: {df['Estado_OT'].value_counts().to_dict()}")
    return df


# ============================================================
# FACT_PLAN_MANTENIMIENTO
# ============================================================

def generar_fact_plan(dim_equipo, dim_actividad, fact_ot):
    print("Generando Fact_Plan_Mantenimiento...")

    planes = []
    plan_id = 1

    # Para cada OT preventiva/predictiva/mayor, generar un registro de plan
    # Más: agregar planes que NO se ejecutaron (cancelados, reprogramados, pendientes)
    ots_planificadas = fact_ot[fact_ot['Tipo_OT'].isin(['Preventivo', 'Predictivo', 'Mayor'])].copy()

    for _, ot in ots_planificadas.iterrows():
        # Fecha programada: típicamente un poco antes de la ejecución
        dias_adelanto = np.random.randint(0, 5)
        fecha_programada = pd.Timestamp(ot['Fecha_Ingreso']) - timedelta(days=dias_adelanto)

        if ot['Estado_OT'] == 'Cerrada':
            estado_plan = 'Ejecutado'
        elif ot['Estado_OT'] == 'Cancelada':
            estado_plan = 'Cancelado'
        elif ot['Estado_OT'] in ['Abierta', 'En Proceso']:
            estado_plan = 'Pendiente'
        else:
            estado_plan = 'Ejecutado'

        planes.append({
            'Plan_ID': f'PM{plan_id:05d}',
            'Equipo_ID': ot['Equipo_ID'],
            'Actividad_ID': ot['Actividad_ID'],
            'OT_ID_Ejecutado': ot['OT_ID'] if estado_plan == 'Ejecutado' else None,
            'Fecha_Programada': fecha_programada.date(),
            'Tipo_Mantenimiento': ot['Tipo_OT'],
            'Horas_Planificadas': ot['Horas_Planificadas'],
            'Estado_Plan': estado_plan,
        })
        plan_id += 1

    # Agregar planes reprogramados y no ejecutados para realismo
    n_extra = int(len(planes) * 0.12)  # ~12% adicional de planes no cumplidos
    actividades_prev = [1, 2, 3, 4, 5, 6, 7]  # IDs de preventivas
    for _ in range(n_extra):
        equipo_id = np.random.choice(dim_equipo['Equipo_ID'].values)
        actividad_id = np.random.choice(actividades_prev)
        dia_aleatorio = np.random.randint(0, DIAS_TOTALES)
        fecha_prog = FECHA_INICIO + timedelta(days=dia_aleatorio)

        estado = np.random.choice(['Reprogramado', 'Cancelado', 'Pendiente'], p=[0.5, 0.3, 0.2])

        actividad_info = dim_actividad[dim_actividad['Actividad_ID'] == actividad_id].iloc[0]

        planes.append({
            'Plan_ID': f'PM{plan_id:05d}',
            'Equipo_ID': equipo_id,
            'Actividad_ID': actividad_id,
            'OT_ID_Ejecutado': None,
            'Fecha_Programada': fecha_prog.date(),
            'Tipo_Mantenimiento': 'Preventivo',
            'Horas_Planificadas': actividad_info['Duracion_Estimada_Hrs'],
            'Estado_Plan': estado,
        })
        plan_id += 1

    df = pd.DataFrame(planes).sort_values('Fecha_Programada').reset_index(drop=True)
    df['Plan_ID'] = [f'PM{i:05d}' for i in range(1, len(df) + 1)]
    df.to_csv(f"{OUTPUT_DIR}/Fact_Plan_Mantenimiento.csv", index=False)
    print(f"  ✓ {len(df):,} planes generados")
    print(f"    Estados: {df['Estado_Plan'].value_counts().to_dict()}")
    return df


# ============================================================
# MAIN
# ============================================================

def main():
    print("="*60)
    print("GENERADOR DE DATA SINTÉTICA - MANTENIMIENTO MINERO")
    print(f"Periodo: {FECHA_INICIO.date()} a {FECHA_FIN.date()}")
    print("="*60)

    # Dimensiones
    dim_fecha    = generar_dim_fecha()
    dim_equipo   = generar_dim_equipo()
    dim_comp     = generar_dim_componente()
    dim_causa    = generar_dim_causa_raiz()
    dim_act      = generar_dim_actividad()
    dim_mec      = generar_dim_mecanico()
    dim_turno    = generar_dim_turno()

    # Hechos (orden importa por FKs)
    fact_eventos = generar_fact_eventos(dim_equipo, dim_fecha)
    fact_fallas  = generar_fact_fallas(dim_equipo, dim_comp, dim_causa, dim_fecha)
    fact_ot      = generar_fact_ot(dim_equipo, dim_act, dim_mec, dim_comp, fact_fallas)
    fact_plan    = generar_fact_plan(dim_equipo, dim_act, fact_ot)

    print("\n" + "="*60)
    print("GENERACIÓN COMPLETA")
    print("="*60)

    # Resumen
    archivos = sorted(os.listdir(OUTPUT_DIR))
    print(f"\n{len(archivos)} archivos CSV generados en {OUTPUT_DIR}:")
    total_size = 0
    for f in archivos:
        path = os.path.join(OUTPUT_DIR, f)
        size_kb = os.path.getsize(path) / 1024
        total_size += size_kb
        print(f"  {f:<40} {size_kb:>8.1f} KB")
    print(f"  {'TOTAL':<40} {total_size:>8.1f} KB")


if __name__ == '__main__':
    main()
