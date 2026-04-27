from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_mock_data_path() -> Path:
    return get_project_root() / "mock_data"
