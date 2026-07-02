"""Local-first personal data vault for AI agents."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import tomllib

__all__ = ["__version__"]


def _version_from_pyproject() -> str:
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    payload = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return str(payload["project"]["version"])


try:
    __version__ = version("agent-personal-vault")
except PackageNotFoundError:
    __version__ = _version_from_pyproject()
