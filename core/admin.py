from django.contrib import admin
from core.models import Tb_Usuario, Material, OpcaoFlange, OpcaoPlacaIdentificacao


@admin.register(Tb_Usuario)
class Tb_UsuarioAdmin(admin.ModelAdmin):
    list_display = ['email', 'nome', 'nivel_permissao', 'confirmado']
    list_filter = ['nivel_permissao', 'confirmado']
    search_fields = ['email', 'nome']


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['nome']
    search_fields = ['nome']


class OpcaoSimplesAdmin(admin.ModelAdmin):
    """Admin compartilhado p/ listas de opção 'folha' (flange, placa, ...)."""
    list_display = ['valor', 'ordem', 'ativo']
    list_editable = ['ordem', 'ativo']
    search_fields = ['valor']


admin.site.register(OpcaoFlange, OpcaoSimplesAdmin)
admin.site.register(OpcaoPlacaIdentificacao, OpcaoSimplesAdmin)

# .
