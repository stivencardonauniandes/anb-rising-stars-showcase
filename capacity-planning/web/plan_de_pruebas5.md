# Escenario 1 - Capacidad de la capa Web (Usuarios concurrentes) - Plan 5

## Objetivo General

Validar y confirmar la capacidad operativa del sistema basado en los hallazgos del Plan de Pruebas Results 5, con enfoque en:
- Confirmar estabilidad al 80% del nivel máximo identificado (100 usuarios)
- Investigar la degradación observada entre 100-200 usuarios
- Validar mejoras y optimizaciones implementadas
- Establecer métricas de monitoreo continuo

**Basado en resultados anteriores:**
- Nivel máximo sin degradación: **100 usuarios concurrentes**
- Throughput sostenible: **3.33 MB/s**
- Latencia promedio: **~5 minutos por video**

---

## Configuración Base

### Herramientas
- **Smoke Test**: `smoke_test.js`
- **Ramp-Up Tests**: `ramp_test.js` (configurable via `MAX_USERS`)
- **Stability Test**: `stability_test.js` (configurable via `BASE_LEVEL`)

### Configuración del Entorno
- **API Endpoint**: http://api-load-balancer-349981975.us-east-1.elb.amazonaws.com:8000/api/videos/upload
- **Video File Size**: 13.14 MB
- **Ramp-Up Duration**: 3 minutos (para tests de ramp)
- **Hold Duration**: 3 minutos (para tests de ramp), 5 minutos (para test de estabilidad)
- **Timeout por Request**: 300 segundos (5 minutos)

### Métricas a Capturar

**Throughput (Comparable across scenarios):**
- MB/min
- MB/s
- Total MB Uploaded

**Latency Statistics (per video):**
- Average
- Minimum
- Maximum
- Standard Deviation
- P50 (Median)
- P95
- P99

**Variability Analysis:**
- Standard Deviation
- Coefficient of Variation
- Performance Degradation (Ramp-Up vs Hold)

**Success Metrics:**
- Total Requests
- Successful Requests
- Failed Requests
- Success Rate
- Error Summary (por status code)

---

## Escenarios de Prueba

### 0. Smoke Test - Validación Inicial del Sistema

**Objetivo**: Validar que el sistema responde correctamente y la telemetría está activa antes de ejecutar pruebas de carga más intensivas.

**Configuración**:
- Usuarios concurrentes: 5
- Duración: 60 segundos
- Herramienta: `npm run smoke` o `node smoke_test.js`

**Criterios de Éxito**:
- ✅ Success Rate ≥ 95%
- ✅ Latencia promedio < 15 segundos
- ✅ Sin errores críticos (500, 502, 503)
- ✅ Variabilidad baja (CV < 30%)

**Métricas Esperadas (basado en resultados anteriores)**:
- MB/min: ~400-420
- MB/s: ~6.5-7.0
- P95: < 12 segundos

---

### 1. Test de Estabilidad al 80% del Nivel Base (80 usuarios)

**Objetivo**: Confirmar que el sistema puede mantener estabilidad sostenida al 80% del nivel máximo identificado (100 usuarios → 80 usuarios).

**Configuración**:
- Base Level (X): 100 usuarios
- Stability Level: 80 usuarios (80% de 100)
- Ramp-Up: 0 → 80 usuarios en 60 segundos
- Hold Duration: 5 minutos
- Herramienta: `BASE_LEVEL=100 npm run stability`

**Criterios de Éxito**:
- ✅ Success Rate ≥ 95%
- ✅ Degradación ramp-up vs hold < 20%
- ✅ Variabilidad estable (CV < 30%)
- ✅ Sin timeouts masivos
- ✅ Throughput sostenible: ~2.5-3.0 MB/s

**Métricas a Monitorear**:
- Latencia promedio en hold phase
- Desviación estándar del tiempo de procesamiento
- Coeficiente de variación
- P50, P95, P99 de latencia
- MB/min y MB/s durante hold phase

**Análisis Esperado**:
- Si este test pasa, confirma que 100 usuarios es un nivel sostenible
- Si falla, indica que el nivel máximo real es menor a 100 usuarios

---

### 2. Ramp-Up Test - Confirmación de 100 Usuarios

**Objetivo**: Re-validar que 100 usuarios concurrentes es el nivel máximo sin degradación significativa.

**Configuración**:
- Ramp-Up: 0 → 100 usuarios en 3 minutos
- Hold: 100 usuarios durante 3 minutos
- Herramienta: `MAX_USERS=100 npm run ramp:100`

