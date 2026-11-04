"""Configuration Django de BT COMPTA PRO.

Toutes les valeurs sensibles viennent des variables d'environnement (.env en local).
"""
from datetime import timedelta
from pathlib import Path
import os
import sys

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {'1', 'true', 'yes', 'on'}


def env_list(name: str, default: str = '') -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(',') if item.strip()]


DEBUG = env_bool('DEBUG', False)
SECRET_KEY = os.getenv('SECRET_KEY', '')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'dev-only-insecure-key-change-me'
    else:
        raise RuntimeError('SECRET_KEY doit être défini en production.')

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', 'localhost,127.0.0.1')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'core',
    'accounts',
    'pedagogy',
    'accounting',
    'calculations',
    'examinations',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.SecurityHeadersMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# --- Base de données : PostgreSQL par défaut, SQLite uniquement si DB_ENGINE=sqlite ---
if os.getenv('DB_ENGINE', 'postgresql').lower() == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'bt_compta_pro'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }
    if env_bool('DB_POOL', True):
        # Pool de connexions psycopg 3 : évite d'ouvrir une connexion PostgreSQL par requête
        # (coûteux, surtout sous Windows où chaque connexion crée un processus serveur).
        DATABASES['default']['OPTIONS'] = {'pool': {'min_size': 2, 'max_size': int(os.getenv('DB_POOL_MAX', '10'))}}
    else:
        DATABASES['default']['CONN_MAX_AGE'] = 60

AUTH_USER_MODEL = 'accounts.User'

# Argon2id (recommandé par l'OWASP) : résistant aux attaques par carte graphique.
# Les anciens hachages PBKDF2 sont convertis automatiquement à la connexion suivante.
PASSWORD_HASHERS = [
    'core.hashers.OwaspArgon2PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr'
TIME_ZONE = 'Africa/Bamako'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.getenv('THROTTLE_ANON', '120/minute'),
        'user': os.getenv('THROTTLE_USER', '1200/minute'),
        'login': os.getenv('THROTTLE_LOGIN', '10/minute'),
        'password_reset': os.getenv('THROTTLE_PASSWORD_RESET', '5/hour'),
        'calculations': os.getenv('THROTTLE_CALCULATIONS', '120/minute'),
        'exports': os.getenv('THROTTLE_EXPORTS', '30/minute'),
    },
    'EXCEPTION_HANDLER': 'core.exceptions.api_exception_handler',
    'COERCE_DECIMAL_TO_STRING': True,
}

SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('Bearer',),
    # Jeton d'accès court, conservé uniquement en mémoire côté navigateur.
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('JWT_ACCESS_MINUTES', '15'))),
    # Jeton de rafraîchissement : cookie HttpOnly, renouvelé à chaque usage, l'ancien est révoqué.
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('JWT_REFRESH_DAYS', '7'))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}

# Cookie du jeton de rafraîchissement : inaccessible au JavaScript (protection contre le vol par XSS),
# limité aux routes d'authentification et jamais envoyé depuis un autre site (SameSite=Strict).
REFRESH_COOKIE = {
    'key': 'btc_refresh',
    'path': '/api/auth/',
    'httponly': True,
    'secure': not DEBUG,
    'samesite': 'Strict',
}

# Verrouillage de compte contre la force brute (indépendant de l'adresse IP).
LOGIN_MAX_FAILURES = int(os.getenv('LOGIN_MAX_FAILURES', '5'))
LOGIN_LOCK_MINUTES = int(os.getenv('LOGIN_LOCK_MINUTES', '15'))

# Limites de taille des requêtes (protection contre les envois massifs).
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024

# Fichiers déposés (sujets et corrigés) : jamais servis publiquement, uniquement via l'API avec contrôle des droits.
MEDIA_ROOT = Path(os.getenv('MEDIA_ROOT', BASE_DIR / 'media'))
MAX_UPLOAD_MB = int(os.getenv('MAX_UPLOAD_MB', '10'))
FILE_UPLOAD_PERMISSIONS = 0o640
CALC_MAX_TABLE_ROWS = int(os.getenv('CALC_MAX_TABLE_ROWS', '300'))

# Réinitialisation du mot de passe par e-mail.
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173').rstrip('/')
PASSWORD_RESET_TIMEOUT = int(os.getenv('PASSWORD_RESET_TIMEOUT', str(60 * 60)))  # 1 heure
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'BT COMPTA PRO <no-reply@btcomptapro.ml>')
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend' if DEBUG
                          else 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)

# Adresse de l'administration Django : à personnaliser en production pour la rendre moins exposée.
ADMIN_URL = os.getenv('ADMIN_URL', 'admin/').strip('/') + '/'

CORS_ALLOWED_ORIGINS = env_list(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,capacitor://localhost,http://localhost',
)
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173')

# --- Sécurité production ---
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 60 * 60 * 8
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = env_bool('SECURE_HSTS_PRELOAD', True)

if 'test' in sys.argv:
    PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']  # tests plus rapides uniquement

LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {'format': '%(asctime)s %(levelname)s %(name)s: %(message)s'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'},
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'bt_compta_pro.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'simple',
            'encoding': 'utf-8',
        },
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'security.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'simple',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'btc.security': {'handlers': ['security_file', 'console'], 'level': 'INFO', 'propagate': False},
        'django.security': {'handlers': ['security_file', 'console'], 'level': 'WARNING', 'propagate': False},
    },
    'root': {'handlers': ['console', 'file'], 'level': os.getenv('LOG_LEVEL', 'INFO')},
}
