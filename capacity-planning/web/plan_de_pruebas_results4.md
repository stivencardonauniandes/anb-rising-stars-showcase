# Escenario 1 - Capacidad de la capa Web (Usuarios concurrentes) - Resultados Plan 3

## Resumen Ejecutivo

Este documento presenta los resultados de las pruebas de carga realizadas con diferentes niveles de usuarios concurrentes, comenzando con un smoke test de validación inicial (5 usuarios) y luego pruebas de ramp-up con 100 y 200 usuarios. Los tests fueron ejecutados con los scripts `smoke_test.js` y `ramp_test.js` que implementan keep-alive HTTP para optimizar el uso de conexiones.

## Metodología

### Smoke Test
- **Usuarios**: 5 concurrentes
- **Duración**: 60 segundos
- **Herramienta**: `smoke_test.js`

### Ramp-Up Tests
- **Ramp-Up**: 0 → X usuarios en 3 minutos
- **Hold**: Mantener X usuarios durante 5 minutos
- **Total duración**: ~8-9 minutos por test
- **Herramienta**: `ramp_test.js`
- **Endpoint**: `/api/videos/upload`
- **Optimizaciones**: HTTP keep-alive activado para reutilización de conexiones

## Resultados Detallados

### Test 0: Smoke Test - Validación Inicial

**Configuración:**
- Concurrent Users: 5
- Duration: 60 segundos
- Total Duration: 61.73 segundos

**Métricas de Rendimiento:**
- Total Requests: 109
- Successful Requests: 109
- Failed Requests: 0
- Success Rate: **100.00%** 
- Throughput: 1.77 requests/segundo

**Tiempos de Respuesta:**
- Average: 2,701.79 ms (2.7 segundos)
- Minimum: 1,679 ms
- Maximum: 5,865 ms

**Análisis:**
- El sistema responde correctamente bajo carga mínima
- Tiempos de respuesta muy aceptables (promedio de 2.7 segundos)
- Sin errores, confirmando que el sistema está operativo y estable
- Throughput consistente de 1.77 req/seg con 5 usuarios
- Este test valida que la infraestructura básica funciona antes de aplicar cargas más intensivas

**Distribución de Requests por Usuario:**
- User 1: 22 requests
- User 2: 22 requests
- User 3: 23 requests
- User 4: 20 requests
- User 5: 22 requests

---

### Test 1: 100 Usuarios Concurrentes (Ejecución 1)

**Configuración:**
- Max Users: 100
- Ramp-Up: 180 segundos (3 minutos)
- Hold: 300 segundos (5 minutos)
- Total Duration: 523.53 segundos (8.73 minutos)

**Métricas de Rendimiento:**
- Total Requests: 928
- Successful Requests: 896
- Failed Requests: 32
- Success Rate: **96.55%** 
- Throughput: 1.77 requests/segundo

**Tiempos de Respuesta:**
- Average: 44,736.55 ms (44.7 segundos)
- Minimum: 1,581 ms
- Maximum: 120,433 ms (120.4 segundos)
- P50 (Median): 42,729 ms
- P95: 85,999 ms (86 segundos)
- P99: 110,485 ms (110.5 segundos)

**Análisis de Degradación:**
- Ramp-Up Avg Response Time: 28,779.70 ms
- Hold Phase Avg Response Time: 54,214.80 ms
- Performance Degradation: **88.38%** 
- **WARNING**: Degradación significativa detectada (>50%)

**Distribución de Errores:**
- Status 500 (Internal Server Error): 3 errores
- Status 504 (Gateway Timeout): 26 errores
- UNKNOWN (ETIMEDOUT): 3 errores

**Análisis:**
- La tasa de éxito es aceptable (96.55%), pero la degradación del 88% indica que el sistema se ve afectado significativamente bajo carga sostenida
- Los errores 504 son predominantes, sugiriendo que el servidor o el load balancer están tardando demasiado en procesar las peticiones
- Los tiempos de respuesta promedio son altos (44.7 segundos), lo cual puede no ser aceptable para una experiencia de usuario óptima

---

### Test 2: 100 Usuarios Concurrentes (Ejecución 2)

**Configuración:**
- Max Users: 100
- Ramp-Up: 180 segundos (3 minutos)
- Hold: 300 segundos (5 minutos)
- Total Duration: 545.55 segundos (9.09 minutos)

**Métricas de Rendimiento:**
- Total Requests: 999
- Successful Requests: 740
- Failed Requests: 259
- Success Rate: **74.07%** 
- Throughput: 1.83 requests/segundo

