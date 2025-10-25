# Requirements

- Before continue run the common initial configuration, [here](../initial-configuration.md)

# Clone the repository

```bash
git clone https://github.com/stivencardonauniandes/anb-rising-stars-showcase.git
```

# Copy the api folder to the root

```bash
cp ./anb-rising-stars-showcase/next_cloud ./nextcloud/next_cloud -r
```

# Join in the api folder

```bash
cd nextcloud
```

# Copy the dockerfile

```bash
cp ./anb-rising-stars-showcase/aws/ec2/next_cloud ./nextcloud/next_cloud -r
```

# Build image

```bash
docker build -t nextcloud .
```

# Run image

```bash
docker run -d \
  -p 8080:80 \
  -v nextcloud_data:/var/www/html \
  --name nextcloud \
  nextcloud
```
