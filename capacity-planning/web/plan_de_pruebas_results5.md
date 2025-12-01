# Escenario 1 - Capacidad de la capa Web (Usuarios concurrentes) - Resultados Actualizados

## Resumen Ejecutivo

Este documento presenta los resultados de las pruebas de capacidad realizadas con métricas mejoradas que permiten comparación objetiva entre escenarios. Se utilizaron métricas de throughput en MB/min y MB/s, junto con análisis completo de variabilidad y percentiles de latencia.

**Configuración del Test:**
- Video File Size: 13.14 MB
- API Endpoint: http://api-load-balancer-349981975.us-east-1.elb.amazonaws.com:8000/api/videos/upload
- Ramp-Up: 3 minutos (para tests de ramp)
- Hold Duration: 3 minutos (para tests de ramp), 5 minutos (para test de estabilidad)

---

[Detalle de pruebas](../../test_concurrency/results/results5/)

## 1. Smoke Test - Validación Básica (5 usuarios, 1 minuto)

### Objetivo
Validar que el sistema responde correctamente y la telemetría está activa con carga mínima.

### Estadísticas

- **Total Requests**: 33
- **Successful Requests**: 33
- **Failed Requests**: 0
- **Success Rate**: 100.00%
- **Test Duration**: 62.98 seconds

### Throughput Metrics (Comparable across scenarios)

- **MB/min**: 413.11
- **MB/s**: 6.89
- **Total MB Uploaded**: 433.60
- **Video File Size**: 13.14 MB

### Latency Statistics (per video)

- **Average**: 9218.64ms
- **Minimum**: 3424ms
- **Maximum**: 12042ms
- **Standard Deviation**: 1764.14ms
- **P50 (Median)**: 9270.00ms
- **P95**: 11628.00ms
- **P99**: 12042.00ms

### Análisis

✅ **Test Exitoso**: El sistema responde correctamente con 5 usuarios concurrentes.
- Latencia promedio: ~9.2 segundos por video
- Baja variabilidad (desviación estándar: 1.76s)
- P95 dentro de límites razonables (~11.6s)

---

## 2. Ramp-Up Tests - Identificación del Nivel Máximo Sin Degradación

### 2.1 Test 100 Usuarios

**Configuración:**
- Ramp-Up: 0 → 100 usuarios en 3 minutos
- Hold: 100 usuarios durante 3 minutos

#### Estadísticas

- **Total Requests**: 154
- **Successful Requests**: 154
- **Failed Requests**: 0
- **Success Rate**: 100.00%
- **Test Duration**: 608.38 seconds (10.14 minutes)

#### Throughput Metrics

- **MB/min**: 199.56
- **MB/s**: 3.33
- **Total MB Uploaded**: 2023.49

#### Latency Statistics (per video)

- **Average**: 284255.25ms (~4.7 minutos)
- **Minimum**: 3210ms
- **Maximum**: 382909ms (~6.4 minutos)
- **Standard Deviation**: 86881.91ms
- **P50 (Median)**: 293758.00ms (~4.9 minutos)
- **P95**: 376814.00ms (~6.3 minutos)
- **P99**: 378985.00ms (~6.3 minutos)

#### Variability Analysis (Hold Phase)

- **Average Processing Time**: 299489.90ms (~5.0 minutos)
- **Standard Deviation**: 36224.33ms
- **Coefficient of Variation**: 12.10%
- **P50 (Median)**: 296334.00ms
- **P95**: 376156.00ms
- **P99**: 382909.00ms

#### Performance Comparison (Ramp-Up vs Hold)

- **Ramp-Up Avg Response Time**: 278909.75ms
- **Hold Phase Avg Response Time**: 299489.90ms
- **Performance Degradation**: 7.38%
- ✅ **Performance is stable**
- ✅ **Response times are stable (low variation)**

#### Evaluación

✅ **Test Exitoso**: El sistema maneja 100 usuarios concurrentes de manera estable.
- Degradación mínima entre ramp-up y hold (7.38%)
- Baja variabilidad en fase de hold (CV: 12.10%)
- Throughput sostenible: 3.33 MB/s

---

### 2.2 Test 200 Usuarios

**Configuración:**
- Ramp-Up: 0 → 200 usuarios en 3 minutos
- Hold: 200 usuarios durante 3 minutos

#### Estadísticas

- **Total Requests**: 268
- **Successful Requests**: 268
- **Failed Requests**: 0
- **Success Rate**: 100.00%
- **Test Duration**: 851.72 seconds (14.20 minutes)

