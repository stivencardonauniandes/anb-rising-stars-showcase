package sqs

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strconv"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/sqs"
	"github.com/aws/aws-sdk-go-v2/service/sqs/types"
	"go.uber.org/zap"

	"github.com/alejandro/video-worker/internal/core/domain"
	"github.com/alejandro/video-worker/internal/core/ports"
)

type SQSQueue struct {
	client        *sqs.Client
	queueURL      string
	maxDeliveries int
	waitTime      int32 // Long polling wait time in seconds
	logger        *zap.Logger
	metrics       ports.Metrics
}

func NewSQSQueue(
	ctx context.Context,
	queueURL string,
	region string,
	maxDeliveries int,
	waitTime int32,
	logger *zap.Logger,
	metrics ports.Metrics,
) (*SQSQueue, error) {
	if logger == nil {
		logger = zap.NewNop()
	}

	// Load AWS config - uses IAM role credentials from EC2 instance when running on AWS
	cfg, err := config.LoadDefaultConfig(ctx, config.WithRegion(region))
	if err != nil {
		return nil, fmt.Errorf("load aws config: %w", err)
	}

	client := sqs.NewFromConfig(cfg)

	return &SQSQueue{
		client:        client,
		queueURL:      queueURL,
		maxDeliveries: maxDeliveries,
		waitTime:      waitTime,
		logger:        logger,
		metrics:       metrics,
	}, nil
}

func (q *SQSQueue) Fetch(ctx context.Context) (*ports.QueueMessage, error) {
	// Get queue attributes for metrics
	if q.metrics != nil {
		attrs, err := q.client.GetQueueAttributes(ctx, &sqs.GetQueueAttributesInput{
			QueueUrl:       aws.String(q.queueURL),
			AttributeNames: []types.QueueAttributeName{types.QueueAttributeNameApproximateNumberOfMessages},
		})
		if err == nil && attrs.Attributes != nil {
			if countStr, ok := attrs.Attributes[string(types.QueueAttributeNameApproximateNumberOfMessages)]; ok {
				if count, err := strconv.ParseInt(countStr, 10, 64); err == nil {
					q.metrics.SetStreamSize("sqs-worker", count)
					q.logger.Debug("queue size", zap.Int64("size", count))
				}
			}
		}
	}

	// Receive message with long polling
	result, err := q.client.ReceiveMessage(ctx, &sqs.ReceiveMessageInput{
		QueueUrl:            aws.String(q.queueURL),
		MaxNumberOfMessages: 1,
		WaitTimeSeconds:     q.waitTime,
		AttributeNames: []types.QueueAttributeName{
			types.QueueAttributeNameApproximateReceiveCount,
		},
	})

	if err != nil {
		return nil, fmt.Errorf("receive message: %w", err)
	}

	if len(result.Messages) == 0 {
		return nil, ports.ErrNoMessages
	}

	msg := result.Messages[0]

	// Parse message body
	var messageBody map[string]interface{}
	if err := json.Unmarshal([]byte(*msg.Body), &messageBody); err != nil {
		q.logger.Error("failed to parse message body", zap.Error(err), zap.String("message_id", *msg.MessageId))
		// Delete the message if we can't parse it
		_, _ = q.client.DeleteMessage(ctx, &sqs.DeleteMessageInput{
			QueueUrl:      aws.String(q.queueURL),
			ReceiptHandle: msg.ReceiptHandle,
		})
		return nil, fmt.Errorf("parse message body: %w", err)
	}

	// Extract attempt count from message attributes if available
	attempt := 0
	if msg.Attributes != nil {
		if receiveCount, ok := msg.Attributes[string(types.QueueAttributeNameApproximateReceiveCount)]; ok {
			if count, err := strconv.Atoi(receiveCount); err == nil {
				attempt = count - 1 // ReceiveCount starts at 1, attempt starts at 0
			}
		}
	}

	// Check if attempt is in message body (for retries)
	if attemptVal, ok := messageBody["attempt"]; ok {
		if attemptInt, err := strconv.Atoi(fmt.Sprint(attemptVal)); err == nil {
			attempt = attemptInt
		}
	}

	task := hydrateTask(messageBody, attempt)

	return &ports.QueueMessage{
		ID:   *msg.ReceiptHandle, // Use receipt handle as ID for deletion
		Task: task,
		Raw:  messageBody,
	}, nil
}

func (q *SQSQueue) Ack(ctx context.Context, msg *ports.QueueMessage) error {
	if msg == nil {
		return errors.New("queue message is nil")
	}

	// Delete message from queue (acknowledgment in SQS)
	_, err := q.client.DeleteMessage(ctx, &sqs.DeleteMessageInput{
		QueueUrl:      aws.String(q.queueURL),
		ReceiptHandle: aws.String(msg.ID),
	})

	if err != nil {
		return fmt.Errorf("delete message: %w", err)
	}

	return nil
}

func (q *SQSQueue) Fail(ctx context.Context, msg *ports.QueueMessage, reason error) error {
	if msg == nil {
		return errors.New("queue message is nil")
	}

	// Check if we've exceeded max deliveries
	if q.maxDeliveries > 0 && msg.Task.Attempt+1 >= q.maxDeliveries {
		q.logger.Warn("discarding message after max deliveries",
			zap.String("task_id", msg.Task.ID),
			zap.Int("attempt", msg.Task.Attempt+1),
		)
		// Delete the message to remove it from the queue
		_, err := q.client.DeleteMessage(ctx, &sqs.DeleteMessageInput{
			QueueUrl:      aws.String(q.queueURL),
			ReceiptHandle: aws.String(msg.ID),
		})
		return err
	}

	// Prepare message body for retry with incremented attempt
	messageBody := map[string]interface{}{
		"task_id":     msg.Task.ID,
		"video_id":    msg.Task.VideoID,
		"source_path": msg.Task.SourcePath,
		"attempt":     msg.Task.Attempt + 1,
	}

	if reason != nil {
		messageBody["error"] = reason.Error()
	}

	// Preserve other metadata
	for k, v := range msg.Raw {
		if k != "task_id" && k != "video_id" && k != "source_path" && k != "attempt" {
			messageBody[k] = v
		}
	}

	// Serialize message body
	bodyBytes, err := json.Marshal(messageBody)
	if err != nil {
		return fmt.Errorf("marshal message body: %w", err)
	}

	// Send message back to queue for retry
	_, err = q.client.SendMessage(ctx, &sqs.SendMessageInput{
		QueueUrl:    aws.String(q.queueURL),
		MessageBody: aws.String(string(bodyBytes)),
	})

	if err != nil {
		return fmt.Errorf("send retry message: %w", err)
	}

	// Delete the original message
	_, err = q.client.DeleteMessage(ctx, &sqs.DeleteMessageInput{
		QueueUrl:      aws.String(q.queueURL),
		ReceiptHandle: aws.String(msg.ID),
	})

	if err != nil {
		q.logger.Error("failed to delete failed message", zap.Error(err), zap.String("message_id", msg.ID))
	}

	return nil
}

func hydrateTask(values map[string]interface{}, attempt int) domain.Task {
	task := domain.Task{
		Attempt:  attempt,
		Metadata: make(map[string]string),
	}

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
			// Already set from parameter
		default:
			task.Metadata[key] = strVal
		}
	}

	return task
}

