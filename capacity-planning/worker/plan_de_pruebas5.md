# Plan de Pruebas 5 - 1 Worker · 4 Threads (50 MB)

---

## Objetivo

Evaluar el rendimiento y comportamiento de un único worker con 4 threads procesando archivos de 50 MB a través de SQS, identificando puntos de saturación, cuello de botellas y la sostenibilidad del sistema bajo esta configuración.

---

## Configuración del Entorno

| Parámetro | Valor |
|-----------|-------|
| Número de Workers | 1 |
| Threads por Worker | 4 |
| Tamaño de archivo | 50 MB |
| Cola de mensajes | SQS |
| Duración de prueba | TBD |
| Carga inicial | TBD |

---

## Casos de Prueba

### Caso 1: Prueba de Saturación

**Objetivo:** Determinar el máximo throughput y el punto en el que el sistema se satura.

**Metodología:**
- Incrementar gradualmente la carga de entrada hasta identificar saturación
- Monitorear métricas de rendimiento en tiempo real
- Registrar el punto de quiebre del sistema

**Métricas a Recolectar:**
- Throughput máximo (videos/min)
- Punto de saturación (tamaño de cola en mensajes)
- Tiempo medio de servicio (segundos)
- p95 latencia
- Tasa de éxito (%)
- Errores totales
- Cuello de botella identificado

**Criterios de Aceptación:**
- Sistema debe procesar videos sin degradación significativa hasta el punto de saturación
- Latencia p95 debe mantenerse bajo 15 segundos
- Tasa de éxito mínima: 90%

---

### Caso 2: Prueba Sostenida

**Objetivo:** Validar si el sistema puede mantener una carga consistente sin degradación de rendimiento a lo largo del tiempo.

**Metodología:**
- Establecer una carga de trabajo predefinida (inferior a la saturación)
- Mantener la carga constante durante un período prolongado (mínimo 30 minutos)
- Monitorear estabilidad y tendencias

**Métricas a Recolectar:**
- Throughput promedio (videos/min)
- Desviación estándar del throughput
- Tendencia de la cola (creciente, decreciente, estable)
- Tamaño máximo de cola observado
- Tiempo de servicio promedio (segundos)
- Tasa de éxito (%)
- Estado de sostenibilidad

**Criterios de Aceptación:**
- Throughput debe ser consistente (desv. estándar < 25% del promedio)
- Cola no debe crecer indefinidamente
- Tasa de éxito mínima: 95%

---

## Instrumentación y Monitoreo

**Dashboards Grafana:**
- Dashboard 1: Métricas de throughput y latencia
- Dashboard 2: Uso de recursos (CPU, memoria)
- Dashboard 3: Estado de la cola SQS y errores

**Logs:**
- Registrar todos los eventos de procesamiento
- Capturar errores y excepciones
- Documentar cambios significativos en el comportamiento

---

## Entregables Esperados

1. Gráficas de throughput vs. tiempo para ambas pruebas
2. Histogramas de latencia
3. Datos de utilización de recursos
4. Tabla comparativa de métricas
5. Identificación de cuello de botella principal
6. Recomendaciones de optimización

---

## Notas

- Basado en resultados del plan de pruebas 4 (Caso A: 1 Worker · 4 Threads)
- Considerar repetir pruebas múltiples veces para validar consistencia
- Documentar cualquier anomalía o comportamiento inesperado
