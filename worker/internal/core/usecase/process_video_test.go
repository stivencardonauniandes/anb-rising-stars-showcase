package usecase

import (
	"bytes"
	"context"
	"errors"
	"io"
	"testing"
	"time"

	"github.com/alejandro/video-worker/internal/core/domain"
	"github.com/alejandro/video-worker/internal/core/ports"
	"github.com/alejandro/video-worker/internal/core/ports/mocks"
	"go.uber.org/mock/gomock"
	"go.uber.org/zap"
)

func TestHandleNextSuccess(t *testing.T) {
	ctrl := gomock.NewController(t)
	ctx := context.Background()
	t.Cleanup(ctrl.Finish)

	queue := mocks.NewMockMessageQueue(ctrl)
	storage := mocks.NewMockStorage(ctrl)
	repository := mocks.NewMockVideoRepository(ctrl)
	metrics := mocks.NewMockMetrics(ctrl)
	processor := mocks.NewMockVideoProcessor(ctrl)

	task := domain.Task{
		ID:         "task-1",
		VideoID:    "video-1",
		SourcePath: "/videos/source.mp4",
		OutputPath: "/videos/output.mp4",
	}
	video := &domain.Video{ID: "video-1", Status: domain.VideoStatusUploaded}
	message := &ports.QueueMessage{ID: "msg-1", Task: task}

	queue.EXPECT().Fetch(ctx).Return(message, nil)
	repository.EXPECT().FindByID(ctx, task.VideoID).Return(video, nil)
	storage.EXPECT().Download(ctx, task.SourcePath).Return(io.NopCloser(bytes.NewBufferString("video-bytes")), nil)
	processor.EXPECT().Process(ctx, gomock.Any(), gomock.Any()).DoAndReturn(func(ctx context.Context, rdr io.Reader, opts ports.VideoProcessingOptions) (*ports.ProcessedVideo, error) {
		data, err := io.ReadAll(rdr)
		if err != nil {
			return nil, err
		}
		if string(data) != "video-bytes" {
			t.Fatalf("expected processor to receive source payload, got %q", data)
		}
		return &ports.ProcessedVideo{
			Reader:   io.NopCloser(bytes.NewBufferString("processed-bytes")),
			Format:   "mp4",
			Duration: 30 * time.Second,
		}, nil
	})
	storage.EXPECT().Upload(ctx, task.OutputPath, gomock.Any()).DoAndReturn(func(ctx context.Context, path string, reader io.Reader) error {
		data, err := io.ReadAll(reader)
		if err != nil {
			return err
		}
		if string(data) != "processed-bytes" {
			t.Fatalf("expected uploaded payload to match processed data, got %q", data)
		}
		return nil
	})
	repository.EXPECT().Update(ctx, gomock.Any()).DoAndReturn(func(ctx context.Context, updated *domain.Video) error {
		if updated.Status != domain.VideoStatusProcessed {
			t.Fatalf("expected video status processed, got %s", updated.Status)
		}
		if updated.ProcessedVideoID == nil {
			t.Fatalf("expected processed video id to be set")
		}
		if updated.ProcessedURL == nil || *updated.ProcessedURL != PROCESSED_BASE_URL+*updated.ProcessedVideoID {
			t.Fatalf("expected processed url to be set")
		}
		return nil
	})
	metrics.EXPECT().IncTaskProcessed(string(domain.VideoStatusProcessed))
	metrics.EXPECT().ObserveProcessingDuration(string(domain.VideoStatusProcessed), gomock.Any())
	queue.EXPECT().Ack(ctx, message).Return(nil)

	uc := NewProcessVideoUseCase(queue, storage, repository, metrics, processor, zap.NewNop(), 0, 3)

	err := uc.HandleNext(ctx)
	if err != nil {
		t.Fatalf("HandleNext returned error: %v", err)
	}
}

func TestHandleNextQueueNoMessages(t *testing.T) {
	ctrl := gomock.NewController(t)
	ctx := context.Background()
	t.Cleanup(ctrl.Finish)

	queue := mocks.NewMockMessageQueue(ctrl)
	queue.EXPECT().Fetch(ctx).Return(nil, ports.ErrNoMessages)

	uc := NewProcessVideoUseCase(queue, nil, nil, nil, nil, zap.NewNop(), 0, 3)

	err := uc.HandleNext(ctx)
	if err != nil {
		t.Fatalf("expected nil error for no messages, got %v", err)
	}
}

