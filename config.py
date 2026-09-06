# generalized numnber of thread availables
import os
from dotenv import load_dotenv

load_dotenv()

MAX_REPORT_LIMIT = 10

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
DETECTION_MODEL = os.environ.get('DETECTION_MODEL', 'claude-haiku-4-5-20251001')
ENABLE_ANTROPIC = 'True'
#ENABLE_ANTROPIC = os.environ.get('ENABLE_ANTROPIC', 'False') == 'True'
