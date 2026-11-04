import shutil
from pathlib import Path

import pytest

from housing_lima.paths import FIXTURE_RUN as FIXTURE


@pytest.fixture
def sample_run(tmp_path) -> Path:
    """A writable copy of the SYNTHETIC fixture run."""
    dst = tmp_path / "20261103-0900-synthetic-fixture"
    shutil.copytree(FIXTURE, dst)
    return dst