func TestHandleNextQueueFetchError(t *testing.T) {
	ctrl := gomock.NewController(t)
	ctx := context.Background()
	t.Cleanup(ctrl.Finish)

	queue := mocks.NewMockMessageQueue(ctrl)
	metrics := mocks.NewMockMetrics(ctrl)

	expectedErr := errors.New("fetch error")
	queue.EXPECT().Fetch(ctx).Return(nil, expectedErr)
	metrics.EXPECT().IncQueueError()

	uc := NewProcessVideoUseCase(queue, nil, nil, metrics, nil, zap.NewNop(), 0, 3)

	err := uc.HandleNext(ctx)
	if !errors.Is(err, expectedErr) {
		t.Fatalf("expected error %v, got %v", expectedErr, err)
	}
}

func TestHandleNextFindByIDError(t *testing.T) {
	ctrl := gomock.NewController(t)
	ctx := context.Background()
	t.Cleanup(ctrl.Finish)

	queue := mocks.NewMockMessageQueue(ctrl)
	repository := mocks.NewMockVideoRepository(ctrl)
	metrics := mocks.NewMockMetrics(ctrl)

	task := domain.Task{
		ID:         "task-2",
		VideoID:    "video-2",
		SourcePath: "src.mp4",
		OutputPath: "out.mp4",
	}
	message := &ports.QueueMessage{ID: "msg-2", Task: task}

	expectedErr := errors.New("not found")

	queue.EXPECT().Fetch(ctx).Return(message, nil)
	repository.EXPECT().FindByID(ctx, task.VideoID).Return(nil, expectedErr)
	metrics.EXPECT().IncTaskProcessed(string(domain.VideoStatusFailed))
	metrics.EXPECT().ObserveProcessingDuration(string(domain.VideoStatusUploaded), gomock.Any())

	uc := NewProcessVideoUseCase(queue, nil, repository, metrics, nil, zap.NewNop(), 0, 3)

	err := uc.HandleNext(context.Background())
	if !errors.Is(err, expectedErr) {
		t.Fatalf("expected %v, got %v", expectedErr, err)
	}
}

func TestHandleNextProcessVideoError(t *testing.T) {
	ctrl := gomock.NewController(t)
	ctx := context.Background()
	t.Cleanup(ctrl.Finish)

	queue := mocks.NewMockMessageQueue(ctrl)
	storage := mocks.NewMockStorage(ctrl)
	repository := mocks.NewMockVideoRepository(ctrl)
	metrics := mocks.NewMockMetrics(ctrl)
	processor := mocks.NewMockVideoProcessor(ctrl)

	task := domain.Task{
		ID:         "task-3",
		VideoID:    "video-3",
		SourcePath: "source.mp4",
		OutputPath: "output.mp4",
	}
	message := &ports.QueueMessage{ID: "msg-3", Task: task}
	video := &domain.Video{ID: "video-3", Status: domain.VideoStatusUploaded}

	processErr := errors.New("process failed")

	queue.EXPECT().Fetch(ctx).Return(message, nil)
	repository.EXPECT().FindByID(ctx, task.VideoID).Return(video, nil)
	storage.EXPECT().Download(ctx, task.SourcePath).Return(io.NopCloser(bytes.NewBufferString("source-bytes")), nil)
	processor.EXPECT().Process(ctx, gomock.Any(), gomock.Any()).Return(nil, processErr)
	repository.EXPECT().Update(ctx, gomock.Any()).DoAndReturn(func(ctx context.Context, updated *domain.Video) error {
		if updated.Status != domain.VideoStatusUploaded {
			t.Fatalf("expected video status reset to uploaded, got %s", updated.Status)
		}
		return nil
	})
	metrics.EXPECT().IncTaskProcessed(string(domain.VideoStatusFailed))
	metrics.EXPECT().ObserveProcessingDuration(string(domain.VideoStatusFailed), gomock.Any())

	uc := NewProcessVideoUseCase(queue, storage, repository, metrics, processor, zap.NewNop(), 0, 3)

	err := uc.HandleNext(ctx)
	if !errors.Is(err, processErr) {
		t.Fatalf("expected %v, got %v", processErr, err)
	}
}

