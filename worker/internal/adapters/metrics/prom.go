package metrics

import (
	"time"

	"github.com/prometheus/client_golang/prometheus"
)

type PrometheusMetrics struct {
	processed   *prometheus.CounterVec
	durations   *prometheus.HistogramVec
	queueErrors *prometheus.CounterVec
	streamSize  *prometheus.GaugeVec
}

func NewPrometheusMetrics(reg prometheus.Registerer) *PrometheusMetrics {
	m := &PrometheusMetrics{
		processed: prometheus.NewCounterVec(prometheus.CounterOpts{
			Namespace: "video_worker",
			Name:      "tasks_processed_total",
			Help:      "Número total de videos procesados por estado.",
		}, []string{"status", "worker_id"}),
		durations: prometheus.NewHistogramVec(prometheus.HistogramOpts{
			Namespace: "video_worker",
			Name:      "task_processing_seconds",
			Help:      "Histograma del la duración del procesamiento de los videos.",
			Buckets:   prometheus.DefBuckets,
		}, []string{"status", "worker_id"}),
		queueErrors: prometheus.NewCounterVec(prometheus.CounterOpts{
			Namespace: "video_worker",
			Name:      "queue_errors_total",
			Help:      "Número total de errores.",
		}, []string{"worker_id"}),
		streamSize: prometheus.NewGaugeVec(prometheus.GaugeOpts{
			Namespace: "video_worker",
			Name:      "stream_size",
			Help:      "Tamaño actual del stream de Redis.",
		}, []string{"worker_id"}),
	}

	reg.MustRegister(m.processed, m.durations, m.queueErrors, m.streamSize)
	return m
}

func (m *PrometheusMetrics) IncQueueError(workerID string) {
	m.queueErrors.WithLabelValues(workerID).Inc()
}

func (m *PrometheusMetrics) IncTaskProcessed(status string, workerID string) {
	m.processed.WithLabelValues(status, workerID).Inc()
}

func (m *PrometheusMetrics) ObserveProcessingDuration(status string, workerID string, d time.Duration) {
	m.durations.WithLabelValues(status, workerID).Observe(d.Seconds())
}

func (m *PrometheusMetrics) SetStreamSize(workerID string, size int64) {
	m.streamSize.WithLabelValues(workerID).Set(float64(size))
}
