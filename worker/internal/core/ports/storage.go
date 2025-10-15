package ports

import (
	"context"
	"io"
)

type Storage interface {
	Download(ctx context.Context, remotePath string) (io.ReadCloser, error)
	Upload(ctx context.Context, remotePath string, data io.Reader) error
}
