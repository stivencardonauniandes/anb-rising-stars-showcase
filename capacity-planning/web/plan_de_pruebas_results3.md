
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

### JMETER 

<img width="1149" height="245" alt="image" src="https://github.com/user-attachments/assets/2dd2477c-3e79-4321-ae40-0e74a3d5d595" />

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

### JMETER

<img width="1160" height="748" alt="image" src="https://github.com/user-attachments/assets/89610e7e-13e3-4d74-aaaa-4bd914fc3cb3" />

<img width="1197" height="321" alt="image" src="https://github.com/user-attachments/assets/14980b73-dc03-4e37-9c47-38f7100e1a9f" />



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

<img width="1169" height="742" alt="image" src="https://github.com/user-attachments/assets/332fa11d-150b-435d-b10e-41ed62773ce3" />


  
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
- throughput: 1.4/seg

Criterios

p95 > 1 segundo

<img width="1208" height="430" alt="image" src="https://github.com/user-attachments/assets/37e17ef5-37ce-4337-b782-6871427b1293" />


Prueba fallida  


## Grafana

Metricas https://snapshots.raintank.io/dashboard/snapshot/PRb2JgN0Ql786vrHXGDw8teG2ONz64nM

## CPU AWS

Web Server
<img width="1485" height="540" alt="image" src="https://github.com/user-attachments/assets/7feb9be6-24de-4e52-a4c6-61f8aae960c7" />

<img width="1509" height="556" alt="image" src="https://github.com/user-attachments/assets/8138d165-21dc-4114-9ce9-f6e780285fc8" />

Workers

<img width="1472" height="767" alt="image" src="https://github.com/user-attachments/assets/6753ac58-6a65-4c51-807e-2eb334b6329d" />


## Conclusiones

### Web Server

1. Se evidencia que el api server demora mucho en la validacion de los videos antes de subir a s3
2. Se debe mejorar la concurrencia de proceso de request, ya que es muy poca lo que genera tener mucho delay en los requests

### Worker

Se evidencia que durante las pruebas el cuello de botella de procesamiento es el servidor de archivos que demora en recibir los archivos a procesar



