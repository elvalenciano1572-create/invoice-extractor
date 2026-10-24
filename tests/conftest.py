import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

import make_samples  # noqa: E402


@pytest.fixture(scope="session")
def samples_dir(tmp_path_factory) -> Path:
    folder = tmp_path_factory.mktemp("invoices")
    make_samples.generate(folder)
    return folder
