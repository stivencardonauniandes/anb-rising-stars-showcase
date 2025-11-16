# Plan de Pruebas de Rendimiento 4 - Video Worker (SQS)

## Diseño Experimental

### Variables de Prueba

#### 1. Tamaño de Video
- **50 MB**: Videos de corta duración (~2-3 minutos en calidad media)
- **100 MB**: Videos de duración media (~5-6 minutos en calidad media)

#### 2. Concurrencia de Workers
- **1 worker**
- **2 workers**
- **4 workers**

### Matriz de Configuraciones

| Configuración | Workers | Tamaño Video | Descripción |
|--------------|---------|--------------|-------------|
| Config 1     | 1       | 50 MB        | Baseline pequeño |
| Config 2     | 1       | 100 MB       | Baseline grande |
| Config 3     | 2       | 50 MB        | Paralelización 2x pequeño |
| Config 4     | 2       | 100 MB       | Paralelización 2x grande |
| Config 5     | 4       | 50 MB        | Paralelización 4x pequeño |
| Config 6     | 4       | 100 MB       | Paralelización 4x grande |

## Tipos de Pruebas

### 1. Pruebas de Saturación

**Objetivo**: Encontrar el punto de quiebre del sistema

**Metodología**:
1. Iniciar con 1 video en cola
2. Incrementar en pasos de 10 videos por segundo
3. Continuar hasta observar:
   - Cola creciendo sin control (tendencia > 1 video/min)
   - Tiempo de servicio incrementando significativamente (>50% del baseline)
   - Errores frecuentes (>5% tasa de fallo)

**Duración**: 5-10 minutos por configuración

**Criterios de Saturación**:
- Cola crece consistentemente (>10 videos acumulados)
- Throughput se estanca o decrece
- Latencia p95 > 2x latencia promedio baseline

### 2. Pruebas Sostenidas

**Objetivo**: Validar estabilidad bajo carga constante

**Metodología**:
1. Mantener un número fijo   de videos en cola (75% de capacidad nominal)
2. Reponer videos procesados inmediatamente
3. Mantener durante 5-10 minutos

**Duración**: 5 minutos por configuración

**Criterios de Estabilidad**:
- Tamaño de cola estable (variación < ±2 videos)
- Tendencia de cola ≈ 0 (entre -0.1 y 0.1 videos/min)
- Tasa de éxito > 99%
- Throughput consistente (desviación estándar < 10%)

## Métricas a Recolectar

### Métricas Primarias

#### 1. Throughput Observado (X)
```promql
sum(rate(video_worker_tasks_processed_total{status="processed"}[1m])) * 60
```
- **Unidad**: videos procesados por minuto
- **Objetivo**: Máximo posible manteniendo estabilidad

#### 2. Tiempo Medio de Servicio (S)
```promql
rate(video_worker_task_processing_seconds_sum{status="processed"}[1m]) / 
rate(video_worker_task_processing_seconds_count{status="processed"}[1m])
```
- **Unidad**: segundos por video
- **Objetivo**: Mínimo y consistente

#### 3. Tendencia de Cola
```promql
deriv(max(video_worker_stream_size)[5m:]) * 60
```
- **Unidad**: videos/minuto
- **Objetivo**: ≈ 0 (entre -0.1 y 0.1)

### Métricas Secundarias

- **Tasa de éxito**: `(procesados / total) * 100`
- **Percentiles de latencia**: p50, p95, p99
- **Errores de cola**: `sum(video_worker_queue_errors_total)`
- **Distribución por worker**: Throughput individual de cada worker

## Procedimiento de Ejecución

### Preparación

1. **Configurar entorno**:
   ```bash
   # Ajustar número de thread en .env
   export WORKER_POOL_SIZE=N  # N = 1, 2, 4
   ```

2. **Preparar videos de prueba**:
   ```bash
   # Generar videos de 50MB
   ffmpeg -f lavfi -i testsrc=duration=180:size=1280x720:rate=30 \
          -c:v libx264 -preset medium -b:v 2M video_50mb.mp4
   
   # Generar videos de 100MB
   ffmpeg -f lavfi -i testsrc=duration=360:size=1280x720:rate=30 \
          -c:v libx264 -preset medium -b:v 2M video_100mb.mp4
   ```

3. **Limpiar estado**:
   ```bash
   # Limpiar cola SQS
   # (Purgar cola desde AWS Console o CLI)
   
   # Reiniciar workers
   docker-compose restart worker
   ```

## Criterios de Éxito/Fallo

### Éxito

Una configuración es exitosa si cumple:

1. **Capacidad Nominal**:
   - Throughput sostenido > umbral mínimo
   - Para 1 worker: > 3 videos/min (50MB), > 1.5 videos/min (100MB)
   - Para 2 workers: > 6 videos/min (50MB), > 3 videos/min (100MB)
   - Para 4 workers: > 12 videos/min (50MB), > 6 videos/min (100MB)

2. **Estabilidad**:
   - Tendencia de cola entre -0.1 y 0.1 videos/min durante 15+ minutos
   - Desviación estándar de throughput < 10% del promedio
   - Tamaño de cola varía < ±3 videos

3. **Calidad**:
   - Tasa de éxito > 99%
   - Errores de cola < 1% del total de tareas
   - p95 de latencia < 1.5x promedio

### Fallo

Una configuración falla si:

1. **Saturación Prematura**:
   - Cola crece sin control con < 50% de carga esperada
   - Throughput decrece bajo carga moderada

2. **Inestabilidad**:
   - Tendencia de cola > 1 video/min sostenida
   - Variaciones bruscas de throughput (>30%)

3. **Errores Frecuentes**:
   - Tasa de fallo > 5%
   - Errores de cola > 10 por minuto

## Herramientas y Dashboards

### Dashboard de Grafana

Dashboard: **Performance Testing - Experimental Design**
- URL: `http://localhost:3000/d/performance-testing`

### Scripts de Prueba

Ubicación: `/scripts/example_test_workflow/`

## Conclusiones

### Throughput observado


### Throughput del worker


### Worker CPU utilization


