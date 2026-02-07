from pathlib import Path

def resolve_path(base: str | Path , path: str | Path) -> Path:
    path = Path(path)
    if path.is_absolute():
        return path
    return Path(base).resolve() / path    