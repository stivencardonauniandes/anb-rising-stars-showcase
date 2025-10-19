package redis

import (
	"context"
	"errors"
	"fmt"
	"strconv"
	"time"

	redislib "github.com/redis/go-redis/v9"
	"go.uber.org/zap"

	"github.com/alejandro/video-worker/internal/core/domain"
	"github.com/alejandro/video-worker/internal/core/ports"
)

type StreamQueue struct {
	client        *redislib.Client
	stream        string
	group         string
	consumer      string
	blockTimeout  time.Duration
	maxDeliveries int
	logger        *zap.Logger
	metrics       ports.Metrics
}

func NewStreamQueue(
	ctx context.Context,
	client *redislib.Client,
	stream string,
	group string,
	consumer string,
	blockTimeout time.Duration,
	maxDeliveries int,
	logger *zap.Logger,
	metrics ports.Metrics,
) (*StreamQueue, error) {
	if logger == nil {
		logger = zap.NewNop()
	}
	if err := client.XGroupCreateMkStream(ctx, stream, group, "0").Err(); err != nil {
		if err.Error() != "BUSYGROUP Consumer Group name already exists" {
			return nil, fmt.Errorf("create consumer group: %w", err)
		}
	}

	return &StreamQueue{
		client:        client,
		stream:        stream,
		group:         group,
		consumer:      consumer,
		blockTimeout:  blockTimeout,
		maxDeliveries: maxDeliveries,
		logger:        logger,
		metrics:       metrics,
	}, nil
}

func (q *StreamQueue) Fetch(ctx context.Context) (*ports.QueueMessage, error) {
	// Get and record stream size
	if q.metrics != nil {
		streamSize, err := q.getStreamSize(ctx)
		if err != nil {
			q.logger.Warn("failed to get stream size", zap.Error(err))
		} else {
			q.metrics.SetStreamSize(q.consumer, streamSize)
			q.logger.Debug("stream size", zap.Int64("size", streamSize), zap.String("worker", q.consumer))
		}
	}

	args := &redislib.XReadGroupArgs{
		Group:    q.group,
		Consumer: q.consumer,
		Streams:  []string{q.stream, ">"},
		Count:    1,
		Block:    q.blockTimeout,
	}

	streams, err := q.client.XReadGroup(ctx, args).Result()
	if errors.Is(err, redislib.Nil) {
		return nil, ports.ErrNoMessages
	}
	if err != nil {
		return nil, err
	}

	if len(streams) == 0 || len(streams[0].Messages) == 0 {
		return nil, ports.ErrNoMessages
	}

	xmsg := streams[0].Messages[0]
	task := hydrateTask(xmsg.Values)

	return &ports.QueueMessage{
		ID:   xmsg.ID,
		Task: task,
		Raw:  toRawMap(xmsg.Values),
	}, nil
}

func (q *StreamQueue) Ack(ctx context.Context, msg *ports.QueueMessage) error {
	if msg == nil {
		return errors.New("queue message is nil")
	}
	if err := q.client.XAck(ctx, q.stream, q.group, msg.ID).Err(); err != nil {
		return err
	}
	return q.client.XDel(ctx, q.stream, msg.ID).Err()
}

func (q *StreamQueue) Fail(ctx context.Context, msg *ports.QueueMessage, reason error) error {
	if msg == nil {
		return errors.New("queue message is nil")
	}

	if err := q.client.XAck(ctx, q.stream, q.group, msg.ID).Err(); err != nil {
		q.logger.Error("failed to ack failed message", zap.Error(err), zap.String("message_id", msg.ID))
	}

	if q.maxDeliveries > 0 && msg.Task.Attempt+1 >= q.maxDeliveries {
		q.logger.Warn("discarding message after max deliveries", zap.String("task_id", msg.Task.ID))
		return nil
	}

	values := map[string]any{
		"task_id":     msg.Task.ID,
		"video_id":    msg.Task.VideoID,
		"source_path": msg.Task.SourcePath,
		"attempt":     msg.Task.Attempt + 1,
	}
	if reason != nil {
		values["error"] = reason.Error()
	}
	for k, v := range msg.Raw {
		if _, exists := values[k]; !exists {
			values[k] = v
		}
	}

	return q.client.XAdd(ctx, &redislib.XAddArgs{Stream: q.stream, Values: values}).Err()
}

func hydrateTask(values map[string]any) domain.Task {
	task := domain.Task{Metadata: make(map[string]string)}

	for key, value := range values {
		strVal := fmt.Sprint(value)
		switch key {
		case "task_id":
			task.ID = strVal
		case "video_id":
			task.VideoID = strVal
		case "source_path":
			task.SourcePath = strVal
		case "attempt":
			if attempt, err := strconv.Atoi(strVal); err == nil {
				task.Attempt = attempt
			}
		default:
			task.Metadata[key] = strVal
		}
	}

	return task
}

func toRawMap(values map[string]any) map[string]any {
	out := make(map[string]any, len(values))
	for k, v := range values {
		out[k] = v
	}
	return out
}

func (q *StreamQueue) getStreamSize(ctx context.Context) (int64, error) {
	return q.client.XLen(ctx, q.stream).Result()
}
