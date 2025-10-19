package ports

import "time"

type Metrics interface {
	IncQueueError(workerID string)
	IncTaskProcessed(status string, workerID string)
	ObserveProcessingDuration(status string, workerID string, d time.Duration)
	SetStreamSize(workerID string, size int64)
}
