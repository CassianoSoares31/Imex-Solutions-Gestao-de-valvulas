from django.db import migrations


FLANGE_EXTRA = ["ASME B16.25", "ASME B36.10", "ASME B36.19", "ASME B16.11", "ASME B16.20"]


def seed(apps, schema_editor):
    OpcaoFlange = apps.get_model("core", "OpcaoFlange")
    inicio = OpcaoFlange.objects.count()
    for i, v in enumerate(FLANGE_EXTRA):
        OpcaoFlange.objects.get_or_create(valor=v, defaults={"ordem": inicio + i})


def unseed(apps, schema_editor):
    apps.get_model("core", "OpcaoFlange").objects.filter(valor__in=FLANGE_EXTRA).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0055_alter_valvula_frequencia_alter_valvula_tensao_and_more'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
