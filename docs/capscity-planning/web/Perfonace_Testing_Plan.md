
# Escenario 1 - Capacidad de la capa Web (Usuarios concurrentes)

### 1. Escenario **5 usuarios durante 1 minutos para validar que todo responde y la telemetría
está activa.**

## Estadistica

- Total Request : 181
- Average: 1674 MS
- p95 
- Min 324 MS
- Max 2559 MS
- Error 0%

### 2. Ramp iniciar en 0 y aumentar hasta X usuarios en 3 minutos; mantener 5 minutos. Repetir con X creciente (p. ej., 100 → 200 → 300) hasta observar degradación.


## Estadistica

### Test 100 Usuarios
- Total Request : 858
- Average: 26493 MS
- p95 41990
- Min 356 MS
- Max 48305 MS
- Error 77.2%

### Test 200 Usuarios
- Total Request : 932
- Average: 52594 MS
- p95 91641
- Min 323 MS
- Max 116753 MS
- Error 0%
- throughput: 2.6/seg

### Test 300 Usuarios
- Total Request : 988
- Average: 80107 MS
- p95 132557
- Min 35 MS
- Max 152324 MS
- Error 0%
- throughput: 2.5/seg

### 3. Ejecutar 5 minutos en el 80% de X (el mejor nivel previo sin degradación) para confirmar estabilidad.

- Users 200 - Prueba con 160 Users
- Total Request : 920
- Ramp up: 60 Segundos
- Average: 52180 MS
- p95: 70739
- Min 446 MS
- Max 92081 MS
- Error 0%
- throughput: 2.6/seg

