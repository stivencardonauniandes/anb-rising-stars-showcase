package ffmpeg

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"
	"math"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/alejandro/video-worker/internal/core/ports"
	"go.uber.org/zap"
)

const (
	defaultClipDuration    = 30 * time.Second
	defaultWidth           = 1280
	defaultHeight          = 720
	curtainSegmentDuration = 2500 * time.Millisecond
)

type VideoProcessor struct {
	ffmpegPath  string
	ffprobePath string
	tempDir     string
	logger      *zap.Logger
}

func NewVideoProcessor(ffmpegPath, ffprobePath, tempDir string, logger *zap.Logger) *VideoProcessor {
	if ffmpegPath == "" {
		ffmpegPath = "ffmpeg"
	}
	if ffprobePath == "" {
		ffprobePath = "ffprobe"
	}
	if tempDir == "" {
		tempDir = os.TempDir()
	}
	if logger == nil {
		logger = zap.NewNop()
	}

	return &VideoProcessor{
		ffmpegPath:  ffmpegPath,
		ffprobePath: ffprobePath,
		tempDir:     tempDir,
		logger:      logger,
	}
}

func (p *VideoProcessor) Process(ctx context.Context, input io.Reader, opts ports.VideoProcessingOptions) (*ports.ProcessedVideo, error) {
	if input == nil {
		return nil, errors.New("ffmpeg processor: input reader is nil")
	}

	inputFile, err := os.CreateTemp(p.tempDir, "ffmpeg-input-*.mp4")
	if err != nil {
		return nil, fmt.Errorf("ffmpeg processor: create temp input: %w", err)
	}
	inputPath := inputFile.Name()
	defer func() {
		_ = os.Remove(inputPath)
	}()

	if _, err := io.Copy(inputFile, input); err != nil {
		_ = inputFile.Close()
		return nil, fmt.Errorf("ffmpeg processor: write temp input: %w", err)
	}
	if err := inputFile.Close(); err != nil {
		return nil, fmt.Errorf("ffmpeg processor: close temp input: %w", err)
	}

	duration, err := p.probeDuration(ctx, inputPath)
	if err != nil {
		p.logger.Warn("ffmpeg processor: probe duration failed", zap.Error(err))
	}

	clipDuration := opts.ClipDuration
	if clipDuration <= 0 {
		clipDuration = defaultClipDuration
	}
	if duration > 0 && (clipDuration > duration || clipDuration == 0) {
		clipDuration = duration
	}
	if clipDuration <= 0 {
		clipDuration = defaultClipDuration
	}

	width := opts.TargetWidth
	height := opts.TargetHeight
	if width <= 0 {
		width = defaultWidth
	}
	if height <= 0 {
		height = defaultHeight
	}

	contentSeconds := clipDuration.Seconds()
	curtainSeconds := curtainSegmentDuration.Seconds()
	totalDuration := clipDuration + 2*curtainSegmentDuration
	totalSeconds := totalDuration.Seconds()

	frameRate := "30"
	if rate, err := p.probeFrameRate(ctx, inputPath); err == nil && rate != "" {
		frameRate = rate
	} else if err != nil {
		p.logger.Debug("ffmpeg processor: probe frame rate failed", zap.Error(err))
	}

	baseFilters := []string{
		fmt.Sprintf("scale=%d:%d:force_original_aspect_ratio=decrease", width, height),
		fmt.Sprintf("pad=%d:%d:(%d-iw)/2:(%d-ih)/2", width, height, width, height),
		"setsar=1",
		"format=yuv420p",
	}
	if frameRate != "" {
		baseFilters = append(baseFilters, fmt.Sprintf("fps=%s", frameRate))
	}
	if contentSeconds > 0 {
		baseFilters = append(baseFilters, fmt.Sprintf("trim=duration=%.3f", contentSeconds), "setpts=PTS-STARTPTS")
	}

	filterParts := []string{fmt.Sprintf("[0:v]%s[vbase]", strings.Join(baseFilters, ","))}

	var watermarkCfg *watermarkConfig
	if opts.Watermark != nil {
		watermarkCfg = normalizeWatermark(opts.Watermark, contentSeconds)
	}

	mainLabel := "vbase"
	if watermarkCfg != nil {
		drawArgs := buildDrawTextArgs(watermarkCfg, true)
		filterParts = append(filterParts, fmt.Sprintf("[%s]drawtext=%s[vmain]", mainLabel, drawArgs))
		mainLabel = "vmain"
	}

	curtainBase := fmt.Sprintf("color=c=black:size=%dx%d:rate=%s:d=%.3f,format=yuv420p,setsar=1", width, height, frameRate, curtainSeconds)
	filterParts = append(filterParts,
		fmt.Sprintf("%s[vcurtain_start_base]", curtainBase),
		fmt.Sprintf("%s[vcurtain_end_base]", curtainBase),
	)

	startLabel := "vcurtain_start_base"
	endLabel := "vcurtain_end_base"
	if watermarkCfg != nil {
		curtainDrawArgs := buildDrawTextArgs(watermarkCfg, false)
		filterParts = append(filterParts,
			fmt.Sprintf("[%s]drawtext=%s[vcurtain_start]", startLabel, curtainDrawArgs),
			fmt.Sprintf("[%s]drawtext=%s[vcurtain_end]", endLabel, curtainDrawArgs),
		)
		startLabel = "vcurtain_start"
		endLabel = "vcurtain_end"
	}

	filterParts = append(filterParts, fmt.Sprintf("[%s][%s][%s]concat=n=3:v=1:a=0[vout]", startLabel, mainLabel, endLabel))
	filter := strings.Join(filterParts, ";")

	outputExt := opts.TargetFormat
	if outputExt == "" {
		outputExt = "mp4"
	}
	outputFile, err := os.CreateTemp(p.tempDir, "ffmpeg-output-*"+ensureExt(outputExt))
	if err != nil {
		return nil, fmt.Errorf("ffmpeg processor: create temp output: %w", err)
	}
	outputPath := outputFile.Name()
	if err := outputFile.Close(); err != nil {
		_ = os.Remove(outputPath)
		return nil, fmt.Errorf("ffmpeg processor: close temp output: %w", err)
	}

	args := []string{"-y", "-i", inputPath, "-filter_complex", filter, "-map", "[vout]"}

	args = append(args, "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-movflags", "+faststart")

	if opts.RemoveAudio {
		args = append(args, "-an")
	}

	if totalSeconds > 0 {
		args = append(args, "-t", fmt.Sprintf("%.3f", totalSeconds))
	}

	args = append(args, outputPath)

	cmd := exec.CommandContext(ctx, p.ffmpegPath, args...)
	var stderr bytes.Buffer
	cmd.Stdout = io.Discard
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		_ = os.Remove(outputPath)
		return nil, fmt.Errorf("ffmpeg processor: processing failed: %w: %s", err, stderr.String())
	}

	reader, err := os.Open(outputPath)
	if err != nil {
		_ = os.Remove(outputPath)
		return nil, fmt.Errorf("ffmpeg processor: open output: %w", err)
	}

	metadata := map[string]string{
		"clip_duration_seconds":   fmt.Sprintf("%.3f", contentSeconds),
		"curtain_segment_seconds": fmt.Sprintf("%.3f", curtainSeconds),
		"total_duration_seconds":  fmt.Sprintf("%.3f", totalSeconds),
		"frame_rate":              frameRate,
		"target_width":            strconv.Itoa(width),
		"target_height":           strconv.Itoa(height),
	}

	return &ports.ProcessedVideo{
		Reader:   &tempFileReadCloser{File: reader, path: outputPath},
		Format:   outputExt,
		Duration: totalDuration,
		Metadata: metadata,
	}, nil
}

