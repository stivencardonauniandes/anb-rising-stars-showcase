package ports

import (
	"context"

	"github.com/alejandro/video-worker/internal/core/domain"
)

type VideoRepository interface {
	FindByID(ctx context.Context, id string) (*domain.Video, error)
	Update(ctx context.Context, video *domain.Video) error
}
