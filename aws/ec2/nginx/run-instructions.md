# Requirements

- Before continue run the common initial configuration, [here](../initial-configuration.md)

# Clone the repository

```bash
git clone https://github.com/stivencardonauniandes/anb-rising-stars-showcase.git
```

# Copy the api folder to the root

```bash
cp ./anb-rising-stars-showcase/nginx ./nginx -r
```

# Join in the api folder

```bash
cd api
```

# Build image

```bash
docker build -t nginx-proxy .
```

# Run image

```bash
docker run -d --env-file .env -p 80:80 --name nginx-proxy-cont nginx-proxy
```

docker run --env-file .env -p 80:80 --name nginx-proxy-cont nginx-proxy