**Tiempos de Respuesta:**
- Average: 41,850.75 ms (41.9 segundos)
- Minimum: 1,283 ms
- Maximum: 81,108 ms (81.1 segundos)
- P50 (Median): 39,511 ms
- P95: 67,622 ms (67.6 segundos)
- P99: 75,716 ms (75.7 segundos)

**Análisis de Degradación:**
- Ramp-Up Avg Response Time: 6,606.79 ms
- Hold Phase Avg Response Time: 46,776.31 ms
- Performance Degradation: **608.00%** 
- **WARNING**: Degradación severa detectada

**Distribución de Errores:**
- Status 500 (Internal Server Error): 52 errores
- Status 504 (Gateway Timeout): 207 errores

**Análisis:**
- Esta ejecución muestra resultados significativamente peores que la primera
- La tasa de éxito del 74.07% está por debajo del umbral aceptable del 95%
- La degradación del 608% es extremadamente alta, indicando que el sistema colapsa bajo carga sostenida
- El alto número de errores 500 y 504 sugiere problemas de estabilidad del servidor o del load balancer
- Esta variabilidad entre ejecuciones indica falta de consistencia en el sistema

---

### Test 3: 200 Usuarios Concurrentes

**Configuración:**
- Max Users: 200
- Ramp-Up: 180 segundos (3 minutos)
- Hold: 300 segundos (5 minutos)
- Total Duration: 573.00 segundos (9.55 minutos)

**Métricas de Rendimiento:**
- Total Requests: 890
- Successful Requests: 865
- Failed Requests: 25
- Success Rate: **97.19%** 
- Throughput: 1.55 requests/segundo

**Tiempos de Respuesta:**
- Average: 99,676.49 ms (99.7 segundos)
- Minimum: 2,309 ms
- Maximum: 177,036 ms (177 segundos)
- P50 (Median): 108,987 ms (109 segundos)
- P95: 149,072 ms (149 segundos)
- P99: 162,979 ms (163 segundos)

**Análisis de Degradación:**
- Ramp-Up Avg Response Time: 81,400.07 ms
- Hold Phase Avg Response Time: 115,692.42 ms
- Performance Degradation: **42.13%** 
- **CAUTION**: Degradación moderada detectada (>20%)

**Distribución de Errores:**
- Status 504 (Gateway Timeout): 23 errores
- UNKNOWN (ETIMEDOUT): 2 errores

**Análisis:**
- Sorprendentemente, 200 usuarios muestra mejor tasa de éxito (97.19%) que ambas ejecuciones de 100 usuarios
- La degradación del 42.13% es más controlada que en las pruebas de 100 usuarios
- Sin embargo, los tiempos de respuesta son muy altos (promedio de 99.7 segundos)
- El P95 de 149 segundos es inaceptable para la mayoría de aplicaciones
- La menor tasa de errores sugiere que el sistema maneja mejor la carga cuando está más distribuida

---

## Comparativa de Resultados

| Métrica | Smoke Test (5 Users) | 100 Users (Ejec 1) | 100 Users (Ejec 2) | 200 Users |
|---------|---------------------|-------------------|-------------------|-----------|
| Success Rate | 100.00% | 96.55% | 74.07%  | 97.19%  |
| Avg Response Time | 2.7s | 44.7s | 41.9s | 99.7s |
| P95 Response Time | N/A | 86s | 67.6s | 149s |
| Performance Degradation | N/A | 88.38% | 608% | 42.13% |
| Error Rate | 0% | 3.45% | 25.93% | 2.81% |
| Throughput | 1.77 req/s | 1.77 req/s | 1.83 req/s | 1.55 req/s |
| Users | 5 | 100 | 100 | 200 |
| Duration | 60s | 523.5s | 545.6s | 573.0s |

## Conclusiones

### 0. Validación Inicial (Smoke Test)

- El smoke test con 5 usuarios muestra resultados excelentes:
  - 100% de éxito sin errores
  - Tiempos de respuesta muy aceptables (2.7 segundos promedio)
  - Throughput estable de 1.77 req/seg
- Esto confirma que el sistema funciona correctamente bajo carga mínima
- Los tiempos de respuesta del smoke test (2.7s) son significativamente mejores que en las pruebas de carga (41-99s), indicando que el sistema se degrada rápidamente con más usuarios
- El smoke test es esencial como punto de referencia y validación antes de ejecutar pruebas más intensivas

### 1. Variabilidad e Inestabilidad

- Las dos ejecuciones con 100 usuarios muestran resultados muy diferentes:
  - Ejecución 1: 96.55% éxito
  - Ejecución 2: 74.07% éxito
