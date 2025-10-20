
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
<img width="1291" height="811" alt="Screenshot 2025-10-19 at 10 42 17 PM" src="https://github.com/user-attachments/assets/2b111bd8-17e0-4100-abd1-c30e08d81791" />

Criterios

p95 > 1 segundo
CPU Supero el 127%

<img width="744" height="387" alt="image" src="https://github.com/user-attachments/assets/dd788bd7-1f78-434a-a2e1-1faea3387feb" />


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

<img width="1333" height="896" alt="Screenshot 2025-10-19 at 10 38 58 PM" src="https://github.com/user-attachments/assets/c62d7e44-dbbc-4f03-b259-6c97f6deb7b5" />

Criterios

p95 > 1 segundo
CPU Supero el 200%

<img width="723" height="363" alt="image" src="https://github.com/user-attachments/assets/6bbeeb82-e608-4a5d-8064-19e3dbb50fbd" />

Prueba fallida  

### Test 200 Usuarios
- Total Request : 932
- Average: 52594 MS
- p95 91641
- Min 323 MS
- Max 116753 MS
- Error 0%
- throughput: 2.6/seg

  <img width="1368" height="859" alt="Screenshot 2025-10-19 at 10 35 19 PM" src="https://github.com/user-attachments/assets/5db94a61-afa9-4316-8f0f-0287ff10196f" />
  
Criterios

p95 > 1 segundo
CPU Supero el 200%

<img width="723" height="363" alt="image" src="https://github.com/user-attachments/assets/6bbeeb82-e608-4a5d-8064-19e3dbb50fbd" />

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

<img width="723" height="363" alt="image" src="https://github.com/user-attachments/assets/6bbeeb82-e608-4a5d-8064-19e3dbb50fbd" />

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

<img width="723" height="363" alt="image" src="https://github.com/user-attachments/assets/6bbeeb82-e608-4a5d-8064-19e3dbb50fbd" />

Prueba fallida