func TestProcessVideoSuccess(t *testing.T) {
	ctrl := gomock.NewController(t)
	ctx := context.Background()
	t.Cleanup(ctrl.Finish)

	processor := mocks.NewMockVideoProcessor(ctrl)

	processor.EXPECT().Process(ctx, gomock.Any(), gomock.Any()).DoAndReturn(func(ctx context.Context, rdr io.Reader, opts ports.VideoProcessingOptions) (*ports.ProcessedVideo, error) {
		data, err := io.ReadAll(rdr)
		if err != nil {
			return nil, err
		}
		if string(data) != "payload" {
			t.Fatalf("expected processor to receive payload, got %q", data)
		}
		if opts.TargetFormat != "mp4" {
			t.Fatalf("expected target format mp4, got %s", opts.TargetFormat)
		}
		if opts.TargetWidth != 1280 || opts.TargetHeight != 720 {
			t.Fatalf("unexpected target dimensions: %dx%d", opts.TargetWidth, opts.TargetHeight)
		}
		if opts.Watermark == nil || opts.Watermark.Position != ports.WatermarkBottomRight {
			t.Fatalf("expected watermark bottom-right configuration")
		}
		return &ports.ProcessedVideo{Reader: io.NopCloser(bytes.NewBufferString("processed"))}, nil
	})

	uc := &ProcessVideoUseCase{processor: processor}
	result, err := uc.processVideo(ctx, io.NopCloser(bytes.NewBufferString("payload")))
	if err != nil {
		t.Fatalf("expected nil error, got %v", err)
	}
	if result == nil {
		t.Fatalf("expected processed video result")
	}
	data, err := io.ReadAll(result.Reader)
	if err != nil {
		t.Fatalf("failed reading processed video: %v", err)
	}
	if string(data) != "processed" {
		t.Fatalf("expected processed bytes, got %q", data)
	}
	if err := result.Close(); err != nil {
		t.Fatalf("unexpected close error: %v", err)
	}
}

func TestGetVideoBinaryDownloadError(t *testing.T) {
	ctrl := gomock.NewController(t)
	ctx := context.Background()
	t.Cleanup(ctrl.Finish)

	storage := mocks.NewMockStorage(ctrl)

	expectedErr := errors.New("download error")
	storage.EXPECT().Download(ctx, "source.mp4").Return(nil, expectedErr)

	uc := &ProcessVideoUseCase{storage: storage}

	_, err := uc.getVideoBinary(ctx, domain.Task{SourcePath: "source.mp4"})
	if !errors.Is(err, expectedErr) {
		t.Fatalf("expected %v, got %v", expectedErr, err)
	}
}

func TestProcessVideoUploadError(t *testing.T) {
	ctrl := gomock.NewController(t)
	ctx := context.Background()
	t.Cleanup(ctrl.Finish)

	storage := mocks.NewMockStorage(ctrl)
	processor := mocks.NewMockVideoProcessor(ctrl)
	expectedErr := errors.New("upload error")

	storage.EXPECT().Upload(ctx, "output.mp4", gomock.Any()).Return(expectedErr)

	uc := &ProcessVideoUseCase{storage: storage, processor: processor}

	err := uc.uploadProcessedVideo(ctx, domain.Task{OutputPath: "output.mp4"}, &ports.ProcessedVideo{Reader: io.NopCloser(bytes.NewBufferString("processed"))})
	if !errors.Is(err, expectedErr) {
		t.Fatalf("expected %v, got %v", expectedErr, err)
	}
}

func TestProcessVideoWithoutProcessor(t *testing.T) {
	ctrl := gomock.NewController(t)
	ctx := context.Background()
	t.Cleanup(ctrl.Finish)

	uc := &ProcessVideoUseCase{}
	_, err := uc.processVideo(ctx, io.NopCloser(bytes.NewBufferString("payload")))
	if err == nil {
		t.Fatalf("expected error when processor is not configured")
	}
}
