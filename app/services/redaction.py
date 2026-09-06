# app/services/redaction.py
import os
import requests
from urllib.parse import quote
from PIL import Image


def apply_redaction_simple(image_path, boxes, output_dir, report_id):
    img = Image.open(image_path).convert("RGB")
    w, h = img.size

    for box in boxes:
        x1, y1 = int(box.x * w), int(box.y * h)
        x2, y2 = int((box.x + box.w) * w), int((box.y + box.h) * h)
        region = img.crop((x1, y1, x2, y2))
        small = region.resize((max(1, (x2 - x1) // 10), max(1, (y2 - y1) // 10)))
        pixelated = small.resize((x2 - x1, y2 - y1), Image.NEAREST)
        img.paste(pixelated, (x1, y1))

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"redacted_{report_id}.jpg")
    img.save(out_path, quality=90)
    return out_path


def build_original_backup_filename(original_filename):
    name, ext = original_filename.rsplit('.', 1)
    return f"{name}_original.{ext}"


def put_file_to_remote(local_path, remote_filename, upload_base_url):
    """PUT generico verso il backend CustomRemoteStorage."""
    with open(local_path, 'rb') as f:
        file_data = f.read()

    remote_path = f"uploaded_images/{remote_filename}"
    url = f"{upload_base_url}/{quote(remote_path)}"

    headers = {
        'Content-Type': 'application/octet-stream',
        'Content-Length': str(len(file_data)),
    }

    resp = requests.put(url, data=file_data, headers=headers, timeout=15)
    if not resp.ok:
        raise Exception(f"Upload fallito verso {url}: {resp.status_code} - {resp.text}")

    return remote_path


def redact_and_swap(image_path, local_redacted_path, original_filename, upload_base_url, media_base_url):
    """
    1. Preserva l'originale sotto nuovo nome (_original)
    2. Sovrascrive il file pubblico esistente con la versione pixelata
    Ritorna l'URL dell'originale preservato, per tracciamento.

    NOTA: redacted_image sul model contiene questo backup dell'originale,
    non la versione pixelata (che vive sotto image_url).
    """
    backup_filename = build_original_backup_filename(original_filename)
    backup_remote_path = put_file_to_remote(image_path, backup_filename, upload_base_url)

    put_file_to_remote(local_redacted_path, original_filename, upload_base_url)

    return f"{media_base_url}/{backup_remote_path}"

def upload_redacted_to_remote(local_path, remote_filename, upload_base_url, media_base_url):
    """
    Carica il file pixelato sul server remoto via PUT, stesso contratto
    del backend CustomRemoteStorage di Django.
    """
    with open(local_path, 'rb') as f:
        file_data = f.read()

    remote_path = f"uploaded_images/{remote_filename}"  # verifica se serve questo prefisso di cartella
    url = f"{upload_base_url}/{quote(remote_path)}"

    headers = {
        'Content-Type': 'application/octet-stream',
        'Content-Length': str(len(file_data)),
    }

    resp = requests.put(url, data=file_data, headers=headers, timeout=15)
    resp.raise_for_status()

    return f"{media_base_url}/{remote_path}"

def build_redacted_filename(original_filename, regions):
    types_found = {r['type'] for r in regions}
    if types_found == {'face'}:
        suffix = '_facing'
    elif types_found == {'plate'}:
        suffix = '_plating'
    else:
        suffix = '_redacted'

    name, ext = original_filename.rsplit('.', 1)
    return f"{name}{suffix}.{ext}"


