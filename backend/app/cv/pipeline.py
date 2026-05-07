import io
from PIL import Image, ImageDraw
import numpy as np
import mediapipe as mp

# Initialize MediaPipe Face Detection
mp_face_detection = mp.solutions.face_detection

class FaceDetectionPipeline:
    def __init__(self):
        self.detector = mp_face_detection.FaceDetection(
            model_selection=0, # 0 for short-range faces (webcam)
            min_detection_confidence=0.5
        )

    def process_frame(self, frame_bytes: bytes) -> tuple[bytes, tuple[float, float, float, float] | None]:
        """
        CPU-bound function run inside ThreadPool.
        Returns: (encoded JPEG bytes, ROI Tuple or None)
        """
        # 1. Decode: Convert bytes to a Pillow Image object
        try:
            image = Image.open(io.BytesFileIO(frame_bytes) if hasattr(io, 'BytesFileIO') else io.BytesIO(frame_bytes)).convert("RGB")
        except Exception as e:
            print("Failed to decode image bytes:", e)
            return frame_bytes, None

        width, height = image.size

        # 2. Detect: Convert to NumPy array for MediaPipe
        image_np = np.array(image)
        results = self.detector.process(image_np)

        roi_coords = None

        if results.detections:
            # Assume only one face as per requirements
            detection = results.detections[0]
            bbox = detection.location_data.relative_bounding_box
            
            # 3. Extract: Get minimal axis-aligned bounding box coordinates (Normalized)
            x_min = max(0.0, bbox.xmin)
            y_min = max(0.0, bbox.ymin)
            x_max = min(1.0, bbox.xmin + bbox.width)
            y_max = min(1.0, bbox.ymin + bbox.height)
            roi_coords = (float(x_min), float(y_min), float(x_max), float(y_max))

            # 4. Draw: Use Pillow's ImageDraw purely, bypassing OpenCV completely
            draw = ImageDraw.Draw(image)
            abs_x_min = int(x_min * width)
            abs_y_min = int(y_min * height)
            abs_x_max = int(x_max * width)
            abs_y_max = int(y_max * height)
            
            # Draw standard red rectangle around the region of interest
            draw.rectangle([abs_x_min, abs_y_min, abs_x_max, abs_y_max], outline="red", width=3)

        # 5. Encode: Compress the drawn Pillow Image back into JPEG bytes
        out_buffer = io.BytesIO()
        image.save(out_buffer, format="JPEG", quality=80)
        return out_buffer.getvalue(), roi_coords

pipeline = FaceDetectionPipeline()
