# S3 Storage Adapter

This adapter implements the `Storage` interface using AWS S3 or S3-compatible services (like MinIO).

## Configuration

The S3 adapter is configured via environment variables in the `.env` file.

### Required Environment Variables

```bash
# Set storage backend to S3
STORAGE_BACKEND=s3

# S3 Region
S3_REGION=us-east-1

# S3 Bucket Name
S3_BUCKET=video-processing-bucket
```

### Optional Environment Variables

```bash
# AWS Credentials (leave empty to use IAM roles or AWS environment variables)
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key

# Custom endpoint for S3-compatible services (leave empty for AWS S3)
S3_ENDPOINT=http://localhost:9000
```

**Note:** The `PROCESSED_BASE_URL` environment variable is used as the S3 key prefix for both NextCloud and S3 storage backends. This ensures consistency across different storage implementations.

## Authentication Methods

The adapter supports multiple authentication methods:

### 1. Static Credentials (Environment Variables)

Set `S3_ACCESS_KEY` and `S3_SECRET_KEY` in your `.env` file:

```bash
S3_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
S3_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

### 2. AWS Credentials Chain (Recommended for AWS)

Leave `S3_ACCESS_KEY` and `S3_SECRET_KEY` empty. The SDK will automatically use:
- Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- Shared credentials file (`~/.aws/credentials`)
- IAM role for EC2 instances
- IAM role for ECS tasks

### 3. IAM Roles for EC2/ECS (Best Practice)

When running on AWS infrastructure, attach an IAM role with S3 permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject"
            ],
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        }
    ]
}
```

## Usage Examples

### Example 1: AWS S3 with Static Credentials

```bash
STORAGE_BACKEND=s3
S3_REGION=us-east-1
S3_BUCKET=my-video-bucket
PROCESSED_BASE_URL=processed/
S3_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
S3_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
S3_ENDPOINT=
```

### Example 2: AWS S3 with IAM Role (EC2/ECS)

```bash
STORAGE_BACKEND=s3
S3_REGION=us-east-1
S3_BUCKET=my-video-bucket
PROCESSED_BASE_URL=processed/
S3_ACCESS_KEY=
S3_SECRET_KEY=
S3_ENDPOINT=
```

### Example 3: MinIO (S3-Compatible)

```bash
STORAGE_BACKEND=s3
S3_REGION=us-east-1
S3_BUCKET=videos
PROCESSED_BASE_URL=
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_ENDPOINT=http://minio:9000
```

### Example 4: DigitalOcean Spaces

```bash
STORAGE_BACKEND=s3
S3_REGION=nyc3
S3_BUCKET=my-space-name
PROCESSED_BASE_URL=videos/
S3_ACCESS_KEY=your_spaces_key
S3_SECRET_KEY=your_spaces_secret
S3_ENDPOINT=https://nyc3.digitaloceanspaces.com
```

## Key Prefix Behavior

The `PROCESSED_BASE_URL` option allows you to organize objects within your bucket:

- If `PROCESSED_BASE_URL=""` and you upload `video.mp4`, the S3 key will be: `video.mp4`
- If `PROCESSED_BASE_URL="videos/"` and you upload `video.mp4`, the S3 key will be: `videos/video.mp4`
- If `PROCESSED_BASE_URL="videos"` and you upload `video.mp4`, the S3 key will be: `videos/video.mp4`

## Switching Between NextCloud and S3

To switch from NextCloud to S3, simply change the `STORAGE_BACKEND` variable:

```bash
# Before (NextCloud)
STORAGE_BACKEND=nextcloud

# After (S3)
STORAGE_BACKEND=s3
```

Both adapters implement the same `ports.Storage` interface, so no code changes are required.

## Production Recommendations

1. **Use IAM Roles**: When running on AWS (EC2/ECS/Lambda), use IAM roles instead of static credentials
2. **Enable Encryption**: Enable server-side encryption on your S3 bucket
3. **Set Lifecycle Policies**: Configure lifecycle policies to manage object retention
4. **Enable Versioning**: Enable bucket versioning for data protection
5. **Monitor Costs**: Use CloudWatch and S3 analytics to monitor storage costs
6. **Set CORS**: If accessing from web applications, configure CORS policies

## Troubleshooting

### Error: "could not import github.com/aws/aws-sdk-go-v2/service/s3"

Run `go mod tidy` to download dependencies:
```bash
cd worker
go mod tidy
```

### Error: "S3_BUCKET is required when STORAGE_BACKEND=s3"

Make sure you've set the `S3_BUCKET` environment variable in your `.env` file.

### Error: "AccessDenied" or "InvalidAccessKeyId"

- Verify your AWS credentials are correct
- Check that the IAM user/role has the required S3 permissions
- For MinIO, verify the endpoint URL is accessible

### Error: "NoSuchBucket"

- Verify the bucket exists in the specified region
- Check that the bucket name is correct (bucket names are case-sensitive)
- For MinIO, create the bucket first using the MinIO console or CLI

## Performance Considerations

- **Multipart Uploads**: The AWS SDK automatically uses multipart uploads for large files
- **Connection Pooling**: The SDK maintains a connection pool for better performance
- **Timeout Settings**: The adapter respects the context timeout passed to `Download()` and `Upload()`
- **Regional Performance**: Choose a region close to your application for better latency
