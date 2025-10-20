# anb-rising-stars-showcase

## Integrantes

- Andres Gomez
- Stiven Cardona
- Juan Manuel Dominguez
- Alejandro Pulido

## SonarQube Reports

- Se pueden examinar los reportes de sonar [aqui](https://sonarcloud.io/summary/new_code?id=miso-cloud-course_anb-rising-stars-showcase&branch=main)

## Cómo ejecutar las pruebas Newman

Para correr la colección de pruebas de Postman usando Newman desde la línea de comandos, utiliza el siguiente comando:

```bash
newman run collections/postman_collection.json -e collections/local.postman_environment.json
```

Este comando ejecutará todos los tests definidos en `collections/postman_collection.json` usando el entorno local especificado en `collections/local.postman_environment.json`. Asegúrate de tener [Newman](https://www.npmjs.com/package/newman) instalado globalmente (`npm install -g newman`) antes de ejecutar el comando.
