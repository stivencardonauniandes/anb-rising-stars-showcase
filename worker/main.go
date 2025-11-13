package main

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"net/http"
	"os"
	"sync"
	"time"

	_ "github.com/lib/pq"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/collectors"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	redislib "github.com/redis/go-redis/v9"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"

	"github.com/alejandro/video-worker/internal/adapters/config"
	"github.com/alejandro/video-worker/internal/adapters/ffmpeg"
	metricsadapter "github.com/alejandro/video-worker/internal/adapters/metrics"
	nextcloudadapter "github.com/alejandro/video-worker/internal/adapters/nextcloud"
	postgresadapter "github.com/alejandro/video-worker/internal/adapters/postgres"
	redisadapter "github.com/alejandro/video-worker/internal/adapters/redis"
	sqsadapter "github.com/alejandro/video-worker/internal/adapters/sqs"
	s3adapter "github.com/alejandro/video-worker/internal/adapters/s3"
	"github.com/alejandro/video-worker/internal/core/ports"
	"github.com/alejandro/video-worker/internal/core/usecase"
)

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	if err := Run(ctx); err != nil {
		fmt.Fprintf(os.Stderr, "fatal error: %v\n", err)
		os.Exit(1)
	}
}

// Run bootstraps all adapters and starts the worker pool. It blocks until the
// provided context is canceled or a fatal error occurs.
func Run(ctx context.Context) error {
	cfg, err := config.Load("./configs/.env")
	if err != nil {
		return fmt.Errorf("load config: %w", err)
	}

	logger, err := newLogger(cfg.LogLevel)
	if err != nil {
		return fmt.Errorf("init logger: %w", err)
	}
	if cfg.AppName != "" {
		logger = logger.Named(cfg.AppName)
	}
	defer func() { _ = logger.Sync() }()

	db, err := sql.Open("postgres", cfg.PostgresDSN)
	if err != nil {
		return fmt.Errorf("connect postgres: %w", err)
	}
	defer func() {
		if cerr := db.Close(); cerr != nil {
			logger.Warn("failed to close postgres connection", zap.Error(cerr))
		}
	}()
	if err := db.PingContext(ctx); err != nil {
		return fmt.Errorf("ping postgres: %w", err)
	}

	registry := prometheus.NewRegistry()
	registry.MustRegister(
		collectors.NewProcessCollector(collectors.ProcessCollectorOpts{}),
		collectors.NewGoCollector(),
	)
	metricsAdapter := metricsadapter.NewPrometheusMetrics(registry)

	metricsMux := http.NewServeMux()
	metricsMux.Handle("/metrics", promhttp.HandlerFor(registry, promhttp.HandlerOpts{}))
	metricsSrv := &http.Server{
		Addr:              cfg.MetricsAddr,
		Handler:           metricsMux,
		ReadHeaderTimeout: 5 * time.Second,
	}
	metricsErrCh := make(chan error, 1)
	go func() {
		logger.Info("metrics server listening", zap.String("addr", cfg.MetricsAddr))
		if err := metricsSrv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			metricsErrCh <- err
		}
	}()
	defer func() {
		select {
		case err := <-metricsErrCh:
			if err != nil {
				logger.Warn("metrics server exited unexpectedly", zap.Error(err))
			}
		default:
		}
	}()
	defer func() {
		shutdownCtx, cancel := context.WithTimeout(context.Background(), cfg.ShutdownGrace)
		defer cancel()
		if err := metricsSrv.Shutdown(shutdownCtx); err != nil && !errors.Is(err, http.ErrServerClosed) {
			logger.Warn("metrics server shutdown error", zap.Error(err))
		}
	}()

	// Initialize storage based on configured backend
	var storage ports.Storage
	switch cfg.StorageBackend {
	case "nextcloud":
		storage, err = nextcloudadapter.NewWebDAVStorage(
			cfg.NextcloudURL,
			cfg.NextcloudRoot,
			cfg.NextcloudUsername,
			cfg.NextcloudPassword,
			logger,
		)
		if err != nil {
			return fmt.Errorf("init nextcloud storage: %w", err)
		}
		logger.Info("using NextCloud storage backend",
			zap.String("url", cfg.NextcloudURL),
			zap.String("root", cfg.NextcloudRoot))
	case "s3":
		storage, err = s3adapter.NewS3Storage(
			cfg.S3Region,
			cfg.S3Bucket,
			cfg.ProcessedBaseURL,
			cfg.S3AccessKey,
			cfg.S3SecretKey,
			cfg.S3Endpoint,
			logger,
		)
		if err != nil {
			return fmt.Errorf("init s3 storage: %w", err)
		}
		logger.Info("using S3 storage backend",
			zap.String("region", cfg.S3Region),
			zap.String("bucket", cfg.S3Bucket),
			zap.String("prefix", cfg.ProcessedBaseURL),
			zap.String("endpoint", cfg.S3Endpoint))
	default:
		return fmt.Errorf("unsupported storage backend: %s", cfg.StorageBackend)
	}

	repository := postgresadapter.NewVideoRepository(db, logger)
	processor := ffmpeg.NewVideoProcessor(os.Getenv("FFMPEG_PATH"), os.Getenv("FFPROBE_PATH"), os.Getenv("VIDEO_TEMP_DIR"), logger)

	workerCount := cfg.WorkerPoolSize
	if workerCount <= 0 {
		workerCount = 1
	}

	logger.Info("video worker running",
		zap.Int("worker_pool_size", workerCount),
		zap.Duration("processing_timeout", cfg.ProcessingTimeout),
		zap.String("queue_backend", cfg.QueueBackend),
	)

	workerCtx, cancelWorkers := context.WithCancel(ctx)
	defer cancelWorkers()

	var wg sync.WaitGroup
	for i := 0; i < workerCount; i++ {
		workerID := i + 1
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			workerIDStr := fmt.Sprintf("%d", id)

			// Create queue instance based on configured backend
			var queue ports.MessageQueue
			var err error

			switch cfg.QueueBackend {
			case "redis":
				redisClient := redislib.NewClient(&redislib.Options{
					Addr:     cfg.RedisAddr,
					Username: cfg.RedisUsername,
					Password: cfg.RedisPassword,
				})
				defer func() {
					if cerr := redisClient.Close(); cerr != nil {
						logger.Warn("failed to close redis client", zap.Error(cerr))
					}
				}()
				if err := redisClient.Ping(ctx).Err(); err != nil {
					logger.Error("failed to connect to redis", zap.Int("worker_id", id), zap.Error(err))
					return
				}
				consumerName := fmt.Sprintf("%s-worker-%d", cfg.RedisConsumer, id)
				queue, err = redisadapter.NewStreamQueue(ctx, redisClient, cfg.RedisStream, cfg.RedisGroup, consumerName, cfg.RedisBlockTimeout, cfg.MaxDeliveries, logger, metricsAdapter)
			case "sqs":
				queue, err = sqsadapter.NewSQSQueue(ctx, cfg.SQSQueueURL, cfg.SQSRegion, cfg.MaxDeliveries, cfg.SQSWaitTime, logger, metricsAdapter)
			default:
				logger.Error("unsupported queue backend", zap.String("backend", cfg.QueueBackend))
				return
			}

			if err != nil {
				logger.Error("failed to create queue for worker", zap.Int("worker_id", id), zap.Error(err))
				return
			}

			useCase := usecase.NewProcessVideoUseCase(
				queue,
				storage,
				repository,
				metricsAdapter,
				processor,
				logger,
				cfg.ProcessingTimeout,
				cfg.MaxDeliveries,
				cfg.ProcessedBaseURL,
			)

			for {
				select {
				case <-workerCtx.Done():
					return
				default:
				}

				if err := useCase.HandleNext(workerCtx, workerIDStr); err != nil {
					if errors.Is(err, context.Canceled) || errors.Is(err, context.DeadlineExceeded) {
						return
					}
					logger.Error("worker iteration failed",
						zap.Int("worker_id", id),
						zap.Error(err),
					)
					time.Sleep(500 * time.Millisecond)
				}
			}
		}(workerID)
	}

	var runErr error
	select {
	case <-ctx.Done():
		runErr = ctx.Err()
	case err := <-metricsErrCh:
		if err != nil {
			runErr = fmt.Errorf("metrics server: %w", err)
		}
	}

	cancelWorkers()

	done := make(chan struct{})
	go func() {
		wg.Wait()
		close(done)
	}()

	select {
	case <-done:
	case <-time.After(cfg.ShutdownGrace):
		logger.Warn("worker shutdown timed out", zap.Duration("grace_period", cfg.ShutdownGrace))
	}

	if runErr != nil && errors.Is(runErr, context.Canceled) {
		return nil
	}

	return runErr
}

func newLogger(level string) (*zap.Logger, error) {
	cfg := zap.NewProductionConfig()
	cfg.Encoding = "console"
	cfg.EncoderConfig.EncodeLevel = zapcore.CapitalColorLevelEncoder
	if level != "" {
		if err := cfg.Level.UnmarshalText([]byte(level)); err != nil {
			cfg.Level = zap.NewAtomicLevelAt(zapcore.InfoLevel)
		}
	}
	cfg.EncoderConfig.TimeKey = "timestamp"
	cfg.EncoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder
	return cfg.Build()
}
