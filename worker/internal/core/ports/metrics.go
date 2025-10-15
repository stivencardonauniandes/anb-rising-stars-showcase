package ports

import "time"

type Metrics interface {
	IncQueueError()
	IncTaskProcessed(status string)
	ObserveProcessingDuration(status string, d time.Duration)
}
