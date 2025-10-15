package usecase

import (
	"bytes"
	"context"
	"errors"
	"io"
	"time"

	"go.uber.org/zap"

	"github.com/alejandro/video-worker/internal/core/domain"
	"github.com/alejandro/video-worker/internal/core/ports"
)

type ProcessVideoUseCase struct {
	queue             ports.MessageQueue
	storage           ports.Storage
	repository        ports.VideoRepository
	metrics           ports.Metrics
	logger            *zap.Logger
	processingTimeout time.Duration
	maxAttempts       int
}

func NewProcessVideoUseCase(
	queue ports.MessageQueue,
	storage ports.Storage,
	repository ports.VideoRepository,
	metrics ports.Metrics,
	logger *zap.Logger,
	processingTimeout time.Duration,
	maxAttempts int,
) *ProcessVideoUseCase {
	if logger == nil {
		logger = zap.NewNop()
	}
	return &ProcessVideoUseCase{
		queue:             queue,
		storage:           storage,
		repository:        repository,
		metrics:           metrics,
		logger:            logger,
		processingTimeout: processingTimeout,
		maxAttempts:       maxAttempts,
	}
}

func (u *ProcessVideoUseCase) HandleNext(ctx context.Context) error {
	msg, err := u.queue.Fetch(ctx)
	if err != nil {
		if errors.Is(err, ports.ErrNoMessages) {
			return nil
		}
		u.metrics.IncQueueError()
		u.logger.Error("failed to fetch message from queue", zap.Error(err))
		return err
	}

	start := time.Now()
	status := domain.VideoStatusUploaded
	defer func() {
		u.metrics.ObserveProcessingDuration(string(status), time.Since(start))
	}()

	task := msg.Task
	video, err := u.repository.FindByID(ctx, task.VideoID)
	if err != nil {
		u.metrics.IncTaskProcessed(string(domain.VideoStatusFailed))
		u.logger.Error("video not found", zap.Error(err), zap.String("video_id", task.VideoID))
		return err
	}

	processCtx := ctx
	var cancel context.CancelFunc
	if u.processingTimeout > 0 {
		processCtx, cancel = context.WithTimeout(ctx, u.processingTimeout)
		defer cancel()
	}

	procErr := u.processVideo(processCtx, task)
	if procErr != nil {
		video.ResetToUploaded()
		if updateErr := u.repository.Update(ctx, video); updateErr != nil {
			u.logger.Error("failed to reset video after processing error", zap.Error(updateErr), zap.String("video_id", task.VideoID))
		}

		u.metrics.IncTaskProcessed(string(domain.VideoStatusFailed))
		u.logger.Error("video processing failed", zap.Error(procErr), zap.String("task_id", task.ID))

		if task.Attempt+1 >= u.maxAttempts && u.maxAttempts > 0 {
			u.logger.Warn("max retry attempts reached", zap.String("task_id", task.ID))
		}
		status = domain.VideoStatusFailed
		return procErr
	}

	processedVideoID := task.Metadata["processed_video_id"]
	processedURL := task.Metadata["processed_url"]
	if processedURL == "" {
		processedURL = task.OutputPath
	}
	processedAt := time.Now()
	video.MarkProcessed(processedAt, processedVideoID, processedURL)
	if err := u.repository.Update(ctx, video); err != nil {
		u.metrics.IncTaskProcessed(string(domain.VideoStatusFailed))
		u.logger.Error("failed to mark completed", zap.Error(err), zap.String("video_id", task.VideoID))
		status = domain.VideoStatusFailed
		return err
	}

	u.metrics.IncTaskProcessed(string(domain.VideoStatusProcessed))
	u.logger.Info("video processed successfully", zap.String("task_id", task.ID), zap.String("video_id", video.ID))

	if err := u.queue.Ack(ctx, msg); err != nil {
		u.logger.Error("acknowledgement failed", zap.Error(err), zap.String("task_id", task.ID))
	}

	status = domain.VideoStatusProcessed
	return nil
}

func (u *ProcessVideoUseCase) processVideo(ctx context.Context, task domain.Task) error {
	reader, err := u.storage.Download(ctx, task.SourcePath)
	if err != nil {
		return err
	}
	defer func() {
		_ = reader.Close()
	}()

	var buf bytes.Buffer
	if _, err := io.Copy(&buf, reader); err != nil {
		return err
	}

	// TODO: Process video
	processed := bytes.NewReader(buf.Bytes())

	if err := u.storage.Upload(ctx, task.OutputPath, processed); err != nil {
		return err
	}

	return nil
}