#### Throughput Metrics

- **MB/min**: 248.07
- **MB/s**: 4.13
- **Total MB Uploaded**: 3521.39

#### Latency Statistics (per video)

- **Average**: 407150.93ms (~6.8 minutos)
- **Minimum**: 4543ms
- **Maximum**: 644136ms (~10.7 minutos)
- **Standard Deviation**: 158242.51ms
- **P50 (Median)**: 441257.00ms (~7.4 minutos)
- **P95**: 597119.00ms (~10.0 minutos)
- **P99**: 642106.00ms (~10.7 minutos)

#### Variability Analysis (Hold Phase)

- **Average Processing Time**: 571122.40ms (~9.5 minutos)
- **Standard Deviation**: 36805.78ms
- **Coefficient of Variation**: 6.44%
- **P50 (Median)**: 577554.00ms
- **P95**: 642106.00ms
- **P99**: 644136.00ms

#### Performance Comparison (Ramp-Up vs Hold)

- **Ramp-Up Avg Response Time**: 369542.79ms
- **Hold Phase Avg Response Time**: 571122.40ms
- **Performance Degradation**: 54.55%
- ⚠️ **WARNING: Significant performance degradation detected (>50%)**
- ✅ **Response times are stable (low variation)**

#### Evaluación

⚠️ **Test con Degradación Significativa**: 
- Aunque el success rate es 100%, hay degradación significativa (54.55%) entre ramp-up y hold
- Latencia promedio en hold: ~9.5 minutos por video
- Throughput: 4.13 MB/s
- **Nota**: La variabilidad es baja (CV: 6.44%), lo que indica que el sistema es estable pero lento

---

### 2.3 Test 300 Usuarios

**Configuración:**
- Ramp-Up: 0 → 300 usuarios en 3 minutos
- Hold: 300 usuarios durante 3 minutos

#### Estadísticas

- **Total Requests**: 404
- **Successful Requests**: 404
- **Failed Requests**: 0
- **Success Rate**: 100.00%
- **Test Duration**: 988.47 seconds (16.47 minutes)

#### Throughput Metrics

- **MB/min**: 322.22
- **MB/s**: 5.37
- **Total MB Uploaded**: 5308.36

#### Latency Statistics (per video)

- **Average**: 462866.05ms (~7.7 minutos)
- **Minimum**: 3348ms
- **Maximum**: 742963ms (~12.4 minutos)
- **Standard Deviation**: 203823.63ms
- **P50 (Median)**: 472967.00ms (~7.9 minutos)
- **P95**: 729638.00ms (~12.2 minutos)
- **P99**: 737927.00ms (~12.3 minutos)

#### Variability Analysis (Hold Phase)

- **Average Processing Time**: 671639.18ms (~11.2 minutos)
- **Standard Deviation**: 25851.61ms
- **Coefficient of Variation**: 3.85%
- **P50 (Median)**: 669426.00ms
- **P95**: 711135.00ms
- **P99**: 732324.00ms

#### Performance Comparison (Ramp-Up vs Hold)

- **Ramp-Up Avg Response Time**: 432703.37ms
- **Hold Phase Avg Response Time**: 671639.18ms
- **Performance Degradation**: 55.22%
- ⚠️ **WARNING: Significant performance degradation detected (>50%)**
- ✅ **Response times are stable (low variation)**

#### Evaluación

⚠️ **Test con Degradación Significativa**: 
- Success rate 100%, pero degradación de 55.22%
- Latencia promedio en hold: ~11.2 minutos por video
- Throughput: 5.37 MB/s (mejor que 200 usuarios)
- Variabilidad muy baja (CV: 3.85%), sistema estable pero lento

---

### 2.4 Test 500 Usuarios

**Configuración:**
- Ramp-Up: 0 → 500 usuarios en 3 minutos
- Hold: 500 usuarios durante 3 minutos

#### Estadísticas

- **Total Requests**: 569
- **Successful Requests**: 200
- **Failed Requests**: 369
- **Success Rate**: 35.15%
- **Test Duration**: 1582.04 seconds (26.37 minutes)

#### Throughput Metrics

- **MB/min**: 99.66
- **MB/s**: 1.66
- **Total MB Uploaded**: 2627.90

#### Latency Statistics (per video - solo exitosos)

