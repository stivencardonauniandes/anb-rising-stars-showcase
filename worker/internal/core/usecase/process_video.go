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

type ProcessVideoUseCase struct {
	queue             ports.MessageQueue
	storage           ports.Storage
	repository        ports.VideoRepository
	metrics           ports.Metrics
	processor         ports.VideoProcessor
	logger            *zap.Logger
	processingTimeout time.Duration
	maxAttempts       int
	processedBaseURL  string
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
	processedBaseURL string,
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
		processedBaseURL:  processedBaseURL,
	}
}

func (u *ProcessVideoUseCase) HandleNext(ctx context.Context, workerID string) error {
	msg, err := u.queue.Fetch(ctx)
	if err != nil {
		if errors.Is(err, ports.ErrNoMessages) {
			return nil
		}
		u.metrics.IncQueueError(workerID)
		u.logger.Error("failed to fetch message from queue", zap.Error(err))
		return err
	}

	start := time.Now()
	status := domain.VideoStatusUploaded
	defer func() {
		u.metrics.ObserveProcessingDuration(string(status), workerID, time.Since(start))
	}()

	task := msg.Task
	video, err := u.repository.FindByID(ctx, task.VideoID)
	if err != nil {
		u.metrics.IncTaskProcessed(string(domain.VideoStatusFailed), workerID)
		u.logger.Error("video not found", zap.Error(err), zap.String("video_id", task.VideoID))
		_ = u.queue.Fail(ctx, msg, err)
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
		u.metrics.IncTaskProcessed(string(domain.VideoStatusFailed), workerID)
		u.logger.Error("failed to download video", zap.Error(err), zap.String("task_id", task.ID))
		_ = u.queue.Fail(ctx, msg, err)
		return err
	}
	defer func() {
		_ = rawVideoReader.Close()
	}()

	videoProcessedReader, err := u.processVideo(ctx, rawVideoReader)
	if err != nil {
		video.ResetToUploaded()
		updateErr := u.repository.Update(ctx, video)
		if updateErr != nil {
			u.logger.Error("failed to reset video after processing error", zap.Error(updateErr), zap.String("video_id", task.VideoID))
		}
		u.metrics.IncTaskProcessed(string(domain.VideoStatusFailed), workerID)
		u.logger.Error("video processing failed", zap.Error(err), zap.String("task_id", task.ID))

		if task.Attempt+1 >= u.maxAttempts && u.maxAttempts > 0 {
			u.logger.Warn("max retry attempts reached", zap.String("task_id", task.ID))
		}
		status = domain.VideoStatusFailed
		_ = u.queue.Fail(ctx, msg, err)
		return err
	}

	// Generate processed video ID and construct output path
	processedVideoID := uuid.New().String()
	outputPath := processedVideoID + ".mp4"

	err = u.uploadProcessedVideo(processCtx, outputPath, videoProcessedReader)
	if err != nil {
		video.ResetToUploaded()
		updateErr := u.repository.Update(ctx, video)
		if updateErr != nil {
			u.logger.Error("failed to reset video after upload error", zap.Error(updateErr), zap.String("video_id", task.VideoID))
		}
		u.metrics.IncTaskProcessed(string(domain.VideoStatusFailed), workerID)
		u.logger.Error("failed to upload processed video", zap.Error(err), zap.String("task_id", task.ID))
		status = domain.VideoStatusFailed
		_ = u.queue.Fail(ctx, msg, err)
		return err
	}

	processedAt := time.Now()
	video.MarkProcessed(processedAt, processedVideoID, outputPath)
	if err := u.repository.Update(ctx, video); err != nil {
		u.metrics.IncTaskProcessed(string(domain.VideoStatusFailed), workerID)
		u.logger.Error("failed to mark completed", zap.Error(err), zap.String("video_id", task.VideoID))
		status = domain.VideoStatusFailed
		_ = u.queue.Fail(ctx, msg, err)
		return err
	}

	u.metrics.IncTaskProcessed(string(domain.VideoStatusProcessed), workerID)
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
	// Don't close here - the caller is responsible for closing the reader
	return reader, nil
}

func (u *ProcessVideoUseCase) uploadProcessedVideo(ctx context.Context, outputPath string, processed *ports.ProcessedVideo) error {
	defer func() {
		_ = processed.Close()
	}()

	u.logger.Info("attempting to upload processed video",
		zap.String("output_path", outputPath))

	if err := u.storage.Upload(ctx, outputPath, processed.Reader); err != nil {
		u.logger.Error("failed to upload processed video", zap.Error(err), zap.String("output_path", outputPath))
		return err
	}

	u.logger.Info("successfully uploaded processed video", zap.String("output_path", outputPath))
	return nil
}

func (u *ProcessVideoUseCase) processVideo(ctx context.Context, rawVideoReader io.ReadCloser) (*ports.ProcessedVideo, error) {
	if u.processor == nil {
		return nil, errors.New("video processor not configured")
	}

	processed, err := u.processor.Process(ctx, rawVideoReader, ports.VideoProcessingOptions{
		ClipDuration: 30 * time.Second,
		TargetWidth:  720,
		TargetHeight: 1280,
		TargetFormat: "mp4",
		RemoveAudio:  true,
		Watermark: &ports.WatermarkOptions{
			Text:          "ANB Rising Stars",
			FontColor:     "white",
			FontSize:      48,
			BorderWidth:   1,
			BorderColor:   "gray",
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
