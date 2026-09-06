# fastapi_app/services/detection.py (nome file indicativo, adatta al tuo progetto FastAPI)
import anthropic, json, base64, io, os
from PIL import Image

from config import ANTHROPIC_API_KEY, DETECTION_MODEL
#ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
#DETECTION_MODEL = os.environ.get('DETECTION_MODEL', 'claude-haiku-4-5-20251001')


def prepare_image_for_api(image_path, max_dimension=1024):
    img = Image.open(image_path).convert("RGB")
    img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def detect_sensitive_regions(image_path):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    img_b64 = prepare_image_for_api(image_path)

    msg = client.messages.create(
        model=DETECTION_MODEL,
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}},
                {"type": "text", "text": "..."}  # stesso prompt di sempre
            ]
        }]
    )
    text = msg.content[0].text.strip().strip("```json").strip("```")
    return json.loads(text)
