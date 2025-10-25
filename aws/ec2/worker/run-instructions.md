# Requirements

- Before continue run the common initial configuration, [here](../initial-configuration.md)

# Build image

```bash
docker build -t worker .
```

# Run image

```bash
docker run -d -p 9090:9090 --name worker worker
```
