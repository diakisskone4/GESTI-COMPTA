"""Validation sécurisée des fichiers déposés (sujets et corrigés d'examen).

Contrôles : extension autorisée, taille maximale, signature binaire réelle du fichier (un .exe renommé
en .pdf est refusé) et nom de stockage aléatoire (le nom d'origine n'est jamais utilisé comme chemin).
"""
import os
import uuid

from django.conf import settings
from rest_framework.exceptions import ValidationError

# extension -> (type MIME servi, signatures binaires acceptées)
ALLOWED = {
    'pdf': ('application/pdf', [b'%PDF-']),
    'docx': ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', [b'PK\x03\x04']),
    'png': ('image/png', [b'\x89PNG\r\n\x1a\n']),
    'jpg': ('image/jpeg', [b'\xff\xd8\xff']),
    'jpeg': ('image/jpeg', [b'\xff\xd8\xff']),
}


def extension_of(name):
    return os.path.splitext(name or '')[1].lower().lstrip('.')


def validate_upload(file, label='Fichier'):
    ext = extension_of(file.name)
    if ext not in ALLOWED:
        raise ValidationError(f'{label} : format non autorisé. Formats acceptés : PDF, Word (.docx), PNG, JPG.')
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if file.size > max_bytes:
        raise ValidationError(f'{label} : {settings.MAX_UPLOAD_MB} Mo maximum.')
    if file.size == 0:
        raise ValidationError(f'{label} : le fichier est vide.')
    head = file.read(16)
    file.seek(0)
    if not any(head.startswith(sig) for sig in ALLOWED[ext][1]):
        raise ValidationError(f'{label} : le contenu ne correspond pas à un fichier .{ext} valide.')
    if ext == 'docx':
        _check_docx(file, label)
    return file


def _check_docx(file, label):
    """Un .docx est une archive ZIP : on refuse les documents contenant des macros."""
    import zipfile
    try:
        with zipfile.ZipFile(file) as z:
            names = z.namelist()
    except zipfile.BadZipFile:
        raise ValidationError(f'{label} : document Word illisible.')
    finally:
        file.seek(0)
    if 'word/document.xml' not in names:
        raise ValidationError(f'{label} : ce n\'est pas un document Word valide.')
    if any(n.lower().endswith('vbaproject.bin') for n in names):
        raise ValidationError(f'{label} : les documents contenant des macros sont refusés.')


def random_path(folder):
    def upload_to(instance, filename):
        return f'{folder}/{uuid.uuid4().hex}.{extension_of(filename)}'
    return upload_to


def content_type_for(name):
    return ALLOWED.get(extension_of(name), ('application/octet-stream', []))[0]
