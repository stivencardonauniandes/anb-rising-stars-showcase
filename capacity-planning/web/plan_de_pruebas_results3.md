
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



Criterios

p95 > 1 segundo

Prueba fallida  
  

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





Criterios

p95 > 1 segundo

Prueba fallida  

### Test 200 Usuarios
- Total Request : 586
- Average: 89715 MS
- p95 117771 MS
- Min 76946 MS
- Max 131115 MS
- Error 0%
- throughput: 1.4/seg



  
Criterios

p95 > 1 segundo

Prueba fallida  

### Test 300 Usuarios
- Total Request : 556
- Average: 157107 MS
- p95 230732 MS
- Min 77109 MS
- Max 245126 MS
- Error 0.18%
- throughput: 1.2/seg

Criterios

p95 > 1 segundo

<img width="1042" height="654" alt="image" src="https://github.com/user-attachments/assets/3975dc05-0085-45c7-9787-5ae180cd3636" />

Prueba fallida  


## CPU AWS

Web Server
<img width="1645" height="634" alt="image" src="https://github.com/user-attachments/assets/e89bf3be-6e15-4033-aa6e-783c08aa2fe9" />

Next Cloud
<img width="1670" height="629" alt="image" src="https://github.com/user-attachments/assets/888ea535-0d09-4c63-ace4-8b028c7b7678" />

Se evidencia que durante las pruebas el cuello de botella de procesamiento es el servidor de archivos que demora en recibir los archivos a procesar



