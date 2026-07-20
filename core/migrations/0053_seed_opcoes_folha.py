from django.db import migrations


FLANGE = ["ASME B16.5", "ASME B16.47", "Norsok"]
PLACA = ["AISI 316", "AISI 304", "Alumínio"]


def seed(apps, schema_editor):
    OpcaoFlange = apps.get_model("core", "OpcaoFlange")
    OpcaoPlacaIdentificacao = apps.get_model("core", "OpcaoPlacaIdentificacao")
    for i, v in enumerate(FLANGE):
        OpcaoFlange.objects.get_or_create(valor=v, defaults={"ordem": i})
    for i, v in enumerate(PLACA):
        OpcaoPlacaIdentificacao.objects.get_or_create(valor=v, defaults={"ordem": i})


def unseed(apps, schema_editor):
    apps.get_model("core", "OpcaoFlange").objects.filter(valor__in=FLANGE).delete()
    apps.get_model("core", "OpcaoPlacaIdentificacao").objects.filter(valor__in=PLACA).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0052_opcaoflange_opcaoplacaidentificacao"),
    ]
    operations = [
        migrations.RunPython(seed, unseed),
    ]
