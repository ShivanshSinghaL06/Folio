"""Start the API after applying database migrations. Used by the container."""

import os
import subprocess
import sys


def main() -> None:
    port = os.environ.get("PORT", "8000")
    subprocess.check_call([sys.executable, "-m", "alembic", "upgrade", "head"])
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            port,
        ]
    )


if __name__ == "__main__":
    main()
