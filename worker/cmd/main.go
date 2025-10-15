package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/alejandro/video-worker/internal/adapters/ffmpeg"
	"github.com/alejandro/video-worker/internal/core/ports"
	"go.uber.org/zap"
)

func main() {
	var inputPath string
	flag.StringVar(&inputPath, "input", "", "path to the source video file")
	flag.Parse()

	if inputPath == "" {
		if flag.NArg() > 0 {
			inputPath = flag.Arg(0)
		} else {
			fmt.Fprintln(os.Stderr, "usage: video-worker -input <path-to-video>")
			os.Exit(1)
		}
	}

	ctx := context.Background()
	processedPath, err := processVideoFile(ctx, inputPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "processing failed: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("processed video saved at:", processedPath)
}

func processVideoFile(ctx context.Context, inputPath string) (string, error) {
	if strings.TrimSpace(inputPath) == "" {
		return "", errors.New("input path is required")
	}

	absPath, err := filepath.Abs(inputPath)
	if err != nil {
		return "", fmt.Errorf("resolve input path: %w", err)
	}

	file, err := os.Open(absPath)
	if err != nil {
		return "", fmt.Errorf("open input file: %w", err)
	}
	defer func() {
		_ = file.Close()
	}()

	logger, err := zap.NewProduction()
	if err != nil {
		logger = zap.NewNop()
	} else {
		defer func() {
			_ = logger.Sync()
		}()
	}

	processor := ffmpeg.NewVideoProcessor(os.Getenv("FFMPEG_PATH"), os.Getenv("FFPROBE_PATH"), os.Getenv("VIDEO_TEMP_DIR"), logger)
	processed, err := processor.Process(ctx, file, ports.VideoProcessingOptions{
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
			StartDuration: 0 * time.Second,
			EndDuration:   0 * time.Second,
		},
	})
	if err != nil {
		return "", fmt.Errorf("process video: %w", err)
	}
	defer func() {
		_ = processed.Close()
	}()

	outputDir := filepath.Dir(absPath)
	base := strings.TrimSuffix(filepath.Base(absPath), filepath.Ext(absPath))
	format := strings.TrimPrefix(processed.Format, ".")
	if format == "" {
		format = "mp4"
	}
	outputPath := filepath.Join(outputDir, fmt.Sprintf("%s_processed.%s", base, format))

	outFile, err := os.Create(outputPath)
	if err != nil {
		return "", fmt.Errorf("create output file: %w", err)
	}
	defer func() {
		_ = outFile.Close()
	}()

	if _, err := io.Copy(outFile, processed.Reader); err != nil {
		return "", fmt.Errorf("write processed video: %w", err)
	}

	return outputPath, nil
}
