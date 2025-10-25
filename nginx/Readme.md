# Steps to execute from docker

1. run ```docker build -t nginx-proxy .```
2. run ``` docker run --env-file .env -p 80:80 --name nginx-proxy-cont nginx-proxy ```
3. If running locally, connect the network to the other containers
``` docker network connect <NETWORK_NAME> <CONTAINER_NAME> ```