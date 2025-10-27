
# Escenario 1 - Capacidad de la capa Web (Usuarios concurrentes)

### 1. Escenario **5 usuarios durante 1 minutos para validar que todo responde y la telemetría
está activa.**

## Estadistica

- Total Request : 696
- Average: 1674 MS
- p95 540
- Min 134 MS
- Max 1510 MS
- Error 0%


Criterios

p95 > 1 segundo
CPU Supero el 127%




Prueba fallida  
  

### 2. Ramp iniciar en 0 y aumentar hasta X usuarios en 3 minutos; mantener 5 minutos. Repetir con X creciente (p. ej., 100 → 200 → 300) hasta observar degradación.


## Estadistica

### Test 100 Usuarios
- Total Request : 858
- Average: 26493 MS
- p95 41990
- Min 356 MS
- Max 48305 MS
- Error 0%



Criterios

p95 > 1 segundo
CPU Supero el 200%



Prueba fallida  

### Test 200 Usuarios
- Total Request : 932
- Average: 52594 MS
- p95 91641
- Min 323 MS
- Max 116753 MS
- Error 0%
- throughput: 2.6/seg


  
Criterios

p95 > 1 segundo
CPU Supero el 200%



Prueba fallida  

### Test 300 Usuarios
- Total Request : 988
- Average: 80107 MS
- p95 132557
- Min 35 MS
- Max 152324 MS
- Error 0%
- throughput: 2.5/seg

Criterios

p95 > 1 segundo
CPU Supero el 200%



Prueba fallida  

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


Criterios

p95 > 1 segundo
CPU Supero el 200%



Prueba fallida