- **Average**: 802582.05ms (~13.4 minutos)
- **Minimum**: 3927ms
- **Maximum**: 1394094ms (~23.2 minutos)
- **Standard Deviation**: 454375.07ms
- **P50 (Median)**: 483817.00ms
- **P95**: 660403.00ms
- **P99**: 664276.00ms

#### Errors Summary

- **Status 401**: 319 errors (timeout/authentication)
- **Status UNKNOWN**: 50 errors (timeout exceeded)
- **Total Errors**: 369 (64.85% failure rate)

#### Evaluación

❌ **Test Fallido**: 
- Success rate crítico: 35.15%
- 369 requests fallidas (64.85%)
- Throughput degradado: 1.66 MB/s (peor que todos los anteriores)
- Múltiples timeouts (300s timeout exceeded)
- **El sistema no puede manejar 500 usuarios concurrentes**

---

## 3. Stability Test - Confirmación de Estabilidad al 80% del Nivel Base

### 3.1 Test de Estabilidad (160 usuarios - 80% de 200)

**Configuración:**
- Base Level (X): 200 usuarios
- Stability Level: 160 usuarios (80% de 200)
- Ramp-Up: 0 → 160 usuarios en 60 segundos
- Hold: 160 usuarios durante 5 minutos

#### Estadísticas

- **Total Requests**: 261
- **Successful Requests**: 211
- **Failed Requests**: 50
- **Success Rate**: 80.84%
- **Test Duration**: 1304.35 seconds (21.74 minutes)

#### Throughput Metrics

- **MB/min**: 127.53
- **MB/s**: 2.13
- **Total MB Uploaded**: 2772.44

#### Latency Statistics (per video)

- **Average**: 531337.42ms (~8.9 minutos)
- **Minimum**: 54372ms
- **Maximum**: 1070752ms (~17.8 minutos)
- **Standard Deviation**: 326665.80ms
- **P50 (Median)**: 344478.00ms
- **P95**: 1006338.00ms (~16.8 minutos)
- **P99**: 1012261.00ms (~16.9 minutos)

#### Variability Analysis (Hold Phase)

- **Average Processing Time**: 899308.34ms (~15.0 minutos)
- **Standard Deviation**: 227810.48ms
- **Coefficient of Variation**: 25.33%
- **P50 (Median)**: 998957.00ms
- **P95**: 1012261.00ms
- **P99**: 1015765.00ms

#### Performance Comparison (Ramp-Up vs Hold)

- **Ramp-Up Avg Response Time**: 262942.09ms
- **Hold Phase Avg Response Time**: 899308.34ms
- **Performance Change**: +242.02%
- ⚠️ **WARNING: Significant performance degradation detected (>50%)**
- ✅ **Response times are stable (low variation)**

#### Errors Summary

- **Status UNKNOWN**: 50 errors (timeout of 300000ms exceeded)

#### Evaluación

❌ **Test de Estabilidad Fallido**: 
- Success rate: 80.84% (por debajo del 95% requerido)
- Degradación extrema: +242% entre ramp-up y hold
- Latencia promedio en hold: ~15 minutos por video
- 50 timeouts durante el test
- **El sistema no puede mantener estabilidad al 80% del nivel base (200 usuarios)**

---

## Análisis Comparativo

### Tabla Comparativa de Throughput

| Escenario | Usuarios | MB/min | MB/s | Success Rate | Estado |
|-----------|----------|--------|------|--------------|--------|
| Smoke Test | 5 | 413.11 | 6.89 | 100% | ✅ Exitoso |
| Ramp 100 | 100 | 199.56 | 3.33 | 100% | ✅ Exitoso |
| Ramp 200 | 200 | 248.07 | 4.13 | 100% | ⚠️ Degradación |
| Ramp 300 | 300 | 322.22 | 5.37 | 100% | ⚠️ Degradación |
| Ramp 500 | 500 | 99.66 | 1.66 | 35.15% | ❌ Fallido |
| Stability 160 | 160 | 127.53 | 2.13 | 80.84% | ❌ Fallido |

### Tabla Comparativa de Latencia (P95)

| Escenario | Usuarios | P95 (ms) | P95 (minutos) | Estado |
|-----------|----------|----------|---------------|--------|
| Smoke Test | 5 | 11628 | 0.19 | ✅ |
| Ramp 100 | 100 | 376814 | 6.28 | ⚠️ |
| Ramp 200 | 200 | 597119 | 9.95 | ⚠️ |
| Ramp 300 | 300 | 729638 | 12.16 | ⚠️ |
| Ramp 500 | 500 | 660403 | 11.01 | ❌ |
| Stability 160 | 160 | 1006338 | 16.77 | ❌ |

### Tabla Comparativa de Variabilidad (Hold Phase)

| Escenario | Usuarios | Std Dev (ms) | Coef. Variación | Estado |
|-----------|----------|--------------|-----------------|--------|
| Ramp 100 | 100 | 36224.33 | 12.10% | ✅ Baja variabilidad |
| Ramp 200 | 200 | 36805.78 | 6.44% | ✅ Muy baja variabilidad |
| Ramp 300 | 300 | 25851.61 | 3.85% | ✅ Muy baja variabilidad |
| Stability 160 | 160 | 227810.48 | 25.33% | ⚠️ Alta variabilidad |

---

## Conclusiones y Recomendaciones

### Nivel Máximo Sin Degradación

**100 usuarios concurrentes** es el mejor nivel identificado sin degradación significativa:
- ✅ Success rate: 100%
- ✅ Degradación ramp-up vs hold: 7.38% (aceptable)
- ✅ Throughput: 3.33 MB/s
- ✅ Variabilidad baja (CV: 12.10%)
- ⚠️ Latencia alta pero estable (~5 minutos promedio en hold)

### Puntos Críticos Identificados

1. **200 usuarios**: Degradación significativa (54.55%) pero success rate 100%
2. **300 usuarios**: Degradación similar (55.22%) pero mejor throughput (5.37 MB/s)
3. **500 usuarios**: Sistema colapsa (35.15% success rate)
4. **Stability 160 usuarios**: No puede mantener estabilidad (80.84% success rate, 242% degradación)

### Recomendaciones

1. **Capacidad Operativa Recomendada**: 
   - **Máximo sostenible**: 100 usuarios concurrentes
   - **Throughput esperado**: ~3.33 MB/s
   - **Latencia promedio**: ~5 minutos por video

2. **Mejoras Necesarias**:
   - Optimizar procesamiento para reducir latencia (actualmente ~5-6 minutos por video)
   - Investigar degradación significativa a partir de 200 usuarios
   - Revisar timeouts (300s puede ser insuficiente para alta carga)
   - Considerar escalado horizontal o vertical para mejorar capacidad

3. **Monitoreo**:
   - Implementar alertas cuando success rate < 95%
   - Monitorear degradación entre ramp-up y hold (>20% es preocupante)
   - Trackear variabilidad (CV > 30% indica inestabilidad)

4. **Próximos Pasos**:
   - Realizar test de estabilidad con 80 usuarios (80% de 100)
   - Investigar causas de degradación a partir de 200 usuarios
   - Optimizar procesamiento de videos para reducir latencia
   - Considerar implementar colas de procesamiento asíncrono

---

## Criterios de Evaluación

### Criterios Aplicados

- ✅ **Success Rate**: Debe ser ≥ 95%
- ⚠️ **Degradación**: < 20% es aceptable, 20-50% es moderada, >50% es significativa
- ✅ **Variabilidad**: CV < 30% es estable, 30-50% es moderada, >50% es inestable
- ⚠️ **Latencia**: P95 < 1 minuto es ideal, pero actualmente el sistema tiene latencias altas

### Resultados por Criterio

| Escenario | Success Rate | Degradación | Variabilidad | Latencia P95 | Evaluación Final |
|-----------|--------------|-------------|--------------|---------------|------------------|
| Smoke (5) | ✅ 100% | N/A | ✅ Baja | ⚠️ 11.6s | ✅ Aceptable |
| Ramp 100 | ✅ 100% | ✅ 7.38% | ✅ 12.10% | ⚠️ 6.3 min | ✅ **Mejor nivel** |
| Ramp 200 | ✅ 100% | ⚠️ 54.55% | ✅ 6.44% | ⚠️ 10.0 min | ⚠️ Degradación |
| Ramp 300 | ✅ 100% | ⚠️ 55.22% | ✅ 3.85% | ⚠️ 12.2 min | ⚠️ Degradación |
| Ramp 500 | ❌ 35.15% | N/A | N/A | ⚠️ 11.0 min | ❌ **Fallido** |
| Stability 160 | ❌ 80.84% | ⚠️ 242% | ⚠️ 25.33% | ⚠️ 16.8 min | ❌ **Fallido** |

---

**Fecha de Pruebas**: 2025-11-26  
**Versión del Sistema**: Actualizada con métricas mejoradas (MB/min, MB/s, variabilidad completa)

