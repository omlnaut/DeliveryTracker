from pathlib import Path
import tempfile


def get_temp_dir() -> Path:
    """Get the temporary directory path for the current system."""
    return Path(tempfile.gettempdir())
