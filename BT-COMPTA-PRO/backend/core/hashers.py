from django.contrib.auth.hashers import Argon2PasswordHasher


class OwaspArgon2PasswordHasher(Argon2PasswordHasher):
    """Argon2id paramétré selon la recommandation OWASP (Password Storage Cheat Sheet) :
    m = 46 Mio, t = 1, p = 1. Sécurité conforme, coût maîtrisé sur un petit serveur
    (une classe entière qui se connecte en même temps ne sature pas le processeur).
    Les hachages existants sont recalculés automatiquement à la connexion suivante."""

    algorithm = 'argon2'
    time_cost = 1
    memory_cost = 47104
    parallelism = 1
