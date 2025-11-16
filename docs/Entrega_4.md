# Documentación entrega 4

## Definición de diagrama entidad-relación
![ERD Diagram](./entrega1_img/ERD.png "ERD")

## Glosario:

|Nombre|Tipo|Descripción|
|------|----|-----------|
|USER|ENTIDAD |Representa a un usuario del sistema. Los usuarios pueden registrarse en el sistema, subir videos para ser votados por otros usuarios o votar.|
|VOTES|RELACIÓN| Representa un voto en el sistema. Es una relación de muchos a muchos, un usuario puede votar por varios videos y un video puede ser votado por múltiples usuarios.|
|VIDEO|ENTIDAD|Es un video que es subido al sistema por un usuario. Los videos son procesados en el backend del sistema. Finalmente, los videos son votados y ranqueados en base al número de votos recibidos.|

## Diagrama de componentes
![Components Diagram](./entrega4_img/Diagrama%20de%20componentes.drawio.png)
## Diagrama de despliegue
![Deployment Diagram](./entrega4_img/ANB%20Rising%20Stars.jpg)
## Diagrama de flujo
![Flow diagram](./entrega1_img/Diagrama%20de%20flujo.png)

## Modificaciones realizadas

1. El servicio de mensajería de Redis es reemplazado por el servicio de Amazon SQS, el cuál actúa cómo cola de mensajes y permite notificar al worker que se debe procesar un video que ya fue recibido en la Api web.

2. Se desacopla el worker del servicio de mensajería, pues a diferencia de la entrega anterior dónde ambos compartían la misma instancia de EC2, ahora ambos se despliegan de forma independiente.

3. El worker se añade a un auto-scaling group el cuál se encargará de ajustar dinámicamente el número de workers de acuerdo con la carga del sistema. Para este caso, se utiliza la CPU cómo métrica a seguir, si la utilización de esta supera el 50%, se añadirá un nuevo worker al sistema.

4. En el caso del worker, al no necesitar de un setup tan largo, para el caso del worker no es utiliza el warm pool. Por el contrario, para la capa web se continúa con el uso de una warm pool para acelerar el proceso de crecimiento.