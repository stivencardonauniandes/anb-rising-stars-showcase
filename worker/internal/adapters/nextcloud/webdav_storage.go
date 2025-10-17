package nextcloud

import (
	"bytes"
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

	// Try ReadStream first and read all content immediately
	stream, err := s.client.ReadStream(fullPath)
	if err != nil {
		s.logger.Error("failed to open stream from Nextcloud", zap.String("path", fullPath), zap.Error(err))
		return nil, err
	}

	// Read all content from the stream immediately before it gets closed
	data, err := io.ReadAll(stream)
	_ = stream.Close() // Close the original stream

	if err != nil {
		s.logger.Error("failed to read stream data", zap.String("path", fullPath), zap.Error(err))
		return nil, err
	}

	s.logger.Info("successfully downloaded file from Nextcloud",
		zap.String("path", fullPath),
		zap.Int("bytes", len(data)))

	// Wrap the byte slice in a ReadCloser
	return io.NopCloser(bytes.NewReader(data)), nil
}

func (s *WebDAVStorage) Upload(ctx context.Context, remotePath string, data io.Reader) error {
	fullPath := s.fullPath(remotePath)
	s.logger.Info("uploading to Nextcloud",
		zap.String("remote_path", remotePath),
		zap.String("full_path", fullPath),
		zap.String("root", s.root))
	return s.client.WriteStream(fullPath, data, 0644)
}

func (s *WebDAVStorage) fullPath(p string) string {
	return path.Join(s.root, p)
}
