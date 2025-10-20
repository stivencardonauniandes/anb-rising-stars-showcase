# Worker

## Local video processing

To process a single video file locally and store the processed output beside the original file, run the command-line tool from the `worker` module:

```shell
go run ./cmd --input /path/to/video.mp4
```

If you omit the `--input` flag, pass the video path as the first positional argument instead. The processed file will be created next to the source file with a `_processed` suffix.

