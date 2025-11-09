# Documentación Entrega 3

## Definición de diagrama entidad-relación
![ERD Diagram](./entrega1_img/ERD.png "ERD")

## Glosario:

|Nombre|Tipo|Descripción|
|------|----|-----------|
|USER|ENTIDAD |Representa a un usuario del sistema. Los usuarios pueden registrarse en el sistema, subir videos para ser votados por otros usuarios o votar.|
|VOTES|RELACIÓN| Representa un voto en el sistema. Es una relación de muchos a muchos, un usuario puede votar por varios videos y un video puede ser votado por múltiples usuarios.|
|VIDEO|ENTIDAD|Es un video que es subido al sistema por un usuario. Los videos son procesados en el backend del sistema. Finalmente, los videos son votados y ranqueados en base al número de votos recibidos.|

## Diagrama de componentes
![Components Diagram](./entrega3_img/Diagrama%20de%20componentes.drawio.png)
## Diagrama de despliegue
![Deployment Diagram](./entrega3_img/ANB%20Rising%20Stars.jpg)
## Diagrama de flujo
![Flow diagram](./entrega1_img/Diagrama%20de%20flujo.png)

## Modificaciones realizadas
1. La API web se añade a un auto-scaling group para que pueda escalar/decrecer dinámicamente de acuerdo con el tráfico del servicio.
2. Se mueve el componente de Redis(servicio de mensajería) hacia la instacia en la que se encuentra desplegado el worker. Esto con el objetivo de poder realizar el escalamiento de las instancias de EC2 sin preocuparse por que el servicio de redis pueda ser eliminado por el decrecimiento de instancias dentro del auto-scaling group.
3. Se cambia el servicio de almacenamiento utilizado previamente (Nextcloud) por el servicio de storage de amazon S3.
4. Se elimina el punto de entrada previo (web server de NGINX) y en su lugar se utiliza el servicio de Load balancing de Amazon (ELB), esto con el objetivo de poder balancear la carga entre los meimbros del auto-scaling group mencionado previamente.

## Estrategia de escalamiento
Para poder escalar con velocidad y impactando mínimamente el servicio se decide escalar en base al uso de CPU cuándo las instancias alcanzan una utilización de más del 60%. Asímismo, para minimizar el tiempo utilizado en el crecimiento de los servicios se utiliza la estrategia warm-pool. Esta estrategia consiste en que las intancias que serán utilizadas para escalar ya se encuentran en un estado "warm" (puede ser running/stopped/hibernation, en nuetro caso se utilizó stopped) con todas las dependencias ya previamente pre-instaladas. De esta forma, de ser necesario añadir una instancia a funcionamiento activo no es necesario realizar todo el setup.