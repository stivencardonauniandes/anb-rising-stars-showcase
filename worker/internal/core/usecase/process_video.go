package usecase

import (
	"context"
	"errors"
	"io"
	"time"

	"go.uber.org/zap"

	"github.com/alejandro/video-worker/internal/core/domain"
	"github.com/alejandro/video-worker/internal/core/ports"
	"github.com/google/uuid"
)

const PROCESSED_BASE_URL = "/videos/processed/"

type ProcessVideoUseCase struct {
	queue             ports.MessageQueue
	storage           ports.Storage
	repository        ports.VideoRepository
	metrics           ports.Metrics
	processor         ports.VideoProcessor
	logger            *zap.Logger
	processingTimeout time.Duration
	maxAttempts       int
}

func NewProcessVideoUseCase(
	queue ports.MessageQueue,
	storage ports.Storage,
	repository ports.VideoRepository,
	metrics ports.Metrics,
	processor ports.VideoProcessor,
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
		processor:         processor,
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
	rawVideoReader, err := u.getVideoBinary(processCtx, task)
	if err != nil {
		video.ResetToUploaded()
		updateErr := u.repository.Update(ctx, video)
		if updateErr != nil {
			u.logger.Error("failed to reset video after download error", zap.Error(updateErr), zap.String("video_id", task.VideoID))
		}
		u.metrics.IncTaskProcessed(string(domain.VideoStatusFailed))
		u.logger.Error("failed to download video", zap.Error(err), zap.String("task_id", task.ID))
		return err
	}

	videoProcessedReader, err := u.processVideo(ctx, rawVideoReader)
	if err != nil {
		video.ResetToUploaded()
		updateErr := u.repository.Update(ctx, video)
		if updateErr != nil {
			u.logger.Error("failed to reset video after processing error", zap.Error(updateErr), zap.String("video_id", task.VideoID))
		}
		u.metrics.IncTaskProcessed(string(domain.VideoStatusFailed))
		u.logger.Error("video processing failed", zap.Error(err), zap.String("task_id", task.ID))

		if task.Attempt+1 >= u.maxAttempts && u.maxAttempts > 0 {
			u.logger.Warn("max retry attempts reached", zap.String("task_id", task.ID))
		}
		status = domain.VideoStatusFailed
		return err
	}

	err = u.uploadProcessedVideo(processCtx, task, videoProcessedReader)
	if err != nil {
		video.ResetToUploaded()
		updateErr := u.repository.Update(ctx, video)
		if updateErr != nil {
			u.logger.Error("failed to reset video after upload error", zap.Error(updateErr), zap.String("video_id", task.VideoID))
		}
		u.metrics.IncTaskProcessed(string(domain.VideoStatusFailed))
		u.logger.Error("failed to upload processed video", zap.Error(err), zap.String("task_id", task.ID))
		status = domain.VideoStatusFailed
		return err
	}

	processedVideoID := uuid.New().String()
	processedURL := PROCESSED_BASE_URL + processedVideoID
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

func (u *ProcessVideoUseCase) getVideoBinary(ctx context.Context, task domain.Task) (io.ReadCloser, error) {
	reader, err := u.storage.Download(ctx, task.SourcePath)
	if err != nil {
		return nil, err
	}
	defer func() {
		_ = reader.Close()
	}()
	return reader, nil
}

func (u *ProcessVideoUseCase) uploadProcessedVideo(ctx context.Context, task domain.Task, processed *ports.ProcessedVideo) error {
	defer func() {
		_ = processed.Close()
	}()

	if err := u.storage.Upload(ctx, task.OutputPath, processed.Reader); err != nil {
		return err
	}
	return nil
}

func (u *ProcessVideoUseCase) processVideo(ctx context.Context, rawVideoReader io.ReadCloser) (*ports.ProcessedVideo, error) {
	if u.processor == nil {
		return nil, errors.New("video processor not configured")
	}

	processed, err := u.processor.Process(ctx, rawVideoReader, ports.VideoProcessingOptions{
		ClipDuration: 30 * time.Second,
		TargetWidth:  1280,
		TargetHeight: 720,
		TargetFormat: "mp4",
		RemoveAudio:  true,
		Watermark: &ports.WatermarkOptions{
			Text:          "water-mark",
			FontColor:     "white",
			FontSize:      48,
			BorderWidth:   2,
			BorderColor:   "black",
			Position:      ports.WatermarkBottomRight,
			MarginX:       40,
			MarginY:       40,
			StartDuration: 3 * time.Second,
			EndDuration:   3 * time.Second,
		},
	})
	if err != nil {
		return nil, err
	}

	return processed, nil
}
