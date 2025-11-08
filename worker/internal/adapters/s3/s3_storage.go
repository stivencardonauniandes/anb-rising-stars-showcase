package s3

import (
	"context"
	"io"
	"strings"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"go.uber.org/zap"
)

type S3Storage struct {
	client *s3.Client
	bucket string
	prefix string
	logger *zap.Logger
}

// NewS3Storage creates a new S3 storage adapter
// region: AWS region (e.g., "us-east-1")
// bucket: S3 bucket name
// prefix: Optional prefix for all object keys (e.g., "videos/")
// accessKey: AWS access key ID (optional, will use default credentials chain if empty)
// secretKey: AWS secret access key (optional, will use default credentials chain if empty)
// endpoint: Optional custom endpoint for S3-compatible services (e.g., MinIO)
func NewS3Storage(region, bucket, prefix, accessKey, secretKey, endpoint string, logger *zap.Logger) (*S3Storage, error) {
	if logger == nil {
		logger = zap.NewNop()
	}

	var cfg aws.Config
	var err error

	// Configure AWS SDK
	ctx := context.Background()

	if accessKey != "" && secretKey != "" {
		// Use provided credentials
		cfg, err = config.LoadDefaultConfig(ctx,
			config.WithRegion(region),
			config.WithCredentialsProvider(credentials.NewStaticCredentialsProvider(accessKey, secretKey, "")),
		)
	} else {
		// Use default credentials chain (environment variables, IAM role, etc.)
		cfg, err = config.LoadDefaultConfig(ctx,
			config.WithRegion(region),
		)
	}

	if err != nil {
		logger.Error("failed to load AWS config", zap.Error(err))
		return nil, err
	}

	// Create S3 client options
	clientOptions := []func(*s3.Options){}

	// Add custom endpoint if provided (for S3-compatible services)
	if endpoint != "" {
		clientOptions = append(clientOptions, func(o *s3.Options) {
			o.BaseEndpoint = aws.String(endpoint)
			o.UsePathStyle = true // Required for MinIO and some S3-compatible services
		})
	}

	client := s3.NewFromConfig(cfg, clientOptions...)

	logger.Info("S3 storage initialized",
		zap.String("region", region),
		zap.String("bucket", bucket),
		zap.String("prefix", prefix),
		zap.String("endpoint", endpoint))

	return &S3Storage{
		client: client,
		bucket: bucket,
		prefix: prefix,
		logger: logger,
	}, nil
}

func (s *S3Storage) Download(ctx context.Context, remotePath string) (io.ReadCloser, error) {
	key := strings.Join(strings.Split(remotePath, "/")[1:], "/")
	s.logger.Debug("downloading from S3",
		zap.String("bucket", s.bucket),
		zap.String("key", key))

	input := &s3.GetObjectInput{
		Bucket: aws.String(s.bucket),
		Key:    aws.String(key),
	}

	result, err := s.client.GetObject(ctx, input)
	if err != nil {
		s.logger.Error("failed to download from S3",
			zap.String("bucket", s.bucket),
			zap.String("key", key),
			zap.Error(err))
		return nil, err
	}

	s.logger.Info("successfully downloaded file from S3",
		zap.String("bucket", s.bucket),
		zap.String("key", key),
		zap.Int64("content_length", aws.ToInt64(result.ContentLength)))

	return result.Body, nil
}

func (s *S3Storage) Upload(ctx context.Context, remotePath string, data io.Reader) error {
	key := s.prefix + "/" + remotePath
	s.logger.Info("uploading to S3",
		zap.String("bucket", s.bucket),
		zap.String("key", key),
		zap.String("remote_path", remotePath),
		zap.String("prefix", s.prefix))

	input := &s3.PutObjectInput{
		Bucket: aws.String(s.bucket),
		Key:    aws.String(key),
		Body:   data,
	}

	_, err := s.client.PutObject(ctx, input)
	if err != nil {
		s.logger.Error("failed to upload to S3",
			zap.String("bucket", s.bucket),
			zap.String("key", key),
			zap.Error(err))
		return err
	}

	s.logger.Info("successfully uploaded file to S3",
		zap.String("bucket", s.bucket),
		zap.String("key", key))

	return nil
}
