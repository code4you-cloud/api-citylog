# fastapi_app/services/detection.py (nome file indicativo, adatta al tuo progetto FastAPI)
import io
import json
import base64
import tempfile
import requests
import anthropic
from PIL import Image
from config import ANTHROPIC_API_KEY, DETECTION_MODEL



def prepare_image_for_api(image_path, max_dimension=1024):
    img = Image.open(image_path).convert("RGB")
    img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()

def resolve_image_path(db_item):
    """Scarica l'immagine da image_url in un file temporaneo locale."""
    if not db_item.image_url:
        raise ValueError(f"Nessuna image_url per record {db_item.id}")

    resp = requests.get(db_item.image_url, timeout=10)
    resp.raise_for_status()

    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    tmp.write(resp.content)
    tmp.close()
    return tmp.name

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
                {"type": "text", "text": (
                    "Individua volti umani e targhe veicolari visibili in questa foto. "
                    "Rispondi SOLO con JSON: "
                    '[{"type":"face"|"plate","x":0-1,"y":0-1,"w":0-1,"h":0-1,"confidence":0-1}]. '
                    "Coordinate normalizzate rispetto a larghezza/altezza immagine, x/y = angolo top-left. "
                    "Se non trovi nulla, rispondi []."
                )}
            ]
        }]
    )
    text = msg.content[0].text.strip().strip("```json").strip("```")
    return json.loads(text)

def detect_sensitive_regions_(image_path):
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