func (p *VideoProcessor) probeFrameRate(ctx context.Context, path string) (string, error) {
	cmd := exec.CommandContext(ctx, p.ffprobePath, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=avg_frame_rate", "-of", "default=noprint_wrappers=1:nokey=1", path)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("ffprobe frame rate: %w: %s", err, string(output))
	}
	frameRate := strings.TrimSpace(string(output))
	if frameRate == "" || frameRate == "N/A" || frameRate == "0/0" {
		return "", errors.New("ffprobe frame rate: unavailable")
	}
	return frameRate, nil
}

func (p *VideoProcessor) probeDuration(ctx context.Context, path string) (time.Duration, error) {
	cmd := exec.CommandContext(ctx, p.ffprobePath, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path)
	var stderr bytes.Buffer
	cmd.Stdout = &stderr
	cmd.Stderr = &stderr
	output, err := cmd.Output()
	if err != nil {
		return 0, fmt.Errorf("ffprobe: %w: %s", err, stderr.String())
	}
	durStr := strings.TrimSpace(string(output))
	if durStr == "" {
		return 0, errors.New("ffprobe: empty duration")
	}
	durSec, err := strconv.ParseFloat(durStr, 64)
	if err != nil {
		return 0, fmt.Errorf("ffprobe: parse duration: %w", err)
	}
	if durSec <= 0 {
		return 0, nil
	}
	return time.Duration(durSec * float64(time.Second)), nil
}

