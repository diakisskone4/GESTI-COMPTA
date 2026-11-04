"""Stockage des fichiers déposés dans PostgreSQL.

Sur Vercel le disque est en lecture seule : les sujets et corrigés sont conservés dans la base Neon.
Les fichiers ne sont jamais exposés par URL : ils passent toujours par l'API (contrôle des droits).
"""
from io import BytesIO

from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class DatabaseStorage(Storage):
    def _model(self):
        from .models import StoredFile
        return StoredFile

    def _open(self, name, mode='rb'):
        row = self._model().objects.filter(name=name).first()
        if row is None:
            raise FileNotFoundError(name)
        return File(BytesIO(bytes(row.content)), name=name)

    def _save(self, name, content):
        content.seek(0)
        data = content.read()
        self._model().objects.update_or_create(name=name, defaults={'content': data, 'size': len(data)})
        return name

    def exists(self, name):
        return self._model().objects.filter(name=name).exists()

    def delete(self, name):
        self._model().objects.filter(name=name).delete()

    def size(self, name):
        row = self._model().objects.filter(name=name).values('size').first()
        if row is None:
            raise FileNotFoundError(name)
        return row['size']

    def url(self, name):
        return ''  # pas d'URL publique : accès uniquement via l'API
