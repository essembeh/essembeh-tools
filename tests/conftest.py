from pathlib import Path

import pytest


@pytest.fixture
def sample_video() -> Path:
    return Path(__file__).parent.parent / "data" / "sample.mp4"


@pytest.fixture
def sample2_video() -> Path:
    return Path(__file__).parent.parent / "data" / "sample2.mp4"
