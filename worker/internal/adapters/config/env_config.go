package config

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"time"

	"github.com/joho/godotenv"
)

type Config struct {
	AppName            string
	LogLevel           string
	RedisAddr          string
	RedisUsername      string
	RedisPassword      string
	RedisStream        string
	RedisGroup         string
	RedisConsumer      string
	RedisBlockTimeout  time.Duration
	RedisMaxDeliveries int
	WorkerPoolSize     int
	ProcessingTimeout  time.Duration
	PostgresDSN        string
	NextcloudURL       string
	NextcloudRoot      string
	NextcloudUsername  string
	NextcloudPassword  string
	ProcessedBaseURL   string
	MetricsAddr        string
	ShutdownGrace      time.Duration
}

func Load(envPaths ...string) (*Config, error) {
	paths := envPaths
	if len(paths) == 0 {
		paths = []string{".env"}
	}

	for _, p := range paths {
		if err := loadIfExists(p); err != nil {
			return nil, err
		}
	}

	cfg := &Config{
		AppName:            getEnv("APP_NAME", "video-worker"),
		LogLevel:           getEnv("LOG_LEVEL", "info"),
		RedisAddr:          getEnv("REDIS_ADDR", "localhost:6379"),
		RedisUsername:      os.Getenv("REDIS_USERNAME"),
		RedisPassword:      os.Getenv("REDIS_PASSWORD"),
		RedisStream:        getEnv("REDIS_STREAM", "video_tasks"),
		RedisGroup:         getEnv("REDIS_GROUP", "video_worker"),
		RedisConsumer:      getEnv("REDIS_CONSUMER", "video_worker_1"),
		RedisBlockTimeout:  getDurationEnv("REDIS_BLOCK_TIMEOUT", 5*time.Second),
		RedisMaxDeliveries: getIntEnv("REDIS_MAX_DELIVERIES", 5),
		WorkerPoolSize:     getIntEnv("WORKER_POOL_SIZE", 4),
		ProcessingTimeout:  getDurationEnv("PROCESSING_TIMEOUT", 5*time.Minute),
		PostgresDSN:        os.Getenv("POSTGRES_DSN"),
		NextcloudURL:       os.Getenv("NEXTCLOUD_URL"),
		NextcloudRoot:      getEnv("NEXTCLOUD_ROOT", "/remote.php/dav/files"),
		NextcloudUsername:  os.Getenv("NEXTCLOUD_USERNAME"),
		NextcloudPassword:  os.Getenv("NEXTCLOUD_PASSWORD"),
		ProcessedBaseURL:   getEnv("PROCESSED_BASE_URL", "/processed/"),
		MetricsAddr:        getEnv("METRICS_ADDR", ":9090"),
		ShutdownGrace:      getDurationEnv("SHUTDOWN_GRACE", 30*time.Second),
	}

	if cfg.PostgresDSN == "" {
		return nil, fmt.Errorf("POSTGRES_DSN is required")
	}

	if cfg.NextcloudURL == "" {
		return nil, fmt.Errorf("NEXTCLOUD_URL is required")
	}

	if cfg.NextcloudUsername == "" || cfg.NextcloudPassword == "" {
		return nil, fmt.Errorf("NEXTCLOUD credentials are required")
	}

	return cfg, nil
}

func loadIfExists(path string) error {
	if !filepath.IsAbs(path) {
		if _, err := os.Stat(path); err != nil {
			if errors.Is(err, os.ErrNotExist) {
				return nil
			}
			return err
		}
	} else {
		if _, err := os.Stat(path); err != nil {
			if errors.Is(err, os.ErrNotExist) {
				return nil
			}
			return err
		}
	}
	if err := godotenv.Load(path); err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return nil
		}
		return err
	}
	return nil
}

func getEnv(key, fallback string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return fallback
}

func getIntEnv(key string, fallback int) int {
	if val := os.Getenv(key); val != "" {
		if parsed, err := strconv.Atoi(val); err == nil {
			return parsed
		}
	}
	return fallback
}

func getDurationEnv(key string, fallback time.Duration) time.Duration {
	if val := os.Getenv(key); val != "" {
		if d, err := time.ParseDuration(val); err == nil {
			return d
		}
		if ms, err := strconv.Atoi(val); err == nil {
			return time.Duration(ms) * time.Millisecond
		}
	}
	return fallback
}
