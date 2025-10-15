package metrics

import (
	"time"

	"github.com/prometheus/client_golang/prometheus"
)

type PrometheusMetrics struct {
	processed   *prometheus.CounterVec
	durations   *prometheus.HistogramVec
	queueErrors prometheus.Counter
}

func NewPrometheusMetrics(reg prometheus.Registerer) *PrometheusMetrics {
	m := &PrometheusMetrics{
		processed: prometheus.NewCounterVec(prometheus.CounterOpts{
			Namespace: "video_worker",
			Name:      "tasks_processed_total",
			Help:      "Número total de videos procesados por estado.",
		}, []string{"status"}),
		durations: prometheus.NewHistogramVec(prometheus.HistogramOpts{
			Namespace: "video_worker",
			Name:      "task_processing_seconds",
			Help:      "Histograma del la duración del procesamiento de los videos.",
			Buckets:   prometheus.DefBuckets,
		}, []string{"status"}),
		queueErrors: prometheus.NewCounter(prometheus.CounterOpts{
			Namespace: "video_worker",
			Name:      "queue_errors_total",
			Help:      "Número total de errores.",
		}),
	}

	reg.MustRegister(m.processed, m.durations, m.queueErrors)
	return m
}

func (m *PrometheusMetrics) IncQueueError() {
	m.queueErrors.Inc()
}

func (m *PrometheusMetrics) IncTaskProcessed(status string) {
	m.processed.WithLabelValues(status).Inc()
}

func (m *PrometheusMetrics) ObserveProcessingDuration(status string, d time.Duration) {
	m.durations.WithLabelValues(status).Observe(d.Seconds())
}
