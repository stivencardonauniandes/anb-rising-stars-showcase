# Resultados de Pruebas de Rendimiento 4 (50 MB) - SQS

---

## Caso A — 1 Worker · 4 Threads · 50 MB

### Prueba de Saturación
**Gráficas:**  
- [Dashboard 1](https://snapshots.raintank.io/dashboard/snapshot/rmpJhGU1m3elUWre6kdupR6zF6Nr53W5?orgId=0&from=1763241724628&to=1763242327337)
- [Dashboard 2](https://snapshots.raintank.io/dashboard/snapshot/Wb2XxSFytAF6A5EqOvNzBmau7KTWYtvm?orgId=0&refresh=5s)
- [Dashboard 3](https://snapshots.raintank.io/dashboard/snapshot/91P6sm4ccQFWcn4vKekm8QXKjfHnLNze?orgId=0&from=1763241780000&to=1763243026398)


| Métrica | Valor |
|--------|-------|
| Throughput máximo | 10.7 (videos/min) |
| Punto de saturación (cola) | 662 mensajes |
| Tiempo medio de servicio | ~21.55s |
| p95 latencia | 10s |
| Tasa de éxito | 92.5% |
| Errores totales | 9 |
| Cuello de botella identificado | I/O |

---

### Prueba Sostenida
**Gráfica:**  
- [Dashboard 1](https://snapshots.raintank.io/dashboard/snapshot/0FkNHrMM69ThlJWAUauZSowPzLZDNa7m?orgId=0&refresh=5s)
- [Dashboard 2](https://snapshots.raintank.io/dashboard/snapshot/RAzxfaP1iwGf3HI9XsCG7p2SMH0xQChF?orgId=0&refresh=5s)
- [Dashboard 3](https://snapshots.raintank.io/dashboard/snapshot/FnaUZ2qkVtScY8uvGraEviqBOghJn70v?orgId=0)


| Métrica | Valor |
|--------|-------|
| Throughput promedio | 4.92 (videos/min) |
| Throughput std dev | 2.38 |
| Tendencia de cola | Creciente con punto máximo en 340 videos |
| Tiempo servicio promedio | 10.18s |
| Tasa de éxito | 87.3% |
| Estado | (No sostenible, cola creciente) |

---

## Caso B — 1 Worker · 1 Thread · 50 MB

### Prueba de Saturación
**Gráfica:**
- [Dashboard 1](https://snapshots.raintank.io/dashboard/snapshot/qkgHF0a3gU2xsbjJ42QlB0QAumKqydCr?orgId=0&refresh=5s)
- [Dashboard 2](https://snapshots.raintank.io/dashboard/snapshot/QDd46hwGD9zmEMn3mz8MLc1YWwwoHwLl?orgId=0&refresh=5s)
- [Dashboard 3](https://snapshots.raintank.io/dashboard/snapshot/d6bUT3LorlgVwE8r38gtrYeyPYI9o26e?orgId=0)


| Métrica | Valor |
|--------|-------|
| Throughput máximo | 24.0 (videos/min) |
| Tiempo medio de servicio | 12.75 seg |
| p95 latencia | 10seg |
| Tasa de éxito | 100% |

---

### Prueba Sostenida
**Gráfica:**  
- [Dashboard 1](https://snapshots.raintank.io/dashboard/snapshot/0FkNHrMM69ThlJWAUauZSowPzLZDNa7m?orgId=0&refresh=5s)
- [Dashboard 2](https://snapshots.raintank.io/dashboard/snapshot/RAzxfaP1iwGf3HI9XsCG7p2SMH0xQChF?orgId=0&refresh=5s)
- [Dashboard 3](https://snapshots.raintank.io/dashboard/snapshot/FnaUZ2qkVtScY8uvGraEviqBOghJn70v?orgId=0)


| Métrica | Valor |
|--------|-------|
| Throughput promedio | 17.3 |
| Throughput std dev | 3.16 |
| Tendencia de cola | Ligeramente creciente con un pico en 318 |
| Tiempo servicio promedio | 3.3 seg |
| Estado | (Sostenible) |

---

## Conclusiones

- El caso B con 1 Worker y 1 Thread muestra un mejor rendimiento y sostenibilidad en comparación con el Caso A.
- Se recomienda priorizar configuraciones con menor número de threads para optimizar el rendimiento y la estabilidad del sistema.
- En todos los casos el cuello de botella principal identificado fue I/O, sugiriendo que futuras optimizaciones deberían centrarse en mejorar las operaciones de lectura/escritura.

