# Adiciona campo de observação (texto livre, até 1000 caracteres) à Válvula.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_add_qsl_to_valvula'),
    ]

    operations = [
        migrations.AddField(
            model_name='valvula',
            name='observacao',
            field=models.TextField(blank=True, default='', max_length=1000, verbose_name='Observação'),
        ),
    ]