func normalizeWatermark(opts *ports.WatermarkOptions, clipSeconds float64) *watermarkConfig {
	if opts == nil {
		return nil
	}

	text := opts.Text
	if text == "" {
		text = "Watermark"
	}

	fontColor := opts.FontColor
	if fontColor == "" {
		fontColor = "white"
	}

	fontSize := opts.FontSize
	if fontSize <= 0 {
		fontSize = 48
	}

	borderWidth := opts.BorderWidth
	if borderWidth < 0 {
		borderWidth = 0
	}

	borderColor := opts.BorderColor
	if borderColor == "" {
		borderColor = "black"
	}

	marginX := opts.MarginX
	if marginX < 0 {
		marginX = 0
	}

	marginY := opts.MarginY
	if marginY < 0 {
		marginY = 0
	}

	start := opts.StartDuration.Seconds()
	if start <= 0 {
		start = math.Min(3, math.Max(0.5, clipSeconds))
	}
	if clipSeconds > 0 {
		start = math.Min(start, clipSeconds)
	}

	end := opts.EndDuration.Seconds()
	if end <= 0 {
		end = math.Min(3, math.Max(0.5, clipSeconds))
	}
	if clipSeconds > 0 {
		end = math.Min(end, clipSeconds)
	}

	startTrigger := math.Max(0, clipSeconds-end)

	position := opts.Position
	if position == "" {
		position = ports.WatermarkBottomRight
	}

	return &watermarkConfig{
		Text:                 text,
		FontFile:             opts.FontFile,
		FontColor:            fontColor,
		FontSize:             fontSize,
		BorderWidth:          borderWidth,
		BorderColor:          borderColor,
		Position:             position,
		MarginX:              marginX,
		MarginY:              marginY,
		StartDurationSeconds: start,
		EndTriggerSeconds:    startTrigger,
	}
}

type watermarkConfig struct {
	Text                 string
	FontFile             string
	FontColor            string
	FontSize             int
	BorderWidth          int
	BorderColor          string
	Position             ports.WatermarkPosition
	MarginX              int
	MarginY              int
	StartDurationSeconds float64
	EndTriggerSeconds    float64
}

func positionExpressions(pos ports.WatermarkPosition, marginX, marginY int) (string, string) {
	x := "0"
	y := "0"
	mx := strconv.Itoa(marginX)
	my := strconv.Itoa(marginY)

	switch pos {
	case ports.WatermarkTopLeft:
		x = mx
		y = my
	case ports.WatermarkTopRight:
		x = fmt.Sprintf("w-text_w-%s", mx)
		y = my
	case ports.WatermarkBottomLeft:
		x = mx
		y = fmt.Sprintf("h-text_h-%s", my)
	case ports.WatermarkCenter:
		x = fmt.Sprintf("(w-text_w)/2")
		y = fmt.Sprintf("(h-text_h)/2")
	default:
		x = fmt.Sprintf("w-text_w-%s", mx)
		y = fmt.Sprintf("h-text_h-%s", my)
	}

	return x, y
}

func buildDrawTextArgs(wm *watermarkConfig, includeEnable bool) string {
	if wm == nil {
		return ""
	}

	xExpr, yExpr := positionExpressions(wm.Position, wm.MarginX, wm.MarginY)

	drawArgs := []string{}
	if wm.FontFile != "" {
		drawArgs = append(drawArgs, fmt.Sprintf("fontfile='%s'", escapeForFFMPEG(wm.FontFile)))
	}
	drawArgs = append(drawArgs,
		fmt.Sprintf("text='%s'", escapeDrawText(wm.Text)),
		fmt.Sprintf("fontcolor=%s", wm.FontColor),
		fmt.Sprintf("fontsize=%d", wm.FontSize),
		fmt.Sprintf("borderw=%d", wm.BorderWidth),
	)
	if wm.BorderWidth > 0 {
		drawArgs = append(drawArgs, fmt.Sprintf("bordercolor=%s", wm.BorderColor))
	}
	drawArgs = append(drawArgs,
		fmt.Sprintf("x=%s", xExpr),
		fmt.Sprintf("y=%s", yExpr),
	)
	if includeEnable {
		drawArgs = append(drawArgs, fmt.Sprintf("enable='lte(t,%.3f)+gte(t,%.3f)'", wm.StartDurationSeconds, wm.EndTriggerSeconds))
	}

	return strings.Join(drawArgs, ":")
}

func ensureExt(ext string) string {
	ext = strings.TrimSpace(ext)
	if ext == "" {
		return ".mp4"
	}
	if strings.HasPrefix(ext, ".") {
		return ext
	}
	return "." + ext
}

func escapeDrawText(value string) string {
	replaced := strings.ReplaceAll(value, `\`, `\\`)
	replaced = strings.ReplaceAll(replaced, `:`, `\:`)
	replaced = strings.ReplaceAll(replaced, `'`, `\\'`)
	replaced = strings.ReplaceAll(replaced, "\n", `\\n`)
	return replaced
}

func escapeForFFMPEG(value string) string {
	replaced := filepath.ToSlash(value)
	replaced = strings.ReplaceAll(replaced, `'`, `\\'`)
	return replaced
}

type tempFileReadCloser struct {
	*os.File
	path string
}

func (t *tempFileReadCloser) Close() error {
	err := t.File.Close()
	removeErr := os.Remove(t.path)
	if removeErr != nil && !errors.Is(removeErr, os.ErrNotExist) {
		if err != nil {
			return err
		}
		return removeErr
	}
	return err
}
