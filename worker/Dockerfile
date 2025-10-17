# syntax=docker/dockerfile:1

# Builder and runtime combined since we want the Go toolchain available alongside ffmpeg.
FROM golang:alpine

# Allow Go modules and reduce noise from prompts.
ENV GO111MODULE=on \
    CGO_ENABLED=0 \
    FFMPEG_PATH=/usr/bin/ffmpeg \
    FFPROBE_PATH=/usr/bin/ffprobe \
    VIDEO_TEMP_DIR=/tmp/video-worker

WORKDIR /app

# Install ffmpeg, fonts, and supporting tooling without leaving behind apk caches.
RUN apk update && \
    apk upgrade --no-cache && \
    apk add --no-cache ffmpeg git ttf-dejavu fontconfig

# Cache module downloads separately.
COPY go.mod go.sum ./
RUN go mod download

# Copy the rest of the worker sources.
COPY . .

# Build the worker binary from the top-level main.go so it's ready to run by default.
RUN go build -o bin/worker .

ENTRYPOINT ["/app/bin/worker"]
