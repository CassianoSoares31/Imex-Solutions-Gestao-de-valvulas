#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Tb_Usuario

user = Tb_Usuario.objects.filter(email='joao@test.com').first()
if user:
    print(f"Token: {user.token_verificacao}")
    print(f"Confirmado: {user.confirmado}")
else:
    print("User not found")
