# serverless/ — host Beat Toolkit as a RunPod endpoint

See the main [README section 33](../README.md#33-serverless) for the full guide.

- `handler.py` — routes one `input.task` (`beat` / `tag` / `flip`) to the toolkit scripts.
- `Dockerfile` — GPU worker image (build `--platform linux/amd64`).

Quick local test (no Docker/cloud needed):

```bash
pip install runpod
python serverless/handler.py --test_input '{"input":{"task":"beat","style":"boom_bap","bpm":90}}'
```
