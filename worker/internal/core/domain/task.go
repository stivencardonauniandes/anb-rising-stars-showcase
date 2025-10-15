package domain

type Task struct {
	ID         string
	VideoID    string
	SourcePath string
	OutputPath string
	Attempt    int
	Metadata   map[string]string
}

func (t *Task) IncrementAttempt() {
	t.Attempt++
}
