package nextcloud

import (
	"context"
	"io"
	"net/url"
	"path"

	"github.com/studio-b12/gowebdav"
	"go.uber.org/zap"
)

type WebDAVStorage struct {
	client *gowebdav.Client
	root   string
	logger *zap.Logger
}

func NewWebDAVStorage(baseURL, root, username, password string, logger *zap.Logger) (*WebDAVStorage, error) {
	parsed, err := url.Parse(baseURL)
	if err != nil {
		return nil, err
	}
	if logger == nil {
		logger = zap.NewNop()
	}

	client := gowebdav.NewClient(parsed.String(), username, password)

	return &WebDAVStorage{
		client: client,
		root:   root,
		logger: logger,
	}, nil
}

func (s *WebDAVStorage) Download(ctx context.Context, remotePath string) (io.ReadCloser, error) {
	fullPath := s.fullPath(remotePath)
	s.logger.Debug("downloading from Nextcloud", zap.String("path", fullPath))
	return s.client.ReadStream(fullPath)
}

func (s *WebDAVStorage) Upload(ctx context.Context, remotePath string, data io.Reader) error {
	fullPath := s.fullPath(remotePath)
	s.logger.Debug("uploading to Nextcloud", zap.String("path", fullPath))
	return s.client.WriteStream(fullPath, data, 0644)
}

func (s *WebDAVStorage) fullPath(p string) string {
	return path.Join(s.root, p)
}
