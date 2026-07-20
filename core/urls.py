from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="index"),
    path("auth/", views.auth_page, name="auth_page"),
    path("api/login/", views.login_api, name="login_api"),
    path("api/cadastro/", views.cadastro_api, name="cadastro_api"),
    path("logout/", views.logout_api, name="logout_api"),
    path("usuarios/", views.usuarios_page, name="usuarios_page"),
    path("estatisticas/", views.estatisticas_page, name="estatisticas_page"),
    path("api/estatisticas/", views.estatisticas_api, name="estatisticas_api"),
    path("api/debug/verification-tokens/", views.debug_verification_tokens, name="debug_verification_tokens"),
    path("api/usuarios/", views.usuario_lista_api, name="usuario_lista_api"),
    path("api/usuarios/<int:pk>/permissao/", views.usuario_alterar_permissao, name="usuario_alterar_permissao"),
    path("api/usuarios/<int:pk>/confirmar/", views.usuario_confirmar, name="usuario_confirmar"),
    # Password reset
    path("esqueci-senha/", views.esqueci_senha_page, name="esqueci_senha_page"),
    path("api/esqueci-senha/", views.esqueci_senha_api, name="esqueci_senha_api"),
    path("redefinir-senha/<uuid:token>/", views.redefinir_senha_form, name="redefinir_senha_form"),
    path("api/redefinir-senha/", views.redefinir_senha_api, name="redefinir_senha_api"),
    # API endpoints
    path("api/valvulas/", views.valvula_lista_api, name="valvula_lista_api"),
    path("api/dashboard-contadores/", views.dashboard_contadores_api, name="dashboard_contadores_api"),
    path('verificar-email/<uuid:token>/', views.verificar_email, name='verificar_email'),
    path("api/valvulas/<int:pk>/", views.valvula_detalhe_api, name="valvula_detalhe_api"),
    path("api/valvulas/criar/", views.valvula_criar, name="valvula_criar"),
    path("api/valvulas/preview/", views.valvula_preview, name="valvula_preview"),
    path("api/valvulas/<int:pk>/editar/", views.valvula_editar, name="valvula_editar"),
    path("api/valvulas/<int:pk>/excluir/", views.valvula_excluir, name="valvula_excluir"),
    path("api/valvulas/excluir-lote/", views.valvula_excluir_lote, name="valvula_excluir_lote"),
    path("api/valvulas/exportar-lote/", views.valvula_export_lote, name="valvula_export_lote"),
    path("api/valvulas/email/", views.valvula_email, name="valvula_email"),
    # Anexos
    path("api/valvulas/<int:pk>/anexos/", views.anexo_upload, name="anexo_upload"),
    path("api/anexos/<int:anexo_id>/download/", views.anexo_download, name="anexo_download"),
    path("api/anexos/<int:anexo_id>/excluir/", views.anexo_excluir, name="anexo_excluir"),
    path("projetos/", views.projetos_page, name="projetos_page"),
    path("api/projetos/", views.projeto_lista_api, name="projeto_lista_api"),
    path("api/projetos/criar/", views.projeto_criar, name="projeto_criar"),
    path("api/projetos/<int:pk>/status/", views.projeto_alterar_status, name="projeto_alterar_status"),
    path("api/projetos/<int:pk>/excluir/", views.projeto_excluir, name="projeto_excluir"),
    path("api/valvulas/atribuir-projeto/", views.valvula_atribuir_projeto, name="valvula_atribuir_projeto"),
    path("api/valvulas/desatribuir-projeto/", views.valvula_desatribuir_projeto, name="valvula_desatribuir_projeto"),
    path("api/opcoes-por-tipo/", views.opcoes_por_tipo, name="opcoes_por_tipo"),
    path("api/pesquisa-avancada/", views.pesquisa_avancada_api, name="pesquisa_avancada_api"),
    path("api/materiais-por-tipo/", views.materiais_por_tipo, name="materiais_por_tipo"),
    path("api/materiais/", views.material_lista_api, name="material_lista_api"),
    path("api/materiais/criar/", views.material_criar, name="material_criar"),
    # PDF
    path("valvulas/<int:pk>/pdf/", views.valvula_pdf, name="valvula_pdf"),
]

# .
