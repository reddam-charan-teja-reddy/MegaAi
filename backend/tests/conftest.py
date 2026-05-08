import urllib.request
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_detector/"
    "blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
)


def _resolve_model_path() -> Path:
    model_path = Path(settings.MODEL_PATH)
    if model_path.is_absolute():
        return model_path

    from app.cv import pipeline as pipeline_module

    return Path(pipeline_module.__file__).resolve().parent / model_path


@pytest.fixture(scope="session")
def model_path() -> Path:
    path = _resolve_model_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(MODEL_URL, path.as_posix())
    return path


@pytest.fixture()
def client(model_path):
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
