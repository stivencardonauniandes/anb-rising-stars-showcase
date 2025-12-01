# Resultados de Pruebas de Rendimiento 5 (50 MB) - SQS

---

## Caso — 1 Worker · 4 Threads · 50 MB

### Prueba de Saturación
**Gráficas:**  
- [Dashboard 1](https://snapshots.raintank.io/dashboard/snapshot/Mj8NtlA6ruE9QSOqphkwStsUKs7d32K7?orgId=0)
- [Dashboard 2](https://snapshots.raintank.io/dashboard/snapshot/1s2pdMMiOOxQ6ASu6cKPxRHL3MIJqvkC?orgId=0)


| Métrica | Valor |
|--------|-------|
| Throughput máximo | 25.3 (videos/min) |
| Punto de saturación (cola) | 658 mensajes |
| Tiempo medio de servicio | ~3.75s |
| p95 latencia | 10ss |
| Tasa de éxito | 92.5% |
| Errores totales | 9 |
| Cuello de botella identificado | I/O |

---

### Prueba Sostenida
**Gráfica:**  
- [Dashboard 1](https://snapshots.raintank.io/dashboard/snapshot/68U2Atlodc4TqsHCWdQrhiJkP4x7fugT?orgId=0)
- [Dashboard 2](https://snapshots.raintank.io/dashboard/snapshot/hPistCNJHLD854IGlC1JNmi3MYvECwAW?orgId=0)


| Métrica | Valor |
|--------|-------|
| Throughput promedio | 13.8 (videos/min) |
| Throughput std dev | 6.83 |
| Tendencia de cola | Creciente con punto máximo en 300 videos |
| Tiempo servicio promedio | 4.37s |
| Tasa de éxito | 87.3% |
| Estado | (No sostenible, cola creciente) |

---

## Conclusiones

- La configuración de 1 Worker con 4 Threads alcanza un throughput máximo de 25.3 videos/min en la prueba de saturación, superior al Caso A (10.7 videos/min) del plan anterior, demostrando mejor aprovechamiento de los recursos con esta infraestructura.
- El sistema presenta no sostenibilidad con una carga promedio de 13.8 videos/min, ya que la cola crece constantemente hacia un máximo de 300 mensajes. El tiempo de servicio promedio de 4.37s durante la prueba sostenida es aceptable, pero insuficiente para procesar la carga de entrada de manera equilibrada.
- El cuello de botella identificado sigue siendo I/O, con una tasa de éxito de 87.3% en la prueba sostenida. Se recomienda optimizar las operaciones de lectura/escritura y considerar aumentar a múltiples workers para garantizar sostenibilidad en cargas sostenidas superiores a 13 videos/min.
