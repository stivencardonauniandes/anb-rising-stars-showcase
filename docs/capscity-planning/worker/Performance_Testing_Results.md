# Resultados de Pruebas de Rendimiento (50 MB)

---

## Caso A — 1 Worker · 4 Threads · 50 MB

### Prueba de Saturación
**Gráfica:**  
https://snapshots.raintank.io/dashboard/snapshot/1ibTPfKRfmMOME6XMsDSpGZdRQAEmEgt

| Métrica | Valor |
|--------|-------|
| Throughput máximo | ~4.00 videos/min |
| Punto de saturación (cola) | ~2212 tareas |
| Tiempo medio de servicio | ~182.4 s |
| p95 latencia | ~10 s |
| Tasa de éxito | 100% |
| Errores totales | 0 |
| Cuello de botella identificado | I/O |

---

### Prueba Sostenida
**Gráfica:**  
https://snapshots.raintank.io/dashboard/snapshot/zoY68UfqoDXSpSwRHtdyrA5PTB4OGqQY

| Métrica | Valor |
|--------|-------|
| Throughput promedio | ~1.30 videos/min |
| Throughput std dev | ~2.04 videos/min |
| Tendencia de cola | Fuertemente creciente |
| Tiempo servicio promedio | ~174 s |
| Tasa de éxito | 100% |
| Estado | ❌ (No sostenible, cola crece) |

---

## Caso B — 1 Worker · 1 Thread · 50 MB

### Prueba de Saturación
**Gráfica:**  
https://snapshots.raintank.io/dashboard/snapshot/VmiHu6if3Q5MPrzBpVBpV6o8R2osRLyb

| Métrica | Valor |
|--------|-------|
| Throughput máximo | ~1.33 videos/min |
| Tiempo medio de servicio | ~43.7 s |
| p95 latencia | ~10 s |
| Tasa de éxito | 100% |

---

### Prueba Sostenida
**Gráfica:**  
https://snapshots.raintank.io/dashboard/snapshot/YLu3mjXfyBnnRT5CMrqjWSU6fRcMsEZJ

| Métrica | Valor |
|--------|-------|
| Throughput promedio | ~1.63 videos/min |
| Throughput std dev | ~0.84 videos/min |
| Tendencia de cola | Negativa (cola drenando) |
| Tiempo servicio promedio | ~34.3 s |
| Estado | ✅ (Sostenible) |

---

## Conclusiones

- 4 threads producen mayor *throughput pico* pero no son sostenibles: la cola crece → saturación real
- 1 thread mantuvo estabilidad: throughput bajo pero cola drenando → operación estable
- El cuello de botella predominante fue I/O (no CPU)
- Para cargas sostenidas, escalar threads **sin controlar I/O** degrada el sistema
