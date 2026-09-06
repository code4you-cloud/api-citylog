# generalized numnber of thread availables
import os
from dotenv import load_dotenv

MAX_REPORT_LIMIT = 10

#ANTHROPIC
load_dotenv()

print(f"[DEBUG] .env caricato, ENABLE_ANTROPIC raw = {os.environ.get('ENABLE_ANTROPIC')}")

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
DETECTION_MODEL = os.environ.get('DETECTION_MODEL', 'claude-haiku-4-5-20251001')
ENABLE_ANTROPIC = os.environ.get('ENABLE_ANTROPIC', 'False') == 'True'

if ENABLE_ANTROPIC and not ANTHROPIC_API_KEY:
    raise RuntimeError(
        "ENABLE_ANTROPIC=True ma ANTHROPIC_API_KEY non è impostata. "
        "Verifica che il file .env esista nella root del progetto e contenga la chiave."
    )

AUTO_REDACT_THRESHOLD = float(os.environ.get('AUTO_REDACT_THRESHOLD', '0.90'))

# cartella appoggio targhe visi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REDACTED_OUTPUT_DIR = os.environ.get(
        'REDACTED_OUTPUT_DIR',
        os.path.join(BASE_DIR, 'media', 'redacted')
)
REMOTE_UPLOAD_URL = os.environ.get('REMOTE_UPLOAD_URL', 'https://ws.citylog.cloud/upload')
REMOTE_MEDIA_URL = os.environ.get('REMOTE_MEDIA_URL', 'https://ws.citylog.cloud/media')

#REDACTED_OUTPUT_DIR = os.environ.get('REDACTED_OUTPUT_DIR', '/home/remote/api-citylog/media/redacted')
