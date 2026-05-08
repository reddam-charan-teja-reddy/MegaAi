import io
from PIL import Image

from app.cv.pipeline import FaceDetectionPipeline


def test_pipeline_process_frame_outputs_jpeg(model_path):
    pipeline = FaceDetectionPipeline()
    pipeline.setup()

    image = Image.new("RGB", (64, 64), color="white")
    buf = io.BytesIO()
    image.save(buf, format="JPEG")

    output_bytes, roi = pipeline.process_frame(buf.getvalue())

    assert output_bytes[:2] == b"\xff\xd8"
    assert output_bytes[-2:] == b"\xff\xd9"
    assert roi is None or (len(roi) == 4 and all(isinstance(x, float) for x in roi))