- Esta variabilidad indica que el sistema no es consistente bajo la misma carga
- Posibles causas:
  - Estado del servidor/cache
  - Condiciones de red variables
  - Problemas de sincronización en el procesamiento

### 2. Paradoja de 200 Usuarios

- A pesar de tener el doble de usuarios, 200 usuarios muestra:
  - Mejor tasa de éxito (97.19%)
  - Menor tasa de errores (2.81%)
  - Degradación más controlada (42.13%)
- Sin embargo:
  - Tiempos de respuesta mucho más altos (99.7s promedio)
  - P95 inaceptablemente alto (149s)
- Esto sugiere que el sistema puede manejar más carga distribuida, pero a costa de tiempos de respuesta muy altos

### 3. Patrones de Errores

- **Errores 504 (Gateway Timeout)**: Predominantes en todos los tests
  - Indica que las peticiones exceden los timeouts del load balancer
  - Sugiere que el procesamiento de videos es demasiado lento
- **Errores 500 (Internal Server Error)**: Más frecuentes en la segunda ejecución de 100 usuarios
  - Indica problemas internos del servidor bajo ciertas condiciones
- **ETIMEDOUT**: Ocurrencias menores pero presentes
  - Conexiones que exceden el timeout de 5 minutos

### 4. Tiempos de Respuesta

- Todos los tests muestran tiempos de respuesta muy altos:
  - Mínimo promedio: 41.9 segundos
  - Máximo promedio: 99.7 segundos
- El P95 está entre 67-149 segundos, lo cual es inaceptable para la mayoría de aplicaciones web
- Esto sugiere que el procesamiento de videos es el cuello de botella principal

## Recomendaciones

### Capacidad Recomendada

1. **Capacidad operativa**: 100 usuarios concurrentes con monitoreo activo
   - Aunque muestra variabilidad, es el punto más balanceado
   - Requiere optimizaciones para mejorar consistencia

2. **Capacidad máxima**: 200 usuarios con advertencias
   - Funciona pero con tiempos de respuesta inaceptables
   - Solo para casos donde la latencia no es crítica

### Optimizaciones Prioritarias

1. **Procesamiento de Videos**:
   - Optimizar la validación de videos antes de subir a S3
   - Implementar procesamiento asíncrono más eficiente
   - Considerar pre-procesamiento o validación más rápida

2. **Manejo de Conexiones**:
   - Aunque se implementó keep-alive, puede necesitarse ajuste de pools
   - Revisar configuración del load balancer para timeouts
   - Optimizar el manejo de conexiones concurrentes en el servidor

3. **Timeouts y Retry Logic**:
   - Ajustar timeouts del load balancer
   - Implementar retry logic más inteligente
   - Considerar circuit breakers para prevenir cascading failures

4. **Monitoreo y Alertas**:
   - Implementar alertas cuando la degradación exceda 50%
   - Monitorear tasa de errores 504 y 500
   - Alertas cuando el P95 exceda umbrales aceptables

### Pruebas Adicionales Recomendadas

1. **Prueba de Estabilidad**: 80 usuarios durante 10 minutos
   - Validar estabilidad a largo plazo
   - Confirmar que no hay memory leaks o degradación progresiva

2. **Prueba de Stress**: Incrementar gradualmente hasta encontrar el punto de falla
   - Identificar el límite absoluto del sistema
   - Entender el comportamiento en condiciones extremas

3. **Prueba de Recuperación**: Simular fallo y recuperación
   - Validar que el sistema se recupera correctamente
   - Medir tiempo de recuperación

## Criterios de Aceptación

### Criterios Actuales (No Cumplidos)

-  P95 < 1 segundo: **FALLIDO** (P95 entre 67-149 segundos)
-  Success Rate > 95%: **PARCIAL** (74-97% dependiendo de ejecución)
-  Performance Degradation < 20%: **FALLIDO** (42-608% de degradación)

### Criterios Ajustados (Realistas)

-  Success Rate > 95%: **PARCIALMENTE CUMPLIDO**
-  P95 < 30 segundos: **FALLIDO** (requiere optimización significativa)
-  Performance Degradation < 50%: **PARCIAL** (solo en 200 usuarios)

## Métricas de Infraestructura

*Nota: Las métricas de CPU, memoria y otros recursos de AWS deberían ser capturadas durante las pruebas y agregadas aquí para un análisis completo.*

## Próximos Pasos

1. Implementar optimizaciones identificadas
2. Ejecutar prueba de estabilidad con 80 usuarios
3. Re-ejecutar pruebas de 100 usuarios para validar mejoras
4. Documentar métricas de infraestructura durante las pruebas
5. Establecer SLAs realistas basados en los resultados actuales
