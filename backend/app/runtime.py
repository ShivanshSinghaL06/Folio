"""Start the API after applying database migrations. Used by the container."""

import subprocess
import sys


def main() -> None:
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
            "8000",
        ]
    )


if __name__ == "__main__":
    main()
