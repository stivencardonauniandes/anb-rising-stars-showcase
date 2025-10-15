package domain

import "time"

type VideoStatus string

const (
	VideoStatusUploaded  VideoStatus = "uploaded"
	VideoStatusProcessed VideoStatus = "processed"
	VideoStatusDeleted   VideoStatus = "deleted"
	VideoStatusFailed    VideoStatus = "failed"
)

type Video struct {
	ID               string
	UserID           string
	RawVideoID       string
	ProcessedVideoID *string
	Title            string
	Status           VideoStatus
	UploadedAt       time.Time
	ProcessedAt      *time.Time
	OriginalURL      string
	ProcessedURL     *string
	Votes            int
}

func (v *Video) MarkProcessed(processedAt time.Time, processedVideoID, processedURL string) {
	v.Status = VideoStatusProcessed
	v.ProcessedAt = &processedAt
	v.ProcessedVideoID = optionalString(processedVideoID)
	v.ProcessedURL = optionalString(processedURL)
}

func (v *Video) ResetToUploaded() {
	v.Status = VideoStatusUploaded
	v.ProcessedAt = nil
	v.ProcessedVideoID = nil
	v.ProcessedURL = nil
}

func optionalString(value string) *string {
	if value == "" {
		return nil
	}
	copy := value
	return &copy
}
