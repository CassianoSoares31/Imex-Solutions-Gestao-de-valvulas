"""Storage de anexos com dois backends:

- **Supabase Storage** (REST via `requests`) quando SUPABASE_URL/KEY/BUCKET
  estiverem configurados.
- **Banco de dados** (StorageBlob) como fallback quando Supabase não está
  configurado. Serve para desenvolvimento local e ambientes sem storage externo.

A escolha é automática via `is_configured()`. O banco guarda só a `storage_key`;
o conteúdo vive no backend ativo.
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_TIMEOUT = 30  # segundos


class StorageError(Exception):
    """Falha ao guardar/ler um anexo."""


def is_configured():
    """True se o Supabase Storage está configurado; senão usa banco de dados."""
    return bool(
        getattr(settings, "SUPABASE_URL", "")
        and getattr(settings, "SUPABASE_KEY", "")
        and getattr(settings, "SUPABASE_BUCKET", "")
    )


# ── Backend: banco de dados (StorageBlob) ────────────────────────────────────

def _db_upload(storage_key, conteudo_bytes):
    from .models import StorageBlob
    StorageBlob.objects.update_or_create(key=storage_key, defaults={"data": conteudo_bytes})


def _db_download(storage_key):
    from .models import StorageBlob
    try:
        blob = StorageBlob.objects.get(key=storage_key)
        return bytes(blob.data)
    except StorageBlob.DoesNotExist as exc:
        raise StorageError(f"Anexo não encontrado no banco: {storage_key}") from exc


def _db_delete(storage_key):
    from .models import StorageBlob
    StorageBlob.objects.filter(key=storage_key).delete()


# ── Backend: Supabase Storage ────────────────────────────────────────────────

def _supabase_config():
    url = (getattr(settings, "SUPABASE_URL", "") or "").rstrip("/")
    key = getattr(settings, "SUPABASE_KEY", "") or ""
    bucket = getattr(settings, "SUPABASE_BUCKET", "") or ""
    return url, key, bucket


def _supabase_headers(key, extra=None):
    h = {"Authorization": f"Bearer {key}"}
    if extra:
        h.update(extra)
    return h


def _supabase_upload(storage_key, conteudo_bytes, content_type):
    url, key, bucket = _supabase_config()
    endpoint = f"{url}/storage/v1/object/{bucket}/{storage_key}"
    try:
        resp = requests.post(
            endpoint,
            data=conteudo_bytes,
            headers=_supabase_headers(key, {"Content-Type": content_type, "x-upsert": "true"}),
            timeout=_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise StorageError(f"Erro de rede ao subir anexo: {exc}") from exc
    if resp.status_code not in (200, 201):
        raise StorageError(f"Upload falhou ({resp.status_code}): {resp.text}")


def _supabase_download(storage_key):
    url, key, bucket = _supabase_config()
    endpoint = f"{url}/storage/v1/object/{bucket}/{storage_key}"
    try:
        resp = requests.get(endpoint, headers=_supabase_headers(key), timeout=_TIMEOUT)
    except requests.RequestException as exc:
        raise StorageError(f"Erro de rede ao baixar anexo: {exc}") from exc
    if resp.status_code != 200:
        raise StorageError(f"Download falhou ({resp.status_code}): {resp.text}")
    return resp.content


def _supabase_delete(storage_key):
    url, key, bucket = _supabase_config()
    endpoint = f"{url}/storage/v1/object/{bucket}/{storage_key}"
    try:
        resp = requests.delete(endpoint, headers=_supabase_headers(key), timeout=_TIMEOUT)
    except requests.RequestException as exc:
        raise StorageError(f"Erro de rede ao excluir anexo: {exc}") from exc
    if resp.status_code not in (200, 204):
        raise StorageError(f"Exclusão falhou ({resp.status_code}): {resp.text}")


# ── API pública (escolhe backend automaticamente) ────────────────────────────

def upload(storage_key, conteudo_bytes, content_type="application/octet-stream"):
    """Sobe um objeto pro backend ativo (Supabase ou banco de dados)."""
    if is_configured():
        _supabase_upload(storage_key, conteudo_bytes, content_type)
    else:
        _db_upload(storage_key, conteudo_bytes)


def download(storage_key):
    """Baixa o objeto do backend ativo e retorna os bytes."""
    if is_configured():
        return _supabase_download(storage_key)
    return _db_download(storage_key)


def delete(storage_key):
    """Remove o objeto do backend ativo."""
    if is_configured():
        _supabase_delete(storage_key)
    else:
        _db_delete(storage_key)

# .
