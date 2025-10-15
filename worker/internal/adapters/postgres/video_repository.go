package postgres

import (
	"context"
	"database/sql"
	"errors"
	"fmt"

	"go.uber.org/zap"

	"github.com/alejandro/video-worker/internal/core/domain"
)

type VideoRepository struct {
	db     *sql.DB
	logger *zap.Logger
}

func NewVideoRepository(db *sql.DB, logger *zap.Logger) *VideoRepository {
	if logger == nil {
		logger = zap.NewNop()
	}
	return &VideoRepository{db: db, logger: logger}
}

func (r *VideoRepository) FindByID(ctx context.Context, id string) (*domain.Video, error) {
	const query = `
SELECT id,
       user_id,
       raw_video_id,
       processed_video_id,
       title,
       status,
       uploaded_at,
       processed_at,
       original_url,
       processed_url,
       votes
FROM "VIDEO"
WHERE id = $1`

	video := &domain.Video{}
	var (
		status           string
		processedVideoID sql.NullString
		processedURL     sql.NullString
		processedAt      sql.NullTime
	)

	if err := r.db.QueryRowContext(ctx, query, id).Scan(
		&video.ID,
		&video.UserID,
		&video.RawVideoID,
		&processedVideoID,
		&video.Title,
		&status,
		&video.UploadedAt,
		&processedAt,
		&video.OriginalURL,
		&processedURL,
		&video.Votes,
	); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, fmt.Errorf("video %s not found: %w", id, err)
		}
		return nil, err
	}

	if processedVideoID.Valid {
		value := processedVideoID.String
		video.ProcessedVideoID = &value
	}
	if processedURL.Valid {
		value := processedURL.String
		video.ProcessedURL = &value
	}
	if processedAt.Valid {
		value := processedAt.Time
		video.ProcessedAt = &value
	}

	video.Status = toVideoStatus(status)
	return video, nil
}

func (r *VideoRepository) Update(ctx context.Context, video *domain.Video) error {
	const stmt = `
UPDATE "VIDEO"
SET status = $2,
    processed_video_id = $3,
    processed_url = $4,
    processed_at = $5
WHERE id = $1`

	processedVideoID := sql.NullString{}
	if video.ProcessedVideoID != nil && *video.ProcessedVideoID != "" {
		processedVideoID = sql.NullString{String: *video.ProcessedVideoID, Valid: true}
	}

	processedURL := sql.NullString{}
	if video.ProcessedURL != nil && *video.ProcessedURL != "" {
		processedURL = sql.NullString{String: *video.ProcessedURL, Valid: true}
	}

	processedAt := sql.NullTime{}
	if video.ProcessedAt != nil {
		processedAt = sql.NullTime{Time: *video.ProcessedAt, Valid: true}
	}

	_, err := r.db.ExecContext(ctx, stmt, video.ID, string(video.Status), processedVideoID, processedURL, processedAt)
	return err
}

func toVideoStatus(raw string) domain.VideoStatus {
	switch domain.VideoStatus(raw) {
	case domain.VideoStatusUploaded,
		domain.VideoStatusProcessed,
		domain.VideoStatusDeleted:
		return domain.VideoStatus(raw)
	default:
		return domain.VideoStatusUploaded
	}
}
