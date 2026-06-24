// Co-Produce AI - Go client for a RunPod Serverless endpoint.
//
// Operator notes
// --------------
// Submits a job to your Co-Produce AI serverless endpoint (see README section
// 33), polls until it finishes, and - if the handler returns base64 audio
// (wav_b64) - decodes it straight to a .wav on disk. Works for all three
// handler tasks via -task:
//
//   beat : -style boom_bap -bpm 90        -> writes out.wav
//   flip : -path in.wav -prompt "dusty"   -> writes out.wav
//   tag  : -path in.wav                    -> prints JSON tags (no audio)
//
// Reads credentials from the environment so keys never live in the source:
//   RUNPOD_API_KEY  - account API key (console -> Settings -> API Keys)
//   ENDPOINT_ID     - your serverless endpoint id (console -> Serverless)
//
// Run:
//   go mod tidy
//   go run . -task beat -style trap -bpm 140 -out trap.wav
package main

import (
	"encoding/base64"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"time"

	"github.com/runpod/go-sdk/pkg/sdk"
	"github.com/runpod/go-sdk/pkg/sdk/config"
	rpEndpoint "github.com/runpod/go-sdk/pkg/sdk/endpoint"
)

func main() {
	task := flag.String("task", "beat", "beat | tag | flip")
	style := flag.String("style", "boom_bap", "beat style (beat task)")
	bpm := flag.Int("bpm", 90, "tempo in BPM (beat task)")
	prompt := flag.String("prompt", "", "steering prompt (flip task)")
	path := flag.String("path", "", "input audio path/URL (tag/flip tasks)")
	out := flag.String("out", "out.wav", "file to write returned audio to")
	interval := flag.Int("interval", 2, "seconds between status polls")
	flag.Parse()

	apiKey, endpointID := os.Getenv("RUNPOD_API_KEY"), os.Getenv("ENDPOINT_ID")
	if apiKey == "" || endpointID == "" {
		fmt.Fprintln(os.Stderr, "error: set RUNPOD_API_KEY and ENDPOINT_ID env vars first")
		os.Exit(1)
	}

	endpoint, err := rpEndpoint.New(
		&config.Config{ApiKey: sdk.String(apiKey)},
		&rpEndpoint.Option{EndpointId: sdk.String(endpointID)},
	)
	if err != nil {
		panic(err)
	}

	// Build the handler input payload for the chosen task.
	input := map[string]interface{}{"task": *task}
	switch *task {
	case "beat":
		input["style"], input["bpm"] = *style, *bpm
	case "flip":
		input["prompt"], input["path"] = *prompt, *path
	case "tag":
		input["path"] = *path
	}

	// 1) Submit asynchronously - returns a job id immediately.
	run, err := endpoint.Run(&rpEndpoint.RunInput{
		JobInput:       &rpEndpoint.JobInput{Input: input},
		RequestTimeout: sdk.Int(120),
	})
	if err != nil {
		panic(err)
	}
	jobID := deref(run.Id)
	fmt.Printf("submitted job %s (status %s)\n", jobID, deref(run.Status))

	// 2) Poll status until the job leaves IN_QUEUE/IN_PROGRESS.
	for {
		st, err := endpoint.Status(&rpEndpoint.StatusInput{Id: sdk.String(jobID)})
		if err != nil {
			panic(err)
		}
		status := deref(st.Status)
		fmt.Printf("status: %s\n", status)
		switch status {
		case "COMPLETED":
			writeOutput(st.Output, *out)
			return
		case "FAILED", "CANCELLED":
			fmt.Fprintf(os.Stderr, "job %s: %s\n", status, deref(st.Error))
			os.Exit(1)
		}
		time.Sleep(time.Duration(*interval) * time.Second)
	}
}

// deref safely reads an optional *string.
func deref(s *string) string {
	if s == nil {
		return ""
	}
	return *s
}

// writeOutput decodes wav_b64 to disk if present, otherwise prints the JSON.
func writeOutput(out *interface{}, path string) {
	if out == nil {
		fmt.Println("no output returned")
		return
	}
	m, ok := (*out).(map[string]interface{})
	if !ok {
		data, _ := json.Marshal(*out)
		fmt.Printf("output: %s\n", data)
		return
	}
	if b64, ok := m["wav_b64"].(string); ok && b64 != "" {
		raw, err := base64.StdEncoding.DecodeString(b64)
		if err != nil {
			panic(err)
		}
		if err := os.WriteFile(path, raw, 0o644); err != nil {
			panic(err)
		}
		fmt.Printf("wrote %s (%d bytes)\n", path, len(raw))
		return
	}
	data, _ := json.Marshal(m) // e.g. the tag task: print tags JSON
	fmt.Printf("output: %s\n", data)
}
