"""Central config, all from environment so the same image runs anywhere."""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings:
    # storage / infra
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./beat_saas.db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    RESULTS_DIR = os.getenv("RESULTS_DIR", os.path.join(REPO_ROOT, "server", "results"))
    SCRIPTS_DIR = os.getenv("SCRIPTS_DIR", os.path.join(REPO_ROOT, "scripts"))
    PYTHON_BIN = os.getenv("PYTHON_BIN", sys.executable)
    # Two lanes: CPU tasks (beat/tag) and GPU tasks (flip/remix/song) so GPU
    # workers only pull jobs that need a GPU.
    CPU_QUEUE = os.getenv("CPU_QUEUE", "beat-cpu")
    GPU_QUEUE = os.getenv("GPU_QUEUE", "beat-gpu")
    # Which queues THIS worker process consumes (comma-sep). Default: both.
    WORKER_QUEUES = os.getenv("WORKER_QUEUES", "")
    JOB_TIMEOUT = int(os.getenv("JOB_TIMEOUT", "1800"))  # seconds a job may run

    # auth / signup
    ALLOW_SIGNUP = os.getenv("ALLOW_SIGNUP", "true").lower() == "true"
    # When public signup is off, an admin can still mint accounts by sending
    # this token in the X-Admin-Token header (leave blank to disable).
    ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
    FREE_CREDITS = int(os.getenv("FREE_CREDITS", "10"))  # granted on signup

    # Stripe
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_SUCCESS_URL = os.getenv("STRIPE_SUCCESS_URL", "https://example.com/success")
    STRIPE_CANCEL_URL = os.getenv("STRIPE_CANCEL_URL", "https://example.com/cancel")
    # JSON map of Stripe price id -> {"plan": "...", "credits": N}
    STRIPE_PRICES = os.getenv("STRIPE_PRICES", "{}")


settings = Settings()
