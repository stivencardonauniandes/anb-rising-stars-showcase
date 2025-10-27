
# Escenario 1 - Capacidad de la capa Web (Usuarios concurrentes)

### 1. Escenario **5 usuarios durante 1 minutos para validar que todo responde y la telemetría
está activa.**

## Estadistica

- Total Request : 21
- Average: 17220 MS
- p95 34611 MS
- Min 6719 MS
- Max 50209 MS
- Error 0%
<img width="1361" height="898" alt="image" src="https://github.com/user-attachments/assets/05799d03-0662-4525-8b4e-0d14eaf10294" />


Criterios

p95 > 1 segundo

Prueba fallida  
  

### 2. Ramp iniciar en 0 y aumentar hasta X usuarios en 3 minutos; mantener 5 minutos. Repetir con X creciente (p. ej., 100 → 200 → 300) hasta observar degradación.


## Estadistica

### Test 100 Usuarios
- Total Request : 430
- Average: 153531 MS
- p95 277468
- Min 1246 MS
- Max 310863 MS
- Error 0%

<img width="1148" height="727" alt="image" src="https://github.com/user-attachments/assets/9a9e1483-c106-422d-96a2-63aefc9a93e5" />



Criterios

p95 > 1 segundo

Prueba fallida  

### Test 200 Usuarios
- Total Request : 240
- Average: 354853 MS
- p95 462883
- Min 5571 MS
- Max 490011 MS
- Error 15%
- throughput: 22.0/seg

<img width="977" height="640" alt="image" src="https://github.com/user-attachments/assets/22d5a62f-a48f-4159-bc74-6cabc63916e4" />

  
Criterios

p95 > 1 segundo

Prueba fallida  

### Test 300 Usuarios
- Total Request : 100
- Average: 80107 MS
- p95 132557
- Min 35 MS
- Max 428600 MS
- Error 100%
- throughput: 9515/seg

Criterios

p95 > 1 segundo

<img width="1042" height="654" alt="image" src="https://github.com/user-attachments/assets/3975dc05-0085-45c7-9787-5ae180cd3636" />

Prueba fallida  

### 3. Ejecutar 5 minutos en el 80% de X (el mejor nivel previo sin degradación) para confirmar estabilidad.

- Users 200 - Prueba con 160 Users
- Total Request : 391
- Ramp up: 60 Segundos
- Average: 148802 MS
- p95: 334292
- Min 316 MS
- Max 371924 MS
- Error 61.38%
- throughput: 40.4/seg


Criterios

p95 > 1 segundo

<img width="1366" height="651" alt="image" src="https://github.com/user-attachments/assets/a4fb2240-bea9-4454-be93-b4af2424ce64" />


Prueba fallida



