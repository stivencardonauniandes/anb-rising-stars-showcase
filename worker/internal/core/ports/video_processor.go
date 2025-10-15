package ports

import (
	"context"
	"io"
	"time"
)

type WatermarkPosition string

const (
	WatermarkTopLeft     WatermarkPosition = "top-left"
	WatermarkTopRight    WatermarkPosition = "top-right"
	WatermarkBottomLeft  WatermarkPosition = "bottom-left"
	WatermarkBottomRight WatermarkPosition = "bottom-right"
	WatermarkCenter      WatermarkPosition = "center"
)

type WatermarkOptions struct {
	Text          string
	FontFile      string
	FontColor     string
	FontSize      int
	BorderWidth   int
	BorderColor   string
	Position      WatermarkPosition
	MarginX       int
	MarginY       int
	StartDuration time.Duration
	EndDuration   time.Duration
}

type VideoProcessingOptions struct {
	ClipDuration time.Duration
	TargetWidth  int
	TargetHeight int
	TargetFormat string
	RemoveAudio  bool
	Watermark    *WatermarkOptions
}

type ProcessedVideo struct {
	Reader   io.ReadCloser
	Format   string
	Duration time.Duration
	Metadata map[string]string
}

func (p *ProcessedVideo) Close() error {
	if p == nil || p.Reader == nil {
		return nil
	}
	return p.Reader.Close()
}

type VideoProcessor interface {
	Process(ctx context.Context, input io.Reader, opts VideoProcessingOptions) (*ProcessedVideo, error)
}
