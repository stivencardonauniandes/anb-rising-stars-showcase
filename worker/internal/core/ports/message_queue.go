package ports

import (
	"context"
	"errors"

	"github.com/alejandro/video-worker/internal/core/domain"
)

var ErrNoMessages = errors.New("no messages available")

type QueueMessage struct {
	ID   string
	Task domain.Task
	Raw  map[string]any
}

// MessageQueue describes the contract for consuming task messages.
type MessageQueue interface {
	// Fetch retrieves the next available task message for this consumer.
	// It should block until a message is available or the context is canceled.
	Fetch(ctx context.Context) (*QueueMessage, error)
	// Ack acknowledges successful processing and removes the message from the queue.
	Ack(ctx context.Context, msg *QueueMessage) error
	// Fail marks a message as failed and optionally requeues it for retry.
	Fail(ctx context.Context, msg *QueueMessage, err error) error
}
