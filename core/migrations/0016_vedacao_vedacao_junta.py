# Adiciona campo de vedação da junta (mesmas opções da vedação sede/tampa).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_valvula_observacao'),
    ]

    operations = [
        migrations.AddField(
            model_name='vedacao',
            name='vedacao_junta',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Vedação da Junta'),
        ),
    ]
