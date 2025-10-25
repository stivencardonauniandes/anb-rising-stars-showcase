# Requirements

- Before continue run the common initial configuration, [here](../initial-configuration.md)

# Build image

```bash
docker build -t redis .
```

# Run image

```bash
docker run -d \
  -p 6379:6379 \
  -v redis_data:/data \
  --name redis \
  redis
```
