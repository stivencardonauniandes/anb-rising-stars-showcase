
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

## Conclusiones

### Comportamiento de la instancia de EC2 1
![EC2 instance 2 behavior](../img/entrega3/EC2%20instance%202.png)
### Comportamiento de la instancia de EC2 2
![EC2 instance 1 behavior](../img/entrega3/EC2%20instance%201.png)

Al ver el uso de CPU de las instancias de EC2 que hacen parte del auto-scaling group y que se utilizan en el proceso de balanceo de carga se puede ver que el proceso de escalamiento es exitoso. Tomando cómo ejemplo las imágenes que se encuentran en más arriba, se puede ver cómo a medida que la carga sobre el sistema crece, se evita que el uso de CPU llegue a un punto crítico (En la capa del servicio web) al balancear la carga entre las instancias. Así mismo, se puede ver cómo a medida que la carga se crece en la istancia uno, se comienza a redirigir tráfico a la instancia 2 (Dónde inicialmente el tráfico es poco y posteriormente comienza a recibir más tráfico). No obstante, la totalidad del sistema si presenta un cuello de botella particular, de esto se hablará en el documento del worker.