**Criterios de Éxito**:
- ✅ Success Rate ≥ 95%
- ✅ Degradación ramp-up vs hold < 20%
- ✅ Variabilidad baja (CV < 30%)
- ✅ Throughput: ~3.0-3.5 MB/s

**Métricas Esperadas (basado en resultados anteriores)**:
- MB/min: ~195-205
- MB/s: ~3.2-3.4
- Latencia promedio en hold: ~4.5-5.5 minutos
- P95: ~6.0-6.5 minutos
- Degradación: < 10%

---

### 3. Ramp-Up Test - Investigación de Degradación (150 usuarios)

**Objetivo**: Investigar el punto de degradación entre 100 y 200 usuarios para entender mejor el comportamiento del sistema.

**Configuración**:
- Ramp-Up: 0 → 150 usuarios en 3 minutos
- Hold: 150 usuarios durante 3 minutos
- Herramienta: `MAX_USERS=150 npm run ramp:custom`

**Criterios de Evaluación**:
- Success Rate (objetivo: ≥ 95%)
- Degradación ramp-up vs hold
- Variabilidad
- Throughput comparado con 100 usuarios

**Análisis Esperado**:
- Si success rate ≥ 95% y degradación < 50%: 150 usuarios es viable
- Si success rate < 95% o degradación > 50%: confirma que 100 es el límite
- Identificar el punto exacto donde comienza la degradación significativa

---

### 4. Ramp-Up Test - Validación de 200 Usuarios

**Objetivo**: Confirmar el comportamiento observado anteriormente con 200 usuarios (degradación significativa pero success rate 100%).

**Configuración**:
- Ramp-Up: 0 → 200 usuarios en 3 minutos
- Hold: 200 usuarios durante 3 minutos
- Herramienta: `MAX_USERS=200 npm run ramp:200`

**Criterios de Evaluación**:
- Success Rate (esperado: 100% basado en resultados anteriores)
- Degradación ramp-up vs hold (esperado: ~50-55%)
- Throughput (esperado: ~4.0-4.5 MB/s)
- Variabilidad (esperado: baja, CV < 10%)

**Análisis Esperado**:
- Confirmar que aunque hay degradación, el sistema mantiene 100% success rate
- Entender si la degradación es aceptable para casos de uso específicos
- Validar que el throughput mejora respecto a 100 usuarios (aunque con mayor latencia)

---

### 5. Ramp-Up Test - Límite de Capacidad (400 usuarios)

**Objetivo**: Identificar el punto exacto donde el sistema comienza a fallar masivamente (entre 300 y 500 usuarios).

**Configuración**:
- Ramp-Up: 0 → 400 usuarios en 3 minutos
- Hold: 400 usuarios durante 3 minutos
- Herramienta: `MAX_USERS=400 npm run ramp:custom`

**Criterios de Evaluación**:
- Success Rate (objetivo: ≥ 95%, pero puede ser menor)
- Identificar tipos de errores (timeouts, 500, 502, 503, 504)
- Throughput comparado con niveles anteriores
- Punto de quiebre del sistema

**Análisis Esperado**:
- Si success rate ≥ 95%: 400 usuarios es viable (aunque con degradación)
- Si success rate < 95%: confirma que el límite está entre 300-400 usuarios
- Identificar el tipo de errores para entender el cuello de botella

---

## Criterios de Evaluación

### Criterios de Éxito por Escenario

| Escenario | Success Rate | Degradación | Variabilidad (CV) | Throughput | Estado |
|-----------|--------------|-------------|-------------------|------------|--------|
| Smoke (5) | ≥ 95% | N/A | < 30% | ~6-7 MB/s | ✅ Validación |
| Stability 80 | ≥ 95% | < 20% | < 30% | ~2.5-3.0 MB/s | ✅ Confirmación |
| Ramp 100 | ≥ 95% | < 20% | < 30% | ~3.0-3.5 MB/s | ✅ Confirmación |
| Ramp 150 | ≥ 95% | < 50% | < 30% | Comparar con 100 | ⚠️ Investigación |
| Ramp 200 | ≥ 95% | < 60% | < 30% | ~4.0-4.5 MB/s | ⚠️ Validación |
| Ramp 400 | ≥ 80% | N/A | < 50% | Comparar | ❌ Límite |

### Criterios de Degradación

