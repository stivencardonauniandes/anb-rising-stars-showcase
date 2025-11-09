
# Escenario 1 - Capacidad de la capa Web (Usuarios concurrentes)

### 1. Escenario **5 usuarios durante 1 minutos para validar que todo responde y la telemetría
está activa.**

## Estadistica

- Total Request : 5
- Average: 79779 MS
- p95 81276 MS
- Min 78848 MS
- Max 81276 MS
- Error 0%
- throughput: 3.7/min

### 2. Ramp iniciar en 0 y aumentar hasta X usuarios en 3 minutos; mantener 5 minutos. Repetir con X creciente (p. ej., 100 → 200 → 300) hasta observar degradación.


## Estadistica

### Test 100 Usuarios
- Total Request : 318
- Average: 78178 MS
- p95 80383 MS
- Min 76866 MS
- Max 98779 MS
- Error 0%
- throughput: 50.6/min

### Test 200 Usuarios
- Total Request : 586
- Average: 89715 MS
- p95 117771 MS
- Min 76946 MS
- Max 131115 MS
- Error 0%
- throughput: 1.4/seg

### Test 300 Usuarios
- Total Request : 556
- Average: 157107 MS
- p95 230732 MS
- Min 77109 MS
- Max 245126 MS
- Error 0.18%
- throughput: 1.2/seg
