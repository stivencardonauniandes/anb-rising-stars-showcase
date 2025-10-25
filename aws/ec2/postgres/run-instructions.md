# Requirements

- Before continue run the common initial configuration, [here](../initial-configuration.md)

# Build image

```bash
docker build -t postgres .
```

# Run image

```bash
docker run -d \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  --name postgres \
  postgres
```