- **< 20%**: Aceptable, sistema estable
- **20-50%**: Moderada, requiere monitoreo
- **50-100%**: Significativa, sistema funcional pero degradado
- **> 100%**: Crítica, sistema inestable

### Criterios de Variabilidad

- **CV < 30%**: Estable, respuesta consistente
- **CV 30-50%**: Moderada variabilidad, requiere atención
- **CV > 50%**: Alta variabilidad, sistema inestable

---

## Plan de Ejecución

### Orden de Ejecución Recomendado

1. **Smoke Test** (5 usuarios, 1 minuto)
   - Validar sistema operativo
   - Tiempo estimado: 2 minutos

2. **Ramp-Up Test 100 usuarios**
   - Confirmar nivel base
   - Tiempo estimado: 10-12 minutos

3. **Stability Test 80 usuarios**
   - Confirmar estabilidad al 80%
   - Tiempo estimado: 6-7 minutos

4. **Ramp-Up Test 150 usuarios**
   - Investigar punto de degradación
   - Tiempo estimado: 10-12 minutos

5. **Ramp-Up Test 200 usuarios**
   - Validar comportamiento conocido
   - Tiempo estimado: 10-12 minutos

6. **Ramp-Up Test 400 usuarios**
   - Identificar límite de capacidad
   - Tiempo estimado: 10-12 minutos

**Tiempo total estimado**: ~50-60 minutos

### Consideraciones

- Ejecutar tests con suficiente tiempo entre ellos para que el sistema se recupere
- Monitorear métricas del sistema (CPU, memoria, conexiones) durante las pruebas
- Capturar logs y métricas de Grafana para análisis posterior
- Documentar cualquier anomalía o comportamiento inesperado

---

## Monitoreo y Alertas

### Métricas a Monitorear en Tiempo Real

**Sistema:**
- CPU usage por instancia
- Memory usage
- Network throughput
- Active connections

**Aplicación:**
- Success rate
- Latency (average, P95, P99)
- Error rate por tipo
- Throughput (MB/s)

### Alertas Recomendadas

- **Success Rate < 95%**: Alerta crítica
- **Degradación > 50%**: Alerta de advertencia
- **CV > 30%**: Alerta de variabilidad
- **Timeout rate > 5%**: Alerta de capacidad
- **Error 500/502/503 > 1%**: Alerta de sistema

---

## Análisis Post-Prueba

### Comparación con Resultados Anteriores

Para cada escenario, comparar:
- Throughput (MB/min, MB/s) - debe ser comparable
- Latencia (P50, P95, P99) - identificar mejoras o degradaciones
- Variabilidad (CV) - confirmar estabilidad
- Success Rate - validar mejoras

### Identificación de Mejoras

- Comparar resultados con plan_de_pruebas_results5.md
- Identificar mejoras en latencia, throughput o estabilidad
- Documentar regresiones o nuevos problemas

### Recomendaciones

Basado en los resultados:
- Confirmar o ajustar capacidad operativa recomendada
- Identificar áreas de mejora
- Proponer optimizaciones específicas
- Establecer límites operativos

---

## Documentación de Resultados

### Formato de Salida

Los resultados deben documentarse en:
- `capacity-planning/web/plan_de_pruebas_results6.md`
- Incluir todas las métricas capturadas
- Comparación con resultados anteriores
- Análisis de variabilidad completo
- Conclusiones y recomendaciones

### Estructura del Reporte

1. Resumen Ejecutivo
2. Configuración del Test
3. Resultados por Escenario (con todas las métricas)
4. Análisis Comparativo
5. Tablas Comparativas (Throughput, Latencia, Variabilidad)
6. Conclusiones y Recomendaciones
7. Criterios de Evaluación

---

## Próximos Pasos Post-Prueba

1. **Análisis de Resultados**:
   - Comparar con resultados anteriores
   - Identificar mejoras o regresiones
   - Validar hipótesis sobre capacidad

2. **Optimizaciones**:
   - Basadas en hallazgos de degradación
   - Mejoras en procesamiento de videos
   - Optimización de timeouts y conexiones

3. **Pruebas de Seguimiento**:
   - Tests específicos para áreas problemáticas
   - Validación de optimizaciones implementadas
   - Tests de regresión

4. **Documentación**:
   - Actualizar capacidad operativa recomendada
   - Documentar límites del sistema
   - Establecer métricas de monitoreo continuo

---

**Fecha de Creación**: 2025-11-26  
**Basado en**: plan_de_pruebas_results5.md  
**Versión**: 5.0

