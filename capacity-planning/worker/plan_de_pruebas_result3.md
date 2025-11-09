# Resultados de Pruebas de Rendimiento 2 (50 MB)

---

## Caso A — 1 Worker · 4 Threads · 50 MB

### Prueba de Saturación
**Gráfica:**  
https://snapshots.raintank.io/dashboard/snapshot/EeHjW6hOlGoBQrGCrX6c0mkorbwpPIqb?orgId=0&refresh=5s

| Métrica | Valor |
|--------|-------|
| Throughput máximo | ~8.00 videos/min |
| Punto de saturación (cola) | ~2212 tareas |
| Tiempo medio de servicio | ~35.5 s |
| p95 latencia | ~10 s |
| Tasa de éxito | 100% |
| Errores totales | 0 |
| Cuello de botella identificado | I/O |

---

### Prueba Sostenida
**Gráfica:**  
https://snapshots.raintank.io/dashboard/snapshot/EeHjW6hOlGoBQrGCrX6c0mkorbwpPIqb?orgId=0&refresh=5s

| Métrica | Valor |
|--------|-------|
| Throughput promedio | ~1.30 videos/min |
| Throughput std dev | ~2.04 videos/min |
| Tendencia de cola | Fuertemente creciente |
| Tiempo servicio promedio | ~174 s |
| Tasa de éxito | 100% |
| Estado |  (No sostenible, cola crece) |

---

## Caso B — 1 Worker · 1 Thread · 50 MB

### Prueba de Saturación
**Gráfica:**  
https://snapshots.raintank.io/dashboard/snapshot/EeHjW6hOlGoBQrGCrX6c0mkorbwpPIqb?orgId=0&refresh=5s

| Métrica | Valor |
|--------|-------|
| Throughput máximo | ~10.33 videos/min |
| Tiempo medio de servicio | ~34.4 s |
| p95 latencia | ~10 s |
| Tasa de éxito | 100% |

---

### Prueba Sostenida
**Gráfica:**  
https://snapshots.raintank.io/dashboard/snapshot/EeHjW6hOlGoBQrGCrX6c0mkorbwpPIqb?orgId=0&refresh=5s

| Métrica | Valor |
|--------|-------|
| Throughput promedio | ~9.33 videos/min |
| Tendencia de cola | Negativa (cola drenando) |
| Tiempo servicio promedio | ~35 s |
| Estado | (Sostenible) |

---

## Conclusiones

- Como visto en el plan de pruebas 1, en contenedores localmente las conclusiones se mantienen
- 4 threads producen mayor *throughput pico* pero no son sostenibles: la cola crece → saturación real
- 1 thread mantuvo estabilidad: throughput bajo pero cola drenando → operación estable
- El cuello de botella predominante fue I/O (no CPU)
- Para cargas sostenidas, escalar threads **sin controlar I/O** degrada el sistema

