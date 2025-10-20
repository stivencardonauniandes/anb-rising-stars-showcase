# anb-rising-stars-showcase

## Integrantes

- Andres Gomez - ae.gomezh1@uniandes.edu.co
- Stiven Cardona - s.cardona112345@uniandes.edu.co
- Juan Manuel Dominguez - jm.dominguez@uniandes.edu.co
- Alejandro Pulido - d.pulidob@uniandes.edu.co

## SonarQube Reports

- Se pueden examinar los reportes de sonar [aqui](https://sonarcloud.io/summary/new_code?id=miso-cloud-course_anb-rising-stars-showcase&branch=main)

## Cómo ejecutar las pruebas Newman

Para correr la colección de pruebas de Postman usando Newman desde la línea de comandos, utiliza el siguiente comando:

```bash
newman run collections/postman_collection.json -e collections/local.postman_environment.json
```

Este comando ejecutará todos los tests definidos en `collections/postman_collection.json` usando el entorno local especificado en `collections/local.postman_environment.json`. Asegúrate de tener [Newman](https://www.npmjs.com/package/newman) instalado globalmente (`npm install -g newman`) antes de ejecutar el comando.

## Información entrega 1

### Índice

* [Documentación](./docs/Entrega_1.md)
* [Diagramas complementarios](./docs/C4-Diagrams.md)
* [Archivos postman](./collections/)
* [Pruebas de carga](./capacity-planning/)
