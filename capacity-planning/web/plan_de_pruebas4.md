# Escenario 1 - Capacidad de la capa Web (Usuarios concurrentes) - Plan 3

### 0. Smoke Test - Validación Inicial del Sistema

**Objetivo**: Validar que el sistema responde correctamente y la telemetría está activa antes de ejecutar pruebas de carga más intensivas.

**Configuración**:
- Usuarios concurrentes: 5
- Duración: 60 segundos
- Herramienta: `smoke_test.js`

## Estadistica

- Total Requests: 109
- Successful Requests: 109
- Failed Requests: 0
- Success Rate: 100.00%
- Throughput: 1.77 requests/segundo
- Average: 2701.79 MS (2.7 segundos)
- Minimum: 1679 MS
- Maximum: 5865 MS
- Error: 0%

**Análisis**:
- ✅ El sistema responde correctamente bajo carga mínima
- ✅ Tiempos de respuesta aceptables (promedio 2.7 segundos)
- ✅ Sin errores, indicando que el sistema está operativo
- ✅ Throughput estable de 1.77 req/seg con 5 usuarios

### 1. Escenario **5 usuarios durante 1 minutos para validar que todo responde y la telemetría está activa.**

## Estadistica

- Total Request : 181
- Average: 1674 MS
- p95: N/A
- Min: 324 MS
- Max: 2559 MS
- Error: 0%

### 2. Ramp iniciar en 0 y aumentar hasta X usuarios en 3 minutos; mantener 5 minutos. Repetir con X creciente (p. ej., 100 → 200 → 300) hasta observar degradación.

## Estadistica

### Test 100 Usuarios (Ejecución 1)
- Total Request: 928
- Average: 44736.55 MS
- p95: 85999 MS
- p99: 110485 MS
- Min: 1581 MS
- Max: 120433 MS
- Error: 3.45% (32 errores)
- Success Rate: 96.55%
- Throughput: 1.77 req/seg
- Performance Degradation: 88.38% (Ramp-Up: 28779.70ms → Hold: 54214.80ms)
- Errores: 3x Status 500, 26x Status 504, 3x UNKNOWN (ETIMEDOUT)

### Test 100 Usuarios (Ejecución 2)
- Total Request: 999
- Average: 41850.75 MS
- p95: 67622 MS
- p99: 75716 MS
- Min: 1283 MS
- Max: 81108 MS
- Error: 25.93% (259 errores)
- Success Rate: 74.07%
- Throughput: 1.83 req/seg
- Performance Degradation: 608.00% (Ramp-Up: 6606.79ms → Hold: 46776.31ms)
- Errores: 52x Status 500, 207x Status 504

### Test 200 Usuarios
- Total Request: 890
- Average: 99676.49 MS
- p95: 149072 MS
- p99: 162979 MS
- Min: 2309 MS
- Max: 177036 MS
- Error: 2.81% (25 errores)
- Success Rate: 97.19%
- Throughput: 1.55 req/seg
- Performance Degradation: 42.13% (Ramp-Up: 81400.07ms → Hold: 115692.42ms)
- Errores: 23x Status 504, 2x UNKNOWN (ETIMEDOUT)

### 3. Análisis de Estabilidad y Degradación

#### Observaciones Clave:

1. **Variabilidad en 100 usuarios**: 
   - Primera ejecución: 96.55% éxito con degradación moderada (88.38%)
   - Segunda ejecución: 74.07% éxito con degradación severa (608%)
   - Indica inestabilidad del sistema bajo carga de 100 usuarios

2. **200 usuarios muestra mejor estabilidad**:
   - 97.19% éxito (mejor que ambas ejecuciones de 100 usuarios)
   - Degradación más controlada (42.13%)
   - Menor tasa de errores (2.81% vs 3.45% y 25.93%)

3. **Patrón de errores**:
   - Principalmente errores 504 (Gateway Timeout) - indica que el servidor tarda demasiado en responder
   - Algunos errores 500 (Internal Server Error) - especialmente en la segunda ejecución de 100 usuarios
   - Timeouts (ETIMEDOUT) - conexiones que exceden el timeout

4. **Tiempos de respuesta**:
   - Con 100 usuarios: promedio entre 41-44 segundos
   - Con 200 usuarios: promedio ~99 segundos (más del doble)
   - P95 consistentemente alto (67-149 segundos)

### 4. Recomendaciones

1. **Capacidad recomendada**: 100 usuarios concurrentes con monitoreo activo
   - Aunque 200 usuarios tiene mejor tasa de éxito, los tiempos de respuesta son muy altos
   - 100 usuarios muestra variabilidad, requiere optimización

2. **Puntos de mejora**:
   - Reducir tiempos de procesamiento de videos
   - Optimizar el manejo de conexiones concurrentes
   - Implementar mejor manejo de timeouts
   - Revisar configuración del load balancer para errores 504
