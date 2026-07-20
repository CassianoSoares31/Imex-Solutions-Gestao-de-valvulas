from config.settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
DEBUG = True
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# .
