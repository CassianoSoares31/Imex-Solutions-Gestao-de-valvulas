import json
import uuid
from datetime import timedelta
from unittest import skipIf
import sys

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone

SKIP_TEMPLATE = sys.version_info >= (3, 14)
SKIP_MSG = "Django 6.0 template context copy broken on Python 3.14+"

from .models import (
    Tb_Usuario, Material, Valvula, ValvulaMaterial,
    Vedacao, ComponentesInternos,
)
from .forms import ValvulaForm, MaterialForm, PesquisaForm


# ── Helpers ─────────────────────────────────────────────────────────────────

def make_user(email="user@test.com", nome="Teste", password="senha12345",
              confirmado=True, nivel="COMUM"):
    user = Tb_Usuario.objects.create_user(
        email=email, nome=nome, password=password,
        confirmado=confirmado, nivel_permissao=nivel,
    )
    return user


def make_especial(email="admin@test.com", nome="Admin", password="senha12345"):
    return make_user(email=email, nome=nome, password=password,
                     confirmado=True, nivel="ESPECIAL")


def make_material(nome="ASTM A216 WCB"):
    return Material.objects.get_or_create(nome=nome)[0]


def make_valvula(tipo="ESFERA", **kwargs):
    from core.views import gerar_codigo
    defaults = {
        "codigo": gerar_codigo(tipo),
        "tipo_valvula": tipo,
        "norma": "API 6D",
        "diametro": '2"',
        "classe": "150",
    }
    defaults.update(kwargs)
    return Valvula.objects.create(**defaults)


class EspecialMixin:
    """Loga como usuário ESPECIAL antes de cada teste (CRUD válvula protegido)."""
    def setUp(self):
        super().setUp()
        self.especial = make_especial()
        self.client.force_login(self.especial)


# ── Model Tests ─────────────────────────────────────────────────────────────

class UsuarioModelTest(TestCase):
    def test_create_user(self):
        u = make_user()
        self.assertEqual(u.email, "user@test.com")
        self.assertTrue(u.check_password("senha12345"))
        self.assertEqual(u.nivel_permissao, "COMUM")

    def test_create_superuser(self):
        u = Tb_Usuario.objects.create_superuser(
            email="super@test.com", nome="Super", password="senha12345"
        )
        self.assertEqual(u.nivel_permissao, "ESPECIAL")
        self.assertTrue(u.confirmado)

    def test_user_str(self):
        u = make_user()
        self.assertEqual(str(u), "user@test.com")

    def test_email_required(self):
        with self.assertRaises(ValueError):
            Tb_Usuario.objects.create_user(email="", nome="X", password="123")

    def test_token_verificacao_generated(self):
        u = make_user()
        self.assertIsNotNone(u.token_verificacao)


class MaterialModelTest(TestCase):
    def test_create_material(self):
        m = make_material("AISI 316")
        self.assertEqual(str(m), "AISI 316")

    def test_ordering(self):
        make_material("ZZZ")
        make_material("AAA")
        nomes = list(Material.objects.values_list("nome", flat=True))
        self.assertEqual(nomes, sorted(nomes))


class ValvulaModelTest(TestCase):
    def test_create_valvula(self):
        v = make_valvula()
        self.assertTrue(v.codigo.startswith("VES"))
        self.assertEqual(v.tipo_valvula, "ESFERA")

    def test_str(self):
        v = make_valvula()
        self.assertEqual(str(v), v.codigo)

    def test_get_tipo_display_extended(self):
        v = make_valvula(tipo="GAVETA")
        self.assertEqual(v.get_tipo_display_extended(), "Gaveta")

    def test_campos_por_tipo_keys(self):
        for tipo_key, _ in Valvula.TIPO_VALVULA:
            self.assertIn(tipo_key, Valvula.CAMPOS_POR_TIPO)
            self.assertIn(tipo_key, Valvula.MATERIAIS_POR_TIPO)


class ValvulaMaterialModelTest(TestCase):
    def test_unique_together(self):
        v = make_valvula()
        m = make_material()
        ValvulaMaterial.objects.create(valvula=v, material=m, tipo_material="CORPO_TAMPA")
        with self.assertRaises(Exception):
            ValvulaMaterial.objects.create(valvula=v, material=m, tipo_material="CORPO_TAMPA")

    def test_str(self):
        v = make_valvula()
        m = make_material("AISI 304")
        vm = ValvulaMaterial.objects.create(valvula=v, material=m, tipo_material="HASTE")
        self.assertIn("Haste", str(vm))
        self.assertIn("AISI 304", str(vm))


class VedacaoModelTest(TestCase):
    def test_create(self):
        v = make_valvula()
        ved = Vedacao.objects.create(valvula=v, vedacao_corpo_tampa="JUNTA ESPIRALADA")
        self.assertIn("JUNTA ESPIRALADA", str(ved))


class ComponentesInternosModelTest(TestCase):
    def test_create(self):
        v = make_valvula()
        c = ComponentesInternos.objects.create(valvula=v, inserto_rede="PEEK")
        self.assertIn("PEEK", str(c))


# ── Utility Function Tests ──────────────────────────────────────────────────

class ParseDiametroTest(TestCase):
    def test_simple(self):
        from core.views import _parse_diametro
        self.assertEqual(_parse_diametro('2"'), 2.0)

    def test_fraction(self):
        from core.views import _parse_diametro
        self.assertEqual(_parse_diametro('1/2"'), 0.5)

    def test_mixed(self):
        from core.views import _parse_diametro
        self.assertEqual(_parse_diametro('2 1/2"'), 2.5)


class GerarCodigoTest(TestCase):
    def test_first_code(self):
        from core.views import gerar_codigo
        code = gerar_codigo("ESFERA")
        self.assertEqual(code, "VES000001")

    def test_sequential(self):
        from core.views import gerar_codigo
        make_valvula(tipo="GAVETA")
        code = gerar_codigo("GAVETA")
        self.assertEqual(code, "VGA000002")

    def test_all_prefixes(self):
        from core.views import gerar_codigo, CODIGO_PREFIXO
        for tipo, prefixo in CODIGO_PREFIXO.items():
            code = gerar_codigo(tipo)
            self.assertTrue(code.startswith(prefixo))


# ── Auth View Tests ─────────────────────────────────────────────────────────

class AuthPageTest(TestCase):
    @skipIf(SKIP_TEMPLATE, SKIP_MSG)
    def test_auth_page_renders(self):
        resp = self.client.get(reverse("core:auth_page"))
        self.assertEqual(resp.status_code, 200)


class LoginAPITest(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_login_success(self):
        resp = self.client.post(
            reverse("core:login_api"),
            json.dumps({"email": "user@test.com", "password": "senha12345"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])

    def test_login_wrong_password(self):
        resp = self.client.post(
            reverse("core:login_api"),
            json.dumps({"email": "user@test.com", "password": "wrong"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 401)

    def test_login_empty_fields(self):
        resp = self.client.post(
            reverse("core:login_api"),
            json.dumps({"email": "", "password": ""}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_login_invalid_json(self):
        resp = self.client.post(
            reverse("core:login_api"),
            "not json",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_login_unconfirmed_user(self):
        make_user(email="pending@test.com", confirmado=False)
        resp = self.client.post(
            reverse("core:login_api"),
            json.dumps({"email": "pending@test.com", "password": "senha12345"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_get_not_allowed(self):
        resp = self.client.get(reverse("core:login_api"))
        self.assertEqual(resp.status_code, 405)


class CadastroAPITest(TestCase):
    def test_cadastro_success(self):
        resp = self.client.post(
            reverse("core:cadastro_api"),
            json.dumps({
                "nome": "Novo", "email": "novo@test.com",
                "password": "senha12345", "password_confirm": "senha12345",
            }),
            content_type="application/json",
        )
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertTrue(Tb_Usuario.objects.filter(email="novo@test.com").exists())

    def test_cadastro_password_mismatch(self):
        resp = self.client.post(
            reverse("core:cadastro_api"),
            json.dumps({
                "nome": "X", "email": "x@test.com",
                "password": "senha12345", "password_confirm": "other12345",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_cadastro_short_password(self):
        resp = self.client.post(
            reverse("core:cadastro_api"),
            json.dumps({
                "nome": "X", "email": "x@test.com",
                "password": "123", "password_confirm": "123",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("password", resp.json()["errors"])

    def test_cadastro_duplicate_confirmed_email(self):
        make_user(email="dup@test.com", confirmado=True)
        resp = self.client.post(
            reverse("core:cadastro_api"),
            json.dumps({
                "nome": "X", "email": "dup@test.com",
                "password": "senha12345", "password_confirm": "senha12345",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("email", resp.json()["errors"])

    def test_cadastro_resend_unconfirmed(self):
        make_user(email="resend@test.com", confirmado=False)
        resp = self.client.post(
            reverse("core:cadastro_api"),
            json.dumps({
                "nome": "Resent", "email": "resend@test.com",
                "password": "senha12345", "password_confirm": "senha12345",
            }),
            content_type="application/json",
        )
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertIn("reenviado", data["message"])

    def test_cadastro_missing_fields(self):
        resp = self.client.post(
            reverse("core:cadastro_api"),
            json.dumps({"nome": "", "email": "", "password": "", "password_confirm": ""}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)


class LogoutTest(TestCase):
    def test_logout_redirects(self):
        user = make_user()
        self.client.force_login(user)
        resp = self.client.get(reverse("core:logout_api"))
        self.assertEqual(resp.status_code, 302)


class VerificarEmailTest(TestCase):
    @skipIf(SKIP_TEMPLATE, SKIP_MSG)
    def test_verificar_email_success(self):
        user = make_user(confirmado=False)
        token = user.token_verificacao
        resp = self.client.get(reverse("core:verificar_email", args=[token]))
        self.assertEqual(resp.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.confirmado)

    @skipIf(SKIP_TEMPLATE, SKIP_MSG)
    def test_verificar_email_invalid_token(self):
        resp = self.client.get(reverse("core:verificar_email", args=[uuid.uuid4()]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "inválido")

    @skipIf(SKIP_TEMPLATE, SKIP_MSG)
    def test_verificar_email_already_confirmed(self):
        user = make_user(confirmado=True)
        token = user.token_verificacao
        resp = self.client.get(reverse("core:verificar_email", args=[token]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "já foi confirmada")


# ── Password Reset Tests ────────────────────────────────────────────────────

class EsqueciSenhaTest(TestCase):
    @skipIf(SKIP_TEMPLATE, SKIP_MSG)
    def test_page_renders(self):
        resp = self.client.get(reverse("core:esqueci_senha_page"))
        self.assertEqual(resp.status_code, 200)

    def test_api_existing_email(self):
        make_user(email="reset@test.com")
        resp = self.client.post(
            reverse("core:esqueci_senha_api"),
            json.dumps({"email": "reset@test.com"}),
            content_type="application/json",
        )
        self.assertTrue(resp.json()["success"])

    def test_api_nonexistent_email(self):
        resp = self.client.post(
            reverse("core:esqueci_senha_api"),
            json.dumps({"email": "nobody@test.com"}),
            content_type="application/json",
        )
        self.assertTrue(resp.json()["success"])

    def test_api_empty_email(self):
        resp = self.client.post(
            reverse("core:esqueci_senha_api"),
            json.dumps({"email": ""}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_rate_limit_3_per_day(self):
        user = make_user(email="limited@test.com")
        user.trocas_senha_hoje = 3
        user.ultima_data_troca = timezone.now().date()
        user.save()
        resp = self.client.post(
            reverse("core:esqueci_senha_api"),
            json.dumps({"email": "limited@test.com"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 429)


class RedefinirSenhaTest(TestCase):
    def setUp(self):
        self.user = make_user(email="redef@test.com")
        self.user.token_expiracao = timezone.now() + timedelta(minutes=30)
        self.user.save()

    @skipIf(SKIP_TEMPLATE, SKIP_MSG)
    def test_form_renders(self):
        resp = self.client.get(
            reverse("core:redefinir_senha_form", args=[self.user.token_verificacao])
        )
        self.assertEqual(resp.status_code, 200)

    @skipIf(SKIP_TEMPLATE, SKIP_MSG)
    def test_form_expired_token(self):
        self.user.token_expiracao = timezone.now() - timedelta(minutes=1)
        self.user.save()
        resp = self.client.get(
            reverse("core:redefinir_senha_form", args=[self.user.token_verificacao])
        )
        self.assertContains(resp, "expirado")

    def test_api_success(self):
        resp = self.client.post(
            reverse("core:redefinir_senha_api"),
            json.dumps({
                "token": str(self.user.token_verificacao),
                "nova_senha": "newpass12345",
                "nova_senha_confirm": "newpass12345",
            }),
            content_type="application/json",
        )
        self.assertTrue(resp.json()["success"])
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass12345"))

    def test_api_mismatch(self):
        resp = self.client.post(
            reverse("core:redefinir_senha_api"),
            json.dumps({
                "token": str(self.user.token_verificacao),
                "nova_senha": "newpass12345",
                "nova_senha_confirm": "different123",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_api_short_password(self):
        resp = self.client.post(
            reverse("core:redefinir_senha_api"),
            json.dumps({
                "token": str(self.user.token_verificacao),
                "nova_senha": "123",
                "nova_senha_confirm": "123",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_api_same_password(self):
        resp = self.client.post(
            reverse("core:redefinir_senha_api"),
            json.dumps({
                "token": str(self.user.token_verificacao),
                "nova_senha": "senha12345",
                "nova_senha_confirm": "senha12345",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("nova_senha", resp.json()["errors"])

    def test_api_expired_token(self):
        self.user.token_expiracao = timezone.now() - timedelta(minutes=1)
        self.user.save()
        resp = self.client.post(
            reverse("core:redefinir_senha_api"),
            json.dumps({
                "token": str(self.user.token_verificacao),
                "nova_senha": "newpass12345",
                "nova_senha_confirm": "newpass12345",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)


# ── Index / Protected Pages ─────────────────────────────────────────────────

class IndexViewTest(TestCase):
    def test_redirect_unauthenticated(self):
        resp = self.client.get(reverse("core:index"))
        self.assertEqual(resp.status_code, 302)

    @skipIf(SKIP_TEMPLATE, SKIP_MSG)
    def test_authenticated_renders(self):
        user = make_user()
        self.client.force_login(user)
        resp = self.client.get(reverse("core:index"))
        self.assertEqual(resp.status_code, 200)


class UsuariosPageTest(TestCase):
    def test_redirect_comum(self):
        user = make_user()
        self.client.force_login(user)
        resp = self.client.get(reverse("core:usuarios_page"))
        self.assertEqual(resp.status_code, 302)

    @skipIf(SKIP_TEMPLATE, SKIP_MSG)
    def test_especial_renders(self):
        admin = make_especial()
        self.client.force_login(admin)
        resp = self.client.get(reverse("core:usuarios_page"))
        self.assertEqual(resp.status_code, 200)


# ── Usuario API Tests ───────────────────────────────────────────────────────

class UsuarioListaAPITest(TestCase):
    def test_forbidden_for_comum(self):
        user = make_user()
        self.client.force_login(user)
        resp = self.client.get(reverse("core:usuario_lista_api"))
        self.assertEqual(resp.status_code, 403)

    def test_success_for_especial(self):
        admin = make_especial()
        self.client.force_login(admin)
        resp = self.client.get(reverse("core:usuario_lista_api"))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("usuarios", data)
        self.assertGreaterEqual(len(data["usuarios"]), 1)


class UsuarioAlterarPermissaoTest(TestCase):
    def setUp(self):
        self.admin = make_especial()
        self.target = make_user(email="target@test.com")

    def test_success(self):
        self.client.force_login(self.admin)
        resp = self.client.post(
            reverse("core:usuario_alterar_permissao", args=[self.target.pk]),
            json.dumps({"nivel_permissao": "ESPECIAL"}),
            content_type="application/json",
        )
        self.assertTrue(resp.json()["success"])
        self.target.refresh_from_db()
        self.assertEqual(self.target.nivel_permissao, "ESPECIAL")

    def test_cannot_change_self(self):
        self.client.force_login(self.admin)
        resp = self.client.post(
            reverse("core:usuario_alterar_permissao", args=[self.admin.pk]),
            json.dumps({"nivel_permissao": "COMUM"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_invalid_nivel(self):
        self.client.force_login(self.admin)
        resp = self.client.post(
            reverse("core:usuario_alterar_permissao", args=[self.target.pk]),
            json.dumps({"nivel_permissao": "INVALID"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)


class UsuarioConfirmarTest(TestCase):
    def test_toggle(self):
        admin = make_especial()
        target = make_user(email="t@test.com", confirmado=False)
        self.client.force_login(admin)
        resp = self.client.post(
            reverse("core:usuario_confirmar", args=[target.pk]),
        )
        self.assertTrue(resp.json()["confirmado"])
        resp = self.client.post(
            reverse("core:usuario_confirmar", args=[target.pk]),
        )
        self.assertFalse(resp.json()["confirmado"])


# ── Valvula API Tests ───────────────────────────────────────────────────────

class ValvulaListaAPITest(TestCase):
    def test_list(self):
        make_valvula()
        resp = self.client.get(reverse("core:valvula_lista_api"))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total"], 1)

    def test_filter_by_tipo(self):
        make_valvula(tipo="ESFERA")
        make_valvula(tipo="GAVETA")
        resp = self.client.get(reverse("core:valvula_lista_api") + "?tipo_valvula=ESFERA")
        self.assertEqual(resp.json()["total"], 1)

    def test_filter_by_codigo(self):
        v = make_valvula()
        resp = self.client.get(reverse("core:valvula_lista_api") + f"?codigo={v.codigo}")
        self.assertEqual(resp.json()["total"], 1)


class ValvulaDetalheAPITest(TestCase):
    def test_detail(self):
        v = make_valvula()
        m = make_material()
        ValvulaMaterial.objects.create(valvula=v, material=m, tipo_material="CORPO_TAMPA")
        Vedacao.objects.create(valvula=v, vedacao_corpo_tampa="JUNTA ESPIRALADA")
        resp = self.client.get(reverse("core:valvula_detalhe_api", args=[v.pk]))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["codigo"], v.codigo)
        self.assertEqual(len(data["materiais"]), 1)
        self.assertEqual(len(data["vedacoes"]), 1)
        self.assertIn("criado_por", data)
        self.assertIn("atualizado_em", data)
        self.assertTrue(data["atualizado_em"])

    @skipIf(SKIP_TEMPLATE, SKIP_MSG)
    def test_404(self):
        resp = self.client.get(reverse("core:valvula_detalhe_api", args=[99999]))
        self.assertEqual(resp.status_code, 404)


class ValvulaCriarTest(EspecialMixin, TestCase):
    def test_criar_esfera(self):
        make_material("ASTM A216 WCB")
        make_material("AISI 316")
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({
                "tipo_valvula": "ESFERA",
                "norma": "API 6D",
                "diametro": '2"',
                "classe": "150",
                "tipo_extremidade": "FLANGE RF",
                "tipo_ranhura": "125-250 μin ESPIRAL",
                "tipo_montagem": "FLUTUANTE",
                "tipo_passagem": "PLENA",
                "tipo_acionamento": "ALAVANCA",
                "construcao_corpo": "BI-PARTIDO",
                "materiais": [
                    {"tipo_material": "CORPO_TAMPA", "material": "ASTM A216 WCB"},
                    {"tipo_material": "HASTE", "material": "AISI 316"},
                ],
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["valvula"]["codigo"].startswith("VES"))

    def test_criar_missing_tipo(self):
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_criar_invalid_json(self):
        resp = self.client.post(
            reverse("core:valvula_criar"),
            "not json",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_criar_com_revestimento(self):
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({
                "tipo_valvula": "GAVETA",
                "norma": "API 600",
                "diametro": '2"',
                "classe": "150",
                "revestimento": "ZINCO NÍQUEL",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        pk = resp.json()["valvula"]["id"]
        v = Valvula.objects.get(pk=pk)
        self.assertEqual(v.revestimento, "ZINCO NÍQUEL")
        # detalhe API expõe revestimento
        det = self.client.get(reverse("core:valvula_detalhe_api", args=[pk]))
        self.assertEqual(det.json()["revestimento"], "ZINCO NÍQUEL")


class ValvulaEditarTest(EspecialMixin, TestCase):
    def test_editar(self):
        v = make_valvula()
        resp = self.client.post(
            reverse("core:valvula_editar", args=[v.pk]),
            json.dumps({
                "tipo_valvula": "ESFERA",
                "norma": "ISO 14313",
                "diametro": '4"',
                "classe": "300",
                "tipo_extremidade": "FLANGE RF",
                "tipo_montagem": "FLUTUANTE",
                "tipo_passagem": "PLENA",
                "tipo_acionamento": "ALAVANCA",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        v.refresh_from_db()
        self.assertEqual(v.norma, "ISO 14313")

    @skipIf(SKIP_TEMPLATE, SKIP_MSG)
    def test_editar_404(self):
        resp = self.client.post(
            reverse("core:valvula_editar", args=[99999]),
            json.dumps({"tipo_valvula": "ESFERA"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 404)


class AcionamentoManualHotDisconnectTest(EspecialMixin, TestCase):
    """Acionamento manual (Alavanca/Volante/Volante c/ Caixa de Redução) força
    hot_disconnect=False — o campo só faz sentido com atuador."""

    def _payload(self, acionamento, hot_disconnect):
        return {
            "tipo_valvula": "GAVETA", "funcao": "BLOQUEIO", "norma": "API 600",
            "diametro": '2"', "classe": "150",
            "tipo_acionamento": acionamento,
            "hot_disconnect": hot_disconnect,
        }

    def test_manual_forca_hot_disconnect_false(self):
        for acionamento in ("ALAVANCA", "VOLANTE", "VOLANTE COM ENGRENAGEM DE REDUÇÃO"):
            with self.subTest(acionamento=acionamento):
                resp = self.client.post(
                    reverse("core:valvula_criar"),
                    json.dumps(self._payload(acionamento, True)),
                    content_type="application/json",
                )
                self.assertEqual(resp.status_code, 200, resp.content)
                pk = resp.json()["valvula"]["id"]
                v = Valvula.objects.get(pk=pk)
                self.assertFalse(v.hot_disconnect)

    def test_atuador_preserva_hot_disconnect_true(self):
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps(self._payload("ATUADOR ELÉTRICO", True)),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        pk = resp.json()["valvula"]["id"]
        v = Valvula.objects.get(pk=pk)
        self.assertTrue(v.hot_disconnect)

    def test_editar_manual_limpa_hot_disconnect(self):
        v = make_valvula(tipo="GAVETA", hot_disconnect=True)
        resp = self.client.post(
            reverse("core:valvula_editar", args=[v.pk]),
            json.dumps(self._payload("ALAVANCA", True)),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        v.refresh_from_db()
        self.assertFalse(v.hot_disconnect)


class RateApi6dTest(TestCase):
    """_calc_rate_api6d: Rate A/D só existe pra Esfera (com/sem inserto macio),
    Rate G só pra Retenção sem inserto, Rate C pros demais tipos sem inserto,
    vazio quando a norma não define rate."""

    def _rate(self, valvula):
        from core.views import _calc_rate_api6d
        materiais = list(valvula.materiais.select_related("material"))
        componentes = list(valvula.componentes.all())
        return _calc_rate_api6d(valvula, materiais, componentes)

    def test_esfera_com_inserto_macio_rate_a(self):
        v = make_valvula(tipo="ESFERA", norma="API 6D")
        ComponentesInternos.objects.create(valvula=v, inserto_rede="PEEK")
        self.assertEqual(self._rate(v), "A")

    def test_esfera_com_inserto_n_a_rate_d(self):
        v = make_valvula(tipo="ESFERA", norma="API 6D")
        ComponentesInternos.objects.create(valvula=v, inserto_rede="N/A")
        self.assertEqual(self._rate(v), "D")

    def test_esfera_sem_componente_rate_d(self):
        v = make_valvula(tipo="ESFERA", norma="API 6D")
        self.assertEqual(self._rate(v), "D")

    def test_retencao_sem_inserto_rate_g(self):
        v = make_valvula(tipo="RETENCAO", norma="API 6D")
        self.assertEqual(self._rate(v), "G")

    def test_gaveta_sem_inserto_rate_c(self):
        v = make_valvula(tipo="GAVETA", norma="API 6D")
        self.assertEqual(self._rate(v), "C")

    def test_norma_sem_rate_vazio(self):
        v = make_valvula(tipo="ESFERA", norma="ISO 17292")
        self.assertEqual(self._rate(v), "")


class JuntaCategoriaVsMaterialTest(EspecialMixin, TestCase):
    """tipo_material "JUNTA" (Categoria Junta) e "MATERIAL_JUNTA" (Materiais da
    Junta) foram separados — antes viviam concatenados num único select. JUNTA só
    tem os 5 valores de categoria (Espiralada/RTJ/Pressure Seal/Castelo Soldado);
    MATERIAL_JUNTA tem a lista de composição (Grafite, PTFE, AISI+Grafite, ...)."""

    def test_materiais_por_tipo_junta_so_categoria(self):
        resp = self.client.get(reverse("core:materiais_por_tipo"),
                                {"tipo_valvula": "GAVETA", "tipo_material": "JUNTA"})
        self.assertEqual(resp.status_code, 200)
        valores = {m[0] for m in resp.json()["materiais"]}
        self.assertEqual(valores, {"JUNTA ESPIRALADA", "RTJ (FJA)", "PRESSURE SEAL", "CASTELO SOLDADO"})

    def test_materiais_por_tipo_material_junta_e_composicao(self):
        resp = self.client.get(reverse("core:materiais_por_tipo"),
                                {"tipo_valvula": "GAVETA", "tipo_material": "MATERIAL_JUNTA"})
        self.assertEqual(resp.status_code, 200)
        valores = {m[0] for m in resp.json()["materiais"]}
        self.assertIn("GRAFITE", valores)
        self.assertIn("PTFE", valores)
        self.assertIn("N/A", valores)
        self.assertNotIn("CASTELO SOLDADO", valores)
        self.assertNotIn("JUNTA ESPIRALADA", valores)

    def test_cria_valvula_com_categoria_e_material_separados(self):
        make_material("ASTM A105")
        make_material("CASTELO SOLDADO")
        make_material("GRAFITE")
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({
                "tipo_valvula": "GAVETA", "funcao": "BLOQUEIO", "norma": "API 600",
                "diametro": '2"', "classe": "150",
                "materiais": [
                    {"tipo_material": "CORPO_TAMPA", "material": "ASTM A105"},
                    {"tipo_material": "JUNTA", "material": "CASTELO SOLDADO"},
                    {"tipo_material": "MATERIAL_JUNTA", "material": "GRAFITE"},
                ],
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertEqual(v.materiais.get(tipo_material="JUNTA").material.nome, "CASTELO SOLDADO")
        self.assertEqual(v.materiais.get(tipo_material="MATERIAL_JUNTA").material.nome, "GRAFITE")


class FolhaJuntaLinhaCombinadaTest(TestCase):
    """PDF/preview: Categoria Junta (JUNTA) + Materiais da Junta (MATERIAL_JUNTA)
    aparecem numa única linha "Material/Categoria da Junta", valor combinado."""

    def _corpo(self, materiais):
        from core.views import _build_folha_grupos, _folha_labels_bi
        v = make_valvula(tipo="GAVETA")
        L = _folha_labels_bi()
        grupos = _build_folha_grupos(v, materiais, [], [], "", L)
        return dict(grupos[0][1])  # grupo "Corpo e Internos"

    def test_categoria_e_material_juntos_na_mesma_linha(self):
        v = make_valvula(tipo="GAVETA")
        mats = [
            ValvulaMaterial(valvula=v, tipo_material="JUNTA", material=Material(nome="CASTELO SOLDADO")),
            ValvulaMaterial(valvula=v, tipo_material="MATERIAL_JUNTA", material=Material(nome="GRAFITE")),
        ]
        corpo = self._corpo(mats)
        rotulo = [k for k in corpo if "Junta" in k][0]
        self.assertIn("Material/Categoria da Junta", rotulo)
        self.assertIn("GRAFITE", corpo[rotulo])
        self.assertIn("CASTELO SOLDADO", corpo[rotulo])
        # Material (composição) vem antes da Categoria no valor combinado
        self.assertLess(corpo[rotulo].index("GRAFITE"), corpo[rotulo].index("CASTELO SOLDADO"))

    def test_so_categoria_aparece_sozinha(self):
        v = make_valvula(tipo="GAVETA")
        mats = [ValvulaMaterial(valvula=v, tipo_material="JUNTA", material=Material(nome="CASTELO SOLDADO"))]
        corpo = self._corpo(mats)
        rotulo = [k for k in corpo if "Junta" in k][0]
        self.assertIn("CASTELO SOLDADO", corpo[rotulo])

    def test_nenhum_valor_sem_linha(self):
        corpo = self._corpo([])
        self.assertFalse([k for k in corpo if "Junta" in k])


class CodigoUniversalJuntaLLTest(TestCase):
    """Parte LL do código universal prioriza MATERIAL_JUNTA (composição) e cai para
    JUNTA (categoria) quando só a categoria foi informada (ex.: Castelo Soldado,
    que não tem material de composição próprio)."""

    def _ll(self, valvula, materiais):
        from core.views import _codigo_universal_l
        return _codigo_universal_l(valvula, materiais)

    def test_prioriza_material_junta_sobre_categoria(self):
        v = make_valvula(tipo="GAVETA")
        mats = [
            ValvulaMaterial(valvula=v, tipo_material="JUNTA", material=Material(nome="CASTELO SOLDADO")),
            ValvulaMaterial(valvula=v, tipo_material="MATERIAL_JUNTA", material=Material(nome="GRAFITE")),
        ]
        self.assertEqual(self._ll(v, mats), "GG")

    def test_fallback_categoria_sem_material_junta(self):
        v = make_valvula(tipo="GAVETA")
        mats = [ValvulaMaterial(valvula=v, tipo_material="JUNTA", material=Material(nome="CASTELO SOLDADO"))]
        self.assertEqual(self._ll(v, mats), "CS")


class FlangeConexaoTest(EspecialMixin, TestCase):
    """Campo "Flange" (norma de conexão) derivado do tipo_extremidade: Butt-Welding
    → ASME B16.25; Socket-Welding → ASME B16.11; Rosca NPT → ASME B16.20; Niple →
    B36.10 (corpo carbono) ou B36.19 (corpo inox). Flange/RF continua livre."""

    def _post(self, extremidade, diametro='2"', corpo="ASTM A105", flange_input=""):
        make_material(corpo)
        payload = {
            "tipo_valvula": "ESFERA", "funcao": "BLOQUEIO", "nbr": False,
            "diametro": diametro, "tipo_montagem": "TRUNNION", "classe": "150",
            "tipo_extremidade": extremidade, "flange": flange_input,
            "materiais": [{"tipo_material": "CORPO_TAMPA", "material": corpo}],
        }
        return self.client.post(reverse("core:valvula_criar"), json.dumps(payload),
                                content_type="application/json")

    def test_butt_welding_forca_b1625(self):
        resp = self._post("BUTT-WELDING 40")
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertEqual(v.flange, "ASME B16.25")

    def test_socket_welding_forca_b1611(self):
        resp = self._post("SOCKET-WELDING")
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertEqual(v.flange, "ASME B16.11")

    def test_rosca_npt_forca_b1620(self):
        resp = self._post("ROSCA NPT")
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertEqual(v.flange, "ASME B16.20")

    def test_niple_corpo_carbono_forca_b3610(self):
        resp = self._post('NIPLE 4" COMP. SCH 80', corpo="ASTM A105")
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertEqual(v.flange, "ASME B36.10")

    def test_niple_corpo_inox_forca_b3619(self):
        resp = self._post('NIPLE 4" COMP. SCH 80', corpo="ASTM A182 F316")
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertEqual(v.flange, "ASME B36.19")

    def test_flange_rf_nao_forca_mantem_valor_usuario(self):
        resp = self._post("FLANGE RF", flange_input="ASME B16.5")
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertEqual(v.flange, "ASME B16.5")


class RateIso14313Test(TestCase):
    """ISO 14313 (11.4.3 + Anexo B.3.1) cita ISO 5208 direto, mas só distingue
    macio(A)/metálico(D) por sede — sem tabela por tipo como a API 6D (sem
    Rate C nem G). Só Esfera/Retenção têm campo de inserto de sede no modelo;
    demais tipos ficam sem rate."""

    def _rate(self, valvula):
        from core.views import _calc_rate_api6d
        materiais = list(valvula.materiais.select_related("material"))
        componentes = list(valvula.componentes.all())
        return _calc_rate_api6d(valvula, materiais, componentes)

    def test_esfera_com_inserto_macio_rate_a(self):
        v = make_valvula(tipo="ESFERA", norma="ISO 14313")
        ComponentesInternos.objects.create(valvula=v, inserto_rede="PTFE")
        self.assertEqual(self._rate(v), "A")

    def test_esfera_sem_inserto_rate_d(self):
        v = make_valvula(tipo="ESFERA", norma="ISO 14313")
        self.assertEqual(self._rate(v), "D")

    def test_retencao_com_inserto_rate_a(self):
        v = make_valvula(tipo="RETENCAO", norma="ISO 14313")
        ComponentesInternos.objects.create(valvula=v, inserto_rede="DEVLON")
        self.assertEqual(self._rate(v), "A")

    def test_retencao_sem_inserto_rate_d_nao_g(self):
        """Diferente da API 6D: ISO 14313 não tem Rate G — Retenção metálica é D."""
        v = make_valvula(tipo="RETENCAO", norma="ISO 14313")
        self.assertEqual(self._rate(v), "D")

    def test_gaveta_sem_campo_inserto_vazio(self):
        """Gaveta não tem campo de inserto de sede no modelo — indeterminável."""
        v = make_valvula(tipo="GAVETA", norma="ISO 14313")
        self.assertEqual(self._rate(v), "")


class RateBs1868Test(TestCase):
    """BS 1868 (decisão de negócio 2026-07-21): rate limitado a A/C, sem G — só
    Retenção oferece a norma, então só esse tipo é exercitado na prática."""

    def _rate(self, valvula):
        from core.views import _calc_rate_api6d
        materiais = list(valvula.materiais.select_related("material"))
        componentes = list(valvula.componentes.all())
        return _calc_rate_api6d(valvula, materiais, componentes)

    def test_retencao_com_inserto_macio_rate_a(self):
        v = make_valvula(tipo="RETENCAO", norma="BS 1868")
        ComponentesInternos.objects.create(valvula=v, inserto_rede="PEEK")
        self.assertEqual(self._rate(v), "A")

    def test_retencao_sem_inserto_rate_c_nao_g(self):
        v = make_valvula(tipo="RETENCAO", norma="BS 1868")
        self.assertEqual(self._rate(v), "C")


class Bs1868RateNaFolhaTest(TestCase):
    """Rate A/C do BS 1868 tem que aparecer na FD (PDF/Excel/preview), não só no
    cálculo isolado — checa a linha "Critério de Aceitação" em _build_folha_grupos,
    mesma fonte usada por valvula_pdf/valvula_preview/valvula_export_lote."""

    def _criterio(self, componentes):
        from core.views import _build_folha_grupos, _folha_labels_bi, _calc_rate_api6d
        v = make_valvula(tipo="RETENCAO", norma="BS 1868")
        L = _folha_labels_bi()
        rate = _calc_rate_api6d(v, [], componentes)
        grupos = _build_folha_grupos(v, [], [], componentes, rate, L)
        corpo = dict(grupos[0][1])  # grupo "Corpo e Internos"
        return corpo[L["lbl_acceptance_criteria"]]

    def test_rate_a_aparece_com_inserto_macio(self):
        comp = [ComponentesInternos(inserto_rede="PEEK")]
        self.assertEqual(self._criterio(comp), "ISO 5208 — Rate A")

    def test_rate_c_aparece_sem_inserto(self):
        self.assertEqual(self._criterio([]), "ISO 5208 — Rate C")


class ValvulaExcluirTest(EspecialMixin, TestCase):
    def test_excluir(self):
        v = make_valvula()
        pk = v.pk
        resp = self.client.post(reverse("core:valvula_excluir", args=[pk]))
        self.assertTrue(resp.json()["success"])
        self.assertFalse(Valvula.objects.filter(pk=pk).exists())


class CrudPermissaoTest(TestCase):
    """Usuário COMUM PODE criar válvula, mas NÃO pode editar/excluir (403).
    (Criar é liberado a qualquer autenticado; editar/excluir são especial_required.)"""
    def setUp(self):
        self.comum = make_user(email="comum@test.com", nivel="COMUM")
        self.client.force_login(self.comum)

    def test_criar_allowed(self):
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({"tipo_valvula": "ESFERA"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertTrue(resp.json()["success"])

    def test_editar_forbidden(self):
        v = make_valvula()
        resp = self.client.post(
            reverse("core:valvula_editar", args=[v.pk]),
            json.dumps({"tipo_valvula": "ESFERA"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 403)
        v.refresh_from_db()
        self.assertEqual(v.norma, "API 6D")

    def test_excluir_forbidden(self):
        v = make_valvula()
        resp = self.client.post(reverse("core:valvula_excluir", args=[v.pk]))
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(Valvula.objects.filter(pk=v.pk).exists())

    def test_anonymous_forbidden(self):
        self.client.logout()
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({"tipo_valvula": "ESFERA"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 403)


# ── Business Rules Tests ────────────────────────────────────────────────────

class NbrGavetaGaxetaRuleTest(EspecialMixin, TestCase):
    def test_gaveta_nbr_wrong_gaxeta_rejected(self):
        make_material("GRAFITE")
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({
                "tipo_valvula": "GAVETA",
                "nbr": True,
                "norma": "API 600",
                "diametro": '2"',
                "classe": "150",
                "materiais": [
                    {"tipo_material": "GAXETA", "material": "GRAFITE"},
                ],
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("materiais", resp.json()["errors"])


class NbrEsferaHasteRuleTest(EspecialMixin, TestCase):
    def test_esfera_nbr_haste_differs_from_obturador(self):
        make_material("AISI 304")
        make_material("AISI 316")
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({
                "tipo_valvula": "ESFERA",
                "nbr": True,
                "norma": "API 6D",
                "diametro": '2"',
                "classe": "150",
                "materiais": [
                    {"tipo_material": "OBTURADOR", "material": "AISI 304"},
                    {"tipo_material": "HASTE", "material": "AISI 316"},
                ],
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("materiais", resp.json()["errors"])

    def test_esfera_nbr_haste_igual_obturador_aceito(self):
        """AISI 410 (forma curta) igual em obturador e haste → regra passa."""
        make_material("AISI 410")
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({
                "tipo_valvula": "ESFERA",
                "nbr": True,
                "norma": "API 6D",
                "diametro": '2"',
                "classe": "150",
                "tipo_montagem": "FLUTUANTE",
                "dispositivo_antiestatico": True,
                "materiais": [
                    {"tipo_material": "OBTURADOR", "material": "AISI 410"},
                    {"tipo_material": "HASTE", "material": "AISI 410"},
                ],
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])

    def test_obturador_esfera_usa_forma_curta(self):
        """Opções de obturador esfera batem com haste (sem refs ASTM longas)."""
        obturador = dict(Valvula.MATERIAIS_OBTURADOR_ESFERA)
        haste = dict(Valvula.MATERIAIS_HASTE)
        for nome in ["AISI 410", "STELLITE 6", "MONEL 400", "MONEL K500"]:
            self.assertIn(nome, obturador, f"{nome} ausente no obturador")
            self.assertIn(nome, haste, f"{nome} ausente na haste")


class EsferaDiametroDibRuleTest(EspecialMixin, TestCase):
    """Esfera + diâmetro ≤2" → Construção da Sede (DIB) trava em DBB, independe
    de NBR (diâmetro pequeno não comporta DIB-1/DIB-2)."""

    def _post(self, diametro, dib):
        payload = {
            "tipo_valvula": "ESFERA", "funcao": "BLOQUEIO", "nbr": False,
            "diametro": diametro, "classe": "150", "dib": dib,
            "tipo_montagem": "FLUTUANTE", "dispositivo_antiestatico": True,
        }
        return self.client.post(
            reverse("core:valvula_criar"), json.dumps(payload),
            content_type="application/json",
        )

    def test_diametro_1_forca_dbb(self):
        resp = self._post('1"', "DIB-2")
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertEqual(v.dib, "DBB")

    def test_diametro_2_forca_dbb(self):
        resp = self._post('2"', "DIB-1")
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertEqual(v.dib, "DBB")

    def test_diametro_2_5_mantem_dib(self):
        resp = self._post('2 1/2"', "DIB-1")
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertEqual(v.dib, "DIB-1")


class NbrEsferaTrunnionDib1AlivioRuleTest(EspecialMixin, TestCase):
    def test_trunnion_nbr_dib1_requires_alivio(self):
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({
                "tipo_valvula": "ESFERA",
                "nbr": True,
                "norma": "API 6D",
                "diametro": '8"',
                "classe": "150",
                "tipo_montagem": "TRUNNION",
                "dib": "DIB-1",
                "valvula_alivio": False,
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("valvula_alivio", resp.json()["errors"])


class EsferaSocketClasse800RuleTest(EspecialMixin, TestCase):
    """Esfera + NBR + Socket-Welding + classe 800 → norma deve ser ISO 17292
    e essa regra tem prioridade sobre a regra de extremidade Niple."""

    def _payload(self, norma):
        return {
            "tipo_valvula": "ESFERA",
            "nbr": True,
            "norma": norma,
            "diametro": '1"',  # Socket-Welding exige diâmetro 1/2"-1.5" (small-bore)
            "classe": "800",
            "tipo_extremidade": "SOCKET-WELDING",
            "tipo_montagem": "FLUTUANTE",  # diâmetro pequeno + classe 600/800/900 → Flutuante
            "dispositivo_antiestatico": True,
            "materiais": [
                {"tipo_material": "CORPO_TAMPA", "material": "ASTM A105"},
            ],
        }

    def test_norma_errada_rejeitada(self):
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps(self._payload("API 6D")),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("norma", resp.json()["errors"])

    def test_norma_iso17292_aceita_e_tem_prioridade(self):
        """Corpo ASTM A105 (carbono) forçaria Niple SCH 160, mas Socket+800+ISO17292
        tem prioridade → aceito mesmo com Socket-Welding."""
        make_material("ASTM A105")
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps(self._payload("ISO 17292")),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertTrue(resp.json()["success"])
        pk = resp.json()["valvula"]["id"]
        v = Valvula.objects.get(pk=pk)
        self.assertEqual(v.tipo_extremidade, "SOCKET-WELDING")
        self.assertEqual(v.norma, "ISO 17292")


class EsferaNbrAntiestaticoRuleTest(EspecialMixin, TestCase):
    """Esfera + NBR 15827 → dispositivo antiestático obrigatório."""

    def test_sem_antiestatico_rejeitado(self):
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({
                "tipo_valvula": "ESFERA", "nbr": True, "norma": "API 6D",
                "diametro": '2"', "classe": "150", "tipo_montagem": "FLUTUANTE",
                "dispositivo_antiestatico": False,
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("dispositivo_antiestatico", resp.json()["errors"])

    def test_com_antiestatico_aceito(self):
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({
                "tipo_valvula": "ESFERA", "nbr": True, "norma": "API 6D",
                "diametro": '2"', "classe": "150", "tipo_montagem": "FLUTUANTE",
                "dispositivo_antiestatico": True,
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertTrue(v.dispositivo_antiestatico)

    def test_esfera_sem_nbr_antiestatico_opcional(self):
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({
                "tipo_valvula": "ESFERA", "nbr": False, "norma": "API 6D",
                "diametro": '2"', "classe": "150", "tipo_montagem": "FLUTUANTE",
                "dispositivo_antiestatico": False,
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)


class EsferaNormaB1634RuleTest(EspecialMixin, TestCase):
    """Esfera + NBR + classe 1500/2500 + Socket-Welding → norma ASME B16.34 (prioritária)."""

    def test_classe_1500_socket_norma_errada_rejeitada(self):
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({
                "tipo_valvula": "ESFERA", "nbr": True, "norma": "API 6D",
                "diametro": '2"', "classe": "1500", "tipo_montagem": "TRUNNION",
                "tipo_extremidade": "SOCKET-WELDING", "dispositivo_antiestatico": True,
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("norma", resp.json()["errors"])

    def test_classe_2500_socket_norma_b1634_aceita(self):
        """B16.34 + socket tem prioridade sobre regra Niple (corpo inox → XXS)."""
        make_material("ASTM A182 F316")
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({
                "tipo_valvula": "ESFERA", "nbr": True, "norma": "ASME B16.34",
                "diametro": '1"', "classe": "2500", "tipo_montagem": "TRUNNION",  # Socket exige 1/2"-1.5"
                "tipo_extremidade": "SOCKET-WELDING", "dispositivo_antiestatico": True,
                "materiais": [{"tipo_material": "CORPO_TAMPA", "material": "ASTM A182 F316"}],
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertEqual(v.norma, "ASME B16.34")
        self.assertEqual(v.tipo_extremidade, "SOCKET-WELDING")

    def test_classe_1500_sem_socket_regra_nao_aplica(self):
        """Sem Socket-Welding a regra B16.34 não se aplica (norma livre)."""
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({
                "tipo_valvula": "ESFERA", "nbr": True, "norma": "API 6D",
                "diametro": '2"', "classe": "1500", "tipo_montagem": "TRUNNION",
                "tipo_extremidade": "FLANGE RF", "dispositivo_antiestatico": True,
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)


class EsferaMontagemlDiametroRuleTest(EspecialMixin, TestCase):
    def test_diametro_gte_6_must_be_trunnion(self):
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({
                "tipo_valvula": "ESFERA",
                "norma": "API 6D",
                "diametro": '8"',
                "classe": "150",
                "tipo_montagem": "FLUTUANTE",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_montagem", resp.json()["errors"])


class DuplicataTest(EspecialMixin, TestCase):
    def test_duplicate_valvula_rejected(self):
        payload = {
            "tipo_valvula": "GAVETA",
            "norma": "API 600",
            "diametro": '2"',
            "classe": "150",
            "tipo_extremidade": "FLANGE RF",
            "tipo_ranhura": "LISO (125 μin)",
            "tipo_passagem": "PLENA",
            "tipo_acionamento": "VOLANTE",
            "tipo_castelo": "NORMAL",
            "juncao_corpo_castelo": "APARAFUSADO",
            "uso_geral": "USO GERAL",
            "certificacao_sil": "SIL 1",
            "nace": "N/A",
            "revestimento": "N/A",
        }
        resp1 = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp1.status_code, 200)
        resp2 = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp2.status_code, 409)
        self.assertTrue(resp2.json().get("duplicata"))

    def test_dup_check_nullable_fields_bug(self):
        """Documenta bug: campos nullable CharField visíveis salvam None,
        mas filtro dup compara com '' → duplicata não detectada."""
        payload = {
            "tipo_valvula": "GAVETA",
            "norma": "API 600",
            "diametro": '2"',
            "classe": "150",
        }
        self.client.post(
            reverse("core:valvula_criar"),
            json.dumps(payload),
            content_type="application/json",
        )
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps(payload),
            content_type="application/json",
        )
        # BUG: deveria ser 409, mas nullable CharField None vs "" no filtro
        self.assertEqual(resp.status_code, 200)


# ── Opcoes / Materiais API Tests ────────────────────────────────────────────

class OpcoesPorTipoTest(TestCase):
    def test_esfera(self):
        resp = self.client.get(reverse("core:opcoes_por_tipo") + "?tipo=ESFERA")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("normas", data)
        self.assertIn("campos_visiveis", data)
        self.assertTrue(len(data["normas"]) > 0)

    def test_all_types(self):
        for tipo, _ in Valvula.TIPO_VALVULA:
            resp = self.client.get(reverse("core:opcoes_por_tipo") + f"?tipo={tipo}")
            self.assertEqual(resp.status_code, 200, f"Failed for {tipo}")

    def test_revestimento_em_todos_tipos(self):
        """Revestimento deve aparecer nas opções e nos campos visíveis de todo tipo."""
        for tipo, _ in Valvula.TIPO_VALVULA:
            resp = self.client.get(reverse("core:opcoes_por_tipo") + f"?tipo={tipo}")
            data = resp.json()
            self.assertIn("revestimento", data, f"sem opcoes revestimento em {tipo}")
            self.assertEqual(len(data["revestimento"]), 3, f"revestimento incompleto em {tipo}")
            self.assertIn("revestimento", data["campos_visiveis"], f"revestimento nao visivel em {tipo}")

    def test_missing_tipo(self):
        resp = self.client.get(reverse("core:opcoes_por_tipo"))
        self.assertEqual(resp.status_code, 400)


class Api607UsoGeralEscopoTest(TestCase):
    """API 607 (Seção 1) cobre válvulas quarter-turn (Esfera/Borboleta) ou com sede
    não-metálica. Gaveta/Globo/Globo Controle não são quarter-turn e não têm campo de
    sede/inserto não-metálico -> uso_geral não deve oferecer API 607 para esses tipos."""

    def _uso_geral(self, tipo):
        resp = self.client.get(reverse("core:opcoes_por_tipo") + f"?tipo={tipo}")
        return [v for v, _ in resp.json()["uso_geral"]]

    def test_ausente_em_gaveta_globo_globo_controle(self):
        for tipo in ("GAVETA", "GLOBO", "GLOBO_CONTROLE"):
            self.assertNotIn("API 607", self._uso_geral(tipo), f"API 607 nao deveria aparecer em {tipo}")

    def test_presente_em_esfera_borboleta(self):
        for tipo in ("ESFERA", "BORBOLETA"):
            self.assertIn("API 607", self._uso_geral(tipo), f"API 607 deveria aparecer em {tipo}")


class MateriaisPorTipoTest(TestCase):
    def test_esfera_corpo(self):
        resp = self.client.get(
            reverse("core:materiais_por_tipo") + "?tipo_valvula=ESFERA&tipo_material=CORPO_TAMPA"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.json()["materiais"]) > 0)

    def test_missing_params(self):
        resp = self.client.get(reverse("core:materiais_por_tipo"))
        self.assertEqual(resp.status_code, 400)


class PesquisaAvancadaTest(TestCase):
    def test_filter_by_tipo(self):
        make_valvula(tipo="ESFERA")
        make_valvula(tipo="GAVETA")
        resp = self.client.get(
            reverse("core:pesquisa_avancada_api") + "?tipo_valvula=ESFERA"
        )
        self.assertEqual(resp.json()["total"], 1)

    def test_filter_by_codigo(self):
        v = make_valvula()
        resp = self.client.get(
            reverse("core:pesquisa_avancada_api") + f"?codigo={v.codigo}"
        )
        self.assertEqual(resp.json()["total"], 1)

    def test_filter_by_bool(self):
        make_valvula(nbr=True)
        make_valvula(nbr=False)
        resp = self.client.get(
            reverse("core:pesquisa_avancada_api") + "?nbr=true"
        )
        self.assertEqual(resp.json()["total"], 1)

    def test_empty_returns_all(self):
        make_valvula()
        make_valvula(tipo="GAVETA")
        resp = self.client.get(reverse("core:pesquisa_avancada_api"))
        self.assertEqual(resp.json()["total"], 2)


# ── Material API Tests ──────────────────────────────────────────────────────

class MaterialListaAPITest(TestCase):
    def test_list(self):
        make_material("AAA")
        make_material("BBB")
        resp = self.client.get(reverse("core:material_lista_api"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["materiais"]), 2)


class MaterialCriarTest(TestCase):
    def test_criar(self):
        resp = self.client.post(
            reverse("core:material_criar"),
            json.dumps({"nome": "Novo Material"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])

    def test_criar_invalid_json(self):
        resp = self.client.post(
            reverse("core:material_criar"),
            "bad",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)


# ── Form Tests ──────────────────────────────────────────────────────────────

class ValvulaFormTest(TestCase):
    def test_valid_minimal(self):
        form = ValvulaForm(data={
            "tipo_valvula": "ESFERA",
            "norma": "API 6D",
            "diametro": '2"',
            "classe": "150",
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_tipo(self):
        form = ValvulaForm(data={"norma": "API 6D"})
        self.assertFalse(form.is_valid())


class MaterialFormTest(TestCase):
    def test_valid(self):
        form = MaterialForm(data={"nome": "Test Material"})
        self.assertTrue(form.is_valid())

    def test_empty(self):
        form = MaterialForm(data={"nome": ""})
        self.assertFalse(form.is_valid())


class PesquisaFormTest(TestCase):
    def test_valid_empty(self):
        form = PesquisaForm(data={"codigo": "", "tipo_valvula": ""})
        self.assertTrue(form.is_valid())

    def test_with_tipo(self):
        form = PesquisaForm(data={"codigo": "", "tipo_valvula": "ESFERA"})
        self.assertTrue(form.is_valid())


# ── Debug Endpoint ──────────────────────────────────────────────────────────

class DebugVerificationTokensTest(TestCase):
    @override_settings(DEBUG=True)
    def test_debug_mode(self):
        make_user(confirmado=False)
        resp = self.client.get(reverse("core:debug_verification_tokens"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("usuarios_pendentes", resp.json())

    @override_settings(DEBUG=False)
    def test_production_forbidden(self):
        resp = self.client.get(reverse("core:debug_verification_tokens"))
        self.assertEqual(resp.status_code, 403)


# ── Acabamento da face do flange (tipo_ranhura) só existe em conexão Flange/Wafer/Lug ──

class RanhuraNaForaDeFlangeRuleTest(EspecialMixin, TestCase):
    """tipo_ranhura ("Acabamento da Face do Flange") só faz sentido em conexão
    Flange/Wafer/Lug — qualquer outra conexão (Butt-Welding, Socket-Welding,
    Rosca, Niple, Gray Loc Hub) força N/A, independente de NBR."""

    def _payload(self, tipo_extremidade, tipo_ranhura, diametro='2"'):
        return {
            "tipo_valvula": "GAVETA", "funcao": "BLOQUEIO", "nbr": False,
            "diametro": diametro, "classe": "150",
            "tipo_extremidade": tipo_extremidade, "tipo_ranhura": tipo_ranhura,
            "tipo_passagem": "PLENA", "tipo_acionamento": "VOLANTE",
            "tipo_castelo": "NORMAL", "juncao_corpo_castelo": "APARAFUSADO",
        }

    def _post(self, payload):
        return self.client.post(
            reverse("core:valvula_criar"), json.dumps(payload),
            content_type="application/json",
        )

    def test_socket_welding_forca_na(self):
        resp = self._post(self._payload("SOCKET-WELDING", "LISO (125 μin)", diametro='1"'))
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertEqual(v.tipo_ranhura, "N/A")

    def test_butt_welding_com_schedule_forca_na(self):
        resp = self._post(self._payload("BUTT-WELDING 40", "LISO (125 μin)"))
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertEqual(v.tipo_ranhura, "N/A")

    def test_flange_mantem_ranhura(self):
        resp = self._post(self._payload("FLANGE RF", "LISO (125 μin)"))
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertEqual(v.tipo_ranhura, "LISO (125 μin)")

    def test_wafer_mantem_ranhura(self):
        resp = self._post(self._payload("Wafer", "LISO (125 μin)"))
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertEqual(v.tipo_ranhura, "LISO (125 μin)")

    def test_globo_controle_butt_welding_sem_schedule_forca_na(self):
        """GLOBO_CONTROLE usa TIPO_EXTREMIDADE_GC — "BUTT-WELDING" sem número de
        schedule (diferente de "BUTT-WELDING 40" etc dos outros tipos)."""
        payload = {
            "tipo_valvula": "GLOBO_CONTROLE", "funcao": "CONTROLE", "nbr": False,
            "diametro": '2"', "classe": "150",
            "tipo_extremidade": "BUTT-WELDING", "tipo_ranhura": "LISO (125 μin)",
            "tipo_passagem": "PLENA", "tipo_acionamento": "PNEUMATICO",
            "juncao_corpo_castelo": "APARAFUSADO",
            "posicionador": "4-20 mA", "valvula_solenoide": "SIM",
            "chave_fim_curso": "SIM", "sensor_posicao": "SIM",
        }
        resp = self.client.post(
            reverse("core:valvula_criar"), json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertEqual(v.tipo_ranhura, "N/A")


# ── NBR 15827: regras de junta / parafusos / porcas / revestimento por corpo ──

class NbrJuntaRuleTest(EspecialMixin, TestCase):
    """Gaveta/Retenção + NBR 15827 → junta não pode ser N/A."""

    def _payload(self, junta_material):
        return {
            "tipo_valvula": "GAVETA", "funcao": "BLOQUEIO", "nbr": True, "norma": "API 600",
            "diametro": '2"', "classe": "150", "tipo_extremidade": "FLANGE RF",
            "tipo_ranhura": "LISO (125 μin)", "tipo_passagem": "PLENA",
            "tipo_acionamento": "VOLANTE", "tipo_castelo": "NORMAL",
            "juncao_corpo_castelo": "APARAFUSADO", "uso_geral": "USO GERAL",
            "certificacao_sil": "SIL 1", "nace": "N/A", "revestimento": "N/A",
            "materiais": [{"tipo_material": "MATERIAL_JUNTA", "material": junta_material}],
        }

    def _post(self, payload):
        return self.client.post(
            reverse("core:valvula_criar"), json.dumps(payload),
            content_type="application/json",
        )

    def test_junta_na_rejeitada(self):
        resp = self._post(self._payload("N/A"))
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("materiais", resp.json()["errors"])

    def test_junta_valida_aceita(self):
        resp = self._post(self._payload("AISI 304 + GRAFITE FLEXÍVEL"))
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertTrue(resp.json()["success"])


class VedacaoNbrClasseRuleTest(EspecialMixin, TestCase):
    """Gaveta + NBR 15827 + classe 2500 só aceita RTJ (FJA)/Pressure Seal/Castelo
    Soldado (_VED_NBR_POR_CLASSE, views.py:37). A trava lê a Categoria da Junta em
    Materiais (tipo_material=JUNTA) — a Vedação Sede/Tampa (Vedacao model) virou
    exclusiva de Esfera; Gaveta/Globo/Retenção/GC usam só a categoria da junta."""

    def _payload(self, junta_categoria):
        return {
            "tipo_valvula": "GAVETA", "funcao": "BLOQUEIO", "nbr": True, "norma": "API 600",
            "diametro": '2"', "classe": "2500", "tipo_extremidade": "FLANGE RTJ",
            "tipo_ranhura": "LISO (125 μin)", "tipo_passagem": "PLENA",
            "tipo_acionamento": "VOLANTE", "tipo_castelo": "NORMAL",
            "juncao_corpo_castelo": "APARAFUSADO", "uso_geral": "USO GERAL",
            "certificacao_sil": "SIL 1", "nace": "N/A", "revestimento": "N/A",
            "materiais": [
                {"tipo_material": "JUNTA", "material": junta_categoria},
                {"tipo_material": "CORPO_TAMPA", "material": "A105"},
                {"tipo_material": "PARAFUSOS", "material": "ASTM A193 B7"},
                {"tipo_material": "PORCAS", "material": "ASTM A194 2H"},
            ],
        }

    def _post(self, payload):
        return self.client.post(
            reverse("core:valvula_criar"), json.dumps(payload),
            content_type="application/json",
        )

    def test_junta_invalida_rejeitada(self):
        resp = self._post(self._payload("JUNTA ESPIRALADA"))
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("materiais", resp.json()["errors"])

    def test_junta_valida_aceita(self):
        resp = self._post(self._payload("PRESSURE SEAL"))
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertTrue(resp.json()["success"])


class NbrParafusoPorcaPorCorpoRuleTest(EspecialMixin, TestCase):
    """NBR 15827: material do corpo define parafusos/porcas (e revestimento no inox).

    Conjuntos de corpo disjuntos:
      - carbono (A105/A181/A216 WCB)        → B7 / 2H
      - liga (A350 LF2/LF3, A352 LCB/LC3)   → A320 L7 / B8M / B8M CL2 ; 8M / 4L / 7L
      - cromo-molib (A182 F11 CL2/F5, A217 WC6/C5) → B16 / Gr 7
      - inox austenítico (F304/F316/F317/F347, CF8/CF8M/CG8M/CF8C) → B8M/B8M CL2 ; 8M ; revest N/A
    """

    def _payload(self, corpo, parafuso=None, porca=None, revestimento="N/A"):
        materiais = [{"tipo_material": "CORPO_TAMPA", "material": corpo}]
        if parafuso:
            materiais.append({"tipo_material": "PARAFUSOS", "material": parafuso})
        if porca:
            materiais.append({"tipo_material": "PORCAS", "material": porca})
        return {
            "tipo_valvula": "GAVETA", "funcao": "BLOQUEIO", "nbr": True, "norma": "API 600",
            "diametro": '2"', "classe": "150", "tipo_extremidade": "FLANGE RF",
            "tipo_ranhura": "LISO (125 μin)", "tipo_passagem": "PLENA",
            "tipo_acionamento": "VOLANTE", "tipo_castelo": "NORMAL",
            "juncao_corpo_castelo": "APARAFUSADO", "uso_geral": "USO GERAL",
            "certificacao_sil": "SIL 1", "nace": "N/A", "revestimento": revestimento,
            "materiais": materiais,
        }

    def _post(self, payload):
        return self.client.post(
            reverse("core:valvula_criar"), json.dumps(payload),
            content_type="application/json",
        )

    # ── carbono → B7 / 2H ──
    def test_b7_parafuso_errado_rejeitado(self):
        resp = self._post(self._payload("ASTM A105", "ASTM A193 B8", "ASTM A194 2H"))
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("materiais", resp.json()["errors"])

    def test_b7_porca_errada_rejeitada(self):
        resp = self._post(self._payload("ASTM A105", "ASTM A193 B7", "ASTM A194 Gr 8"))
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("materiais", resp.json()["errors"])

    def test_b7_correto_aceito(self):
        resp = self._post(self._payload("ASTM A105", "ASTM A193 B7", "ASTM A194 2H"))
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── liga → A320 L7 / B8M / B8M CL2 ; 8M / 4L / 7L ──
    def test_liga_parafuso_fora_rejeitado(self):
        resp = self._post(self._payload("ASTM A352 LC3", "ASTM A193 B7", "ASTM A194 Gr 4L"))
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("materiais", resp.json()["errors"])

    def test_liga_correto_aceito(self):
        resp = self._post(self._payload("ASTM A352 LC3", "ASTM A193 Gr B8M", "ASTM A194 Gr 4L"))
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── cromo-molib → B16 / Gr 7 ──
    def test_b16_porca_errada_rejeitada(self):
        resp = self._post(self._payload("ASTM A217 WC6", "ASTM A193 Gr B16", "ASTM A194 Gr 8"))
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("materiais", resp.json()["errors"])

    def test_b16_correto_aceito(self):
        resp = self._post(self._payload("ASTM A217 WC6", "ASTM A193 Gr B16", "ASTM A194 Gr 7"))
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── inox → B8M/B8M CL2 ; 8M ; revestimento N/A ──
    def test_inox_parafuso_errado_rejeitado(self):
        resp = self._post(self._payload("ASTM A182 F316", "ASTM A193 B7", "ASTM A194 Gr 8M"))
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("materiais", resp.json()["errors"])

    def test_inox_porca_errada_rejeitada(self):
        resp = self._post(self._payload("ASTM A182 F316", "ASTM A193 Gr B8M", "ASTM A194 2H"))
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("materiais", resp.json()["errors"])

    def test_inox_revestimento_nao_na_rejeitado(self):
        resp = self._post(self._payload(
            "ASTM A182 F316", "ASTM A193 Gr B8M", "ASTM A194 Gr 8M", revestimento="ZINCO NÍQUEL"))
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("revestimento", resp.json()["errors"])

    def test_inox_correto_aceito(self):
        resp = self._post(self._payload(
            "ASTM A182 F316", "ASTM A193 Gr B8M", "ASTM A194 Gr 8M", revestimento="N/A"))
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_inox_cg8m_correto_aceito(self):
        """CG8M (adicionado à lista do corpo) entra no conjunto inox."""
        resp = self._post(self._payload(
            "ASTM A351 CG8M", "ASTM A193 Gr B8M CL2", "ASTM A194 Gr 8M", revestimento="N/A"))
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_corpo_fora_das_regras_nao_restringe(self):
        """Corpo não listado + NBR → parafuso/porca livres (sem 400)."""
        resp = self._post(self._payload("ASTM A182 F51", "ASTM A193 B8", "ASTM A194 Gr 8"))
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── corpo revestido (variante do mesmo material base) também entra na regra ──
    def test_b7_corpo_revestido_parafuso_errado_rejeitado(self):
        """A105N revestido a INCONEL é o mesmo corpo carbono do A105 → ainda exige B7/2H."""
        resp = self._post(self._payload(
            "ASTM A105N revestimento interno de INCONEL", "ASTM A193 B8", "ASTM A194 2H"))
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("materiais", resp.json()["errors"])

    def test_b7_corpo_revestido_correto_aceito(self):
        resp = self._post(self._payload(
            "ASTM A105N revestimento interno de INCONEL", "ASTM A193 B7", "ASTM A194 2H"))
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_liga_corpo_revestido_correto_aceito(self):
        """A350 LF2 Cl1 revestido a INCONEL é variante do corpo liga LF2."""
        resp = self._post(self._payload(
            "ASTM A350 LF2 Cl1 revestimento interno de INCONEL", "ASTM A193 Gr B8M", "ASTM A194 Gr 4L"))
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_b16_f55_nao_confundido_com_f5(self):
        """F55 é grau distinto de F5 (boundary de prefixo não pode confundir os dois)."""
        resp = self._post(self._payload("ASTM A182 F55", "ASTM A193 B8", "ASTM A194 Gr 8"))
        self.assertEqual(resp.status_code, 200, resp.content)


class ParafusoPorcaCompatSemNbrTest(EspecialMixin, TestCase):
    """Sem NBR (nem NACE), parafuso e porca ainda tem que ser um par compatível —
    o corpo nao dita mais o par, mas parafuso/porca continuam amarrados entre si."""

    def _payload(self, parafuso, porca, nace="N/A"):
        return {
            "tipo_valvula": "ESFERA", "funcao": "BLOQUEIO", "nbr": False,
            "dispositivo_antiestatico": True, "tipo_montagem": "TRUNNION",
            "diametro": '2"', "classe": "150", "nace": nace,
            "materiais": [
                {"tipo_material": "PARAFUSOS", "material": parafuso},
                {"tipo_material": "PORCAS", "material": porca},
            ],
        }

    def _post(self, **kw):
        return self.client.post(reverse("core:valvula_criar"), json.dumps(self._payload(**kw)),
                                content_type="application/json")

    def test_b7_com_2h_aceito(self):
        resp = self._post(parafuso="ASTM A193 B7", porca="ASTM A194 2H")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_b7_com_gr8_rejeitado(self):
        resp = self._post(parafuso="ASTM A193 B7", porca="ASTM A194 Gr 8")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("materiais", resp.json()["errors"])

    def test_b8_aceita_gr8_ou_8a(self):
        for porca in ("ASTM A194 Gr 8", "ASTM A194 8A"):
            with self.subTest(porca=porca):
                resp = self._post(parafuso="ASTM A193 B8", porca=porca)
                self.assertEqual(resp.status_code, 200, porca)

    def test_l7_aceita_qualquer_um_dos_4(self):
        for porca in ("ASTM A194 Gr 7", "ASTM A194 Gr 7L", "ASTM A194 Gr 4", "ASTM A194 Gr 4L"):
            with self.subTest(porca=porca):
                resp = self._post(parafuso="ASTM A320 Gr L7", porca=porca)
                self.assertEqual(resp.status_code, 200, porca)

    def test_l7_com_2h_rejeitado(self):
        resp = self._post(parafuso="ASTM A320 Gr L7", porca="ASTM A194 2H")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("materiais", resp.json()["errors"])

    def test_padrao_fabricante_aceita_so_padrao(self):
        resp = self._post(parafuso="PADRÃO FABRICANTE", porca="PADRÃO FABRICANTE")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_padrao_fabricante_com_na_rejeitado(self):
        resp = self._post(parafuso="PADRÃO FABRICANTE", porca="N/A")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("materiais", resp.json()["errors"])

    def test_zeron_exige_zeron(self):
        resp = self._post(parafuso="ZERON 100 FG", porca="UNS S32760")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("materiais", resp.json()["errors"])

    def test_com_nbr_nao_roda_essa_regra(self):
        """Com NBR ativo, a regra de corpo (não esta) e' quem manda."""
        p = self._payload(parafuso="ASTM A193 B7", porca="ASTM A194 Gr 8")
        p["nbr"] = True
        p["tipo_montagem"] = "FLUTUANTE"  # NBR + diametro 2" + classe 150 exige Flutuante
        resp = self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")
        # Sem corpo cadastrado, nenhuma regra de corpo NBR dispara -> par livre
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_nace_nao_altera_a_regra_de_compat(self):
        """NACE nao tem mais regra propria de parafuso/porca: o par compativel do
        parafuso escolhido continua mandando, com ou sem NACE."""
        resp = self._post(parafuso="ASTM A193 Grade B7M", porca="ASTM A194 Grade 8MA",
                          nace="MR0175 ISO 15156")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("materiais", resp.json()["errors"])


# ── NBR 15827: Esfera Flange/Butt-Welding (norma/uso/diâmetro por classe) ─────

class EsferaFlangeButtRuleTest(EspecialMixin, TestCase):
    def _post(self, **kw):
        p = {
            "tipo_valvula": "ESFERA", "nbr": True, "dispositivo_antiestatico": True,
            "tipo_extremidade": "FLANGE RF", "tipo_montagem": "FLUTUANTE",
            "diametro": '4"', "classe": "150", "norma": "ISO 14313", "uso_geral": "ISO 14313",
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_aceito(self):
        self.assertEqual(self._post().status_code, 200, "flange esfera base deve passar")

    def test_norma_invalida(self):
        resp = self._post(norma="API 608")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("norma", resp.json()["errors"])

    def test_uso_invalido(self):
        resp = self._post(uso_geral="USO GERAL")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("uso_geral", resp.json()["errors"])

    def test_diametro_classe1500_max16(self):
        resp = self._post(classe="1500", diametro='18"', tipo_montagem="TRUNNION")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_diametro_classe1500_ok(self):
        resp = self._post(classe="1500", diametro='16"', tipo_montagem="TRUNNION")
        self.assertEqual(resp.status_code, 200, resp.content)


# ── NBR 15827: Esfera Rosca — norma construtiva dita classe/uso ──────────────

class EsferaRoscaRuleTest(EspecialMixin, TestCase):
    """A norma construtiva é o parâmetro: BS ISO 7121 → classe 150 + uso N/A;
    ISO 17292 → classe 800 + uso ISO 17292/ISO 10497/API 607."""

    def _post(self, **kw):
        p = {
            "tipo_valvula": "ESFERA", "funcao": "BLOQUEIO", "nbr": True,
            "dispositivo_antiestatico": True,
            "tipo_extremidade": "ROSCA NPT", "tipo_montagem": "FLUTUANTE",
            "diametro": '1"', "classe": "150", "norma": "BS ISO 7121", "uso_geral": "N/A",
            "materiais": [{"tipo_material": "CORPO_TAMPA", "material": "ASTM A105"}],
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_bs7121_classe150_aceito(self):
        self.assertEqual(self._post().status_code, 200, "rosca BS ISO 7121 + 150 deve passar")

    def test_iso17292_classe800_aceito(self):
        resp = self._post(classe="800", norma="ISO 17292", uso_geral="ISO 17292")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_norma_fora_do_par(self):
        resp = self._post(norma="API 6D", qsl="QSL2")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("norma", resp.json()["errors"])

    def test_bs7121_classe_errada(self):
        resp = self._post(classe="800")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_iso17292_classe_errada(self):
        resp = self._post(norma="ISO 17292", classe="150", uso_geral="ISO 17292")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_bs7121_uso_fire_test_barrado(self):
        resp = self._post(uso_geral="API 607")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("uso_geral", resp.json()["errors"])

    def test_classe_invalida(self):
        resp = self._post(classe="300")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_diametro_invalido(self):
        resp = self._post(diametro='2"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])


# ── NBR 15827: Esfera Socket-Welding + corpo (diâmetro/classe/uso) ────────────

class EsferaSocketCorpoRuleTest(EspecialMixin, TestCase):
    def _post(self, **kw):
        p = {
            "tipo_valvula": "ESFERA", "nbr": True, "dispositivo_antiestatico": True,
            "tipo_extremidade": "SOCKET-WELDING", "tipo_montagem": "FLUTUANTE",
            "diametro": '1"', "classe": "800", "norma": "ISO 17292", "uso_geral": "ISO 17292",
            "materiais": [{"tipo_material": "CORPO_TAMPA", "material": "ASTM A105"}],
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_aceito(self):
        self.assertEqual(self._post().status_code, 200, "socket esfera base deve passar")

    def test_diametro_invalido(self):
        resp = self._post(diametro='2"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_uso_invalido(self):
        resp = self._post(uso_geral="USO GERAL")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("uso_geral", resp.json()["errors"])

    def test_classe_invalida(self):
        resp = self._post(classe="600", norma="ISO 17292")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])


# ── NBR 15827 Tabela C.2: espessura de parede do niple (Esfera) ──────────────

class EsferaNipleTabelaC2Test(EspecialMixin, TestCase):
    """Tabela C.2: 150/300/600/800 → SCH 160 (carbono/liga) e SCH 80S (inox);
    900 e 1500 → SCH 160 (ambos); 2500 → XXS (ambos)."""

    CARBONO = "ASTM A105"
    INOX = "ASTM A182 F316"

    def _post(self, corpo, classe, extremidade):
        make_material(corpo)
        return self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({
                "tipo_valvula": "ESFERA", "funcao": "BLOQUEIO", "nbr": True,
                "dispositivo_antiestatico": True,
                "diametro": '2"', "tipo_montagem": "TRUNNION",
                "classe": classe, "tipo_extremidade": extremidade,
                "materiais": [{"tipo_material": "CORPO_TAMPA", "material": corpo}],
            }),
            content_type="application/json",
        )

    def test_2500_carbono_exige_xxs(self):
        resp = self._post(self.CARBONO, "2500", 'NIPLE 4" COMP. SCH 160')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_2500_inox_exige_xxs(self):
        resp = self._post(self.INOX, "2500", 'NIPLE 4" COMP. SCH 80')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_2500_xxs_aceito(self):
        resp = self._post(self.CARBONO, "2500", 'NIPLE 4" COMP. SCH XXS')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_900_carbono_exige_sch160(self):
        resp = self._post(self.CARBONO, "900", 'NIPLE 4" COMP. SCH 80')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_900_carbono_sch160_aceito(self):
        resp = self._post(self.CARBONO, "900", 'NIPLE 4" COMP. SCH 160')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_1500_inox_sch160_aceito(self):
        resp = self._post(self.INOX, "1500", 'NIPLE 4" COMP. SCH 160')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_800_inox_sch80_aceito(self):
        resp = self._post(self.INOX, "800", 'NIPLE 4" COMP. SCH 80')
        self.assertEqual(resp.status_code, 200, resp.content)


class NipleDiametroMaximoTest(EspecialMixin, TestCase):
    """Niple e' peca de pequeno porte: acima de 3" nao e' oferecido, pra qualquer tipo
    de valvula (Esfera/Gaveta/Globo/Retencao) e independente de NBR/norma."""

    def test_esfera_niple_acima_de_3_rejeitado(self):
        make_material("ASTM A105")
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({
                "tipo_valvula": "ESFERA", "funcao": "BLOQUEIO", "nbr": False,
                "diametro": '4"', "tipo_montagem": "TRUNNION",
                "classe": "150", "tipo_extremidade": 'NIPLE 4" COMP. SCH 160',
                "materiais": [{"tipo_material": "CORPO_TAMPA", "material": "ASTM A105"}],
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_esfera_niple_3_polegadas_aceito(self):
        make_material("ASTM A105")
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({
                "tipo_valvula": "ESFERA", "funcao": "BLOQUEIO", "nbr": False,
                "diametro": '3"', "tipo_montagem": "TRUNNION",
                "classe": "150", "tipo_extremidade": 'NIPLE 4" COMP. SCH 160',
                "materiais": [{"tipo_material": "CORPO_TAMPA", "material": "ASTM A105"}],
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_gaveta_niple_acima_de_3_rejeitado(self):
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({
                "tipo_valvula": "GAVETA", "funcao": "BLOQUEIO", "nbr": False,
                "diametro": '4"', "classe": "150",
                "tipo_extremidade": 'NIPLE 4" COMP. SCH 160',
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_niple_sem_diametro_nao_quebra(self):
        resp = self.client.post(
            reverse("core:valvula_criar"),
            json.dumps({
                "tipo_valvula": "GAVETA", "funcao": "BLOQUEIO", "nbr": False,
                "classe": "150", "tipo_extremidade": 'NIPLE 4" COMP. SCH 160',
            }),
            content_type="application/json",
        )
        self.assertNotIn("tipo_extremidade", resp.json().get("errors", {}))


# ── NBR 15827: Globo Socket-Welding + corpo ──────────────────────────────────

class GloboSocketWeldingRuleTest(EspecialMixin, TestCase):
    def _post(self, **kw):
        p = {
            "tipo_valvula": "GLOBO", "nbr": True,
            "tipo_extremidade": "SOCKET-WELDING",
            "diametro": '1"', "classe": "800", "norma": "ISO 15761",
            "materiais": [{"tipo_material": "CORPO_TAMPA", "material": "ASTM A105"}],
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_aceito(self):
        self.assertEqual(self._post().status_code, 200, "globo socket base deve passar")

    def test_diametro_invalido(self):
        resp = self._post(diametro='2"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_classe_invalida(self):
        resp = self._post(classe="2500")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_norma_invalida(self):
        resp = self._post(norma="BS 1873")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("norma", resp.json()["errors"])


# ── NBR 15827: Globo Butt-Welding (1500 geral / 2500 corpo elegível) ──────────

class GloboButtWeldingRuleTest(EspecialMixin, TestCase):
    def _post(self, **kw):
        p = {
            "tipo_valvula": "GLOBO", "nbr": True,
            "tipo_extremidade": "BUTT-WELDING",
            "diametro": '1"', "classe": "2500", "norma": "ASME B16.34",
            "materiais": [{"tipo_material": "CORPO_TAMPA", "material": "ASTM A105"}],
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_corpo_eligivel_2500_aceito(self):
        self.assertEqual(self._post().status_code, 200, "butt 2500 corpo elegível deve passar")

    def test_corpo_eligivel_1500_aceito(self):
        resp = self._post(classe="1500", diametro='4"', norma="BS 1873")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_corpo_eligivel_classe_invalida(self):
        resp = self._post(classe="800")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_2500_diametro_invalido(self):
        resp = self._post(diametro='4"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_outro_corpo_so_1500(self):
        resp = self._post(classe="2500",
                          materiais=[{"tipo_material": "CORPO_TAMPA", "material": "ASTM A216 WCB"}])
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_outro_corpo_1500_aceito(self):
        resp = self._post(classe="1500", diametro='4"', norma="BS 1873",
                          materiais=[{"tipo_material": "CORPO_TAMPA", "material": "ASTM A216 WCB"}])
        self.assertEqual(resp.status_code, 200, resp.content)


# ── NBR 15827: Globo Flange ──────────────────────────────────────────────────

class GloboFlangeRuleTest(EspecialMixin, TestCase):
    def _post(self, **kw):
        p = {
            "tipo_valvula": "GLOBO", "nbr": True,
            "tipo_extremidade": "FLANGE RF",
            "diametro": '4"', "classe": "300", "norma": "BS 1873",
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_aceito(self):
        self.assertEqual(self._post().status_code, 200, "globo flange base deve passar")

    def test_diametro_invalido(self):
        resp = self._post(diametro='16"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_norma_invalida(self):
        resp = self._post(norma="API 602")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("norma", resp.json()["errors"])


# ── NBR 15827: Borboleta Bi/Tri-Excêntrica + corpo fora do set ───────────────

class BorboletaBiExcRuleTest(EspecialMixin, TestCase):
    def _post(self, **kw):
        p = {
            "tipo_valvula": "BORBOLETA", "nbr": True,
            "face_a_face": "WAFER", "configuracao_disco": "BI-EXCÊNTRICA",
            "diametro": '4"', "classe": "300", "norma": "API 609",
            "materiais": [{"tipo_material": "CORPO_TAMPA", "material": "ASTM A216 WCB"}],
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_aceito(self):
        self.assertEqual(self._post().status_code, 200, "borboleta bi base deve passar")

    def test_classe_invalida(self):
        resp = self._post(classe="900")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_diametro_invalido(self):
        resp = self._post(diametro='30"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_norma_invalida(self):
        resp = self._post(norma="ASME B16.34")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("norma", resp.json()["errors"])

    def test_corpo_excluido_nao_aplica(self):
        """Corpo A105 está no set excluído → regra não aplica (classe 900 passa)."""
        resp = self._post(classe="900",
                          materiais=[{"tipo_material": "CORPO_TAMPA", "material": "ASTM A105"}])
        self.assertEqual(resp.status_code, 200, resp.content)


class RetencaoPassagemPlenaTest(EspecialMixin, TestCase):
    """NBR 15827 Tabela 2: a celula "Flange ou solda de topo" da Retencao tem duas
    alternativas de padrao construtivo, e so' uma exige passagem plena:
      - "BS 1868, ASME B16.34 e Anexo B"                 -> passagem livre
      - "ISO 14313 (API 6D) e Anexo B (Passagem Plena)"  -> passagem plena obrigatoria
    """

    def _post(self, **kw):
        p = {
            "tipo_valvula": "RETENCAO", "funcao": "BLOQUEIO", "nbr": True,
            "tipo_extremidade": "FLANGE RF", "diametro": '4"', "classe": "300",
            "norma": "ISO 14313", "tipo_passagem": "PLENA",
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_iso14313_plena_aceita(self):
        self.assertEqual(self._post().status_code, 200, self._post().content)

    def test_iso14313_reduzida_rejeitada(self):
        resp = self._post(tipo_passagem="REDUZIDA")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_passagem", resp.json()["errors"])

    def test_api6d_reduzida_rejeitada(self):
        resp = self._post(norma="API 6D", qsl="QSL2", tipo_passagem="REDUZIDA")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_passagem", resp.json()["errors"])

    def test_bs1868_reduzida_aceita(self):
        """A outra alternativa da celula nao exige passagem plena."""
        resp = self._post(norma="BS 1868", tipo_passagem="REDUZIDA")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_b1634_reduzida_aceita(self):
        resp = self._post(norma="ASME B16.34", tipo_passagem="REDUZIDA")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_wafer_nao_aplica(self):
        """A regra e' da celula de flange/solda de topo; wafer e' API 594."""
        resp = self._post(tipo_extremidade="Wafer", norma="API 594",
                          tipo_passagem="REDUZIDA")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_sem_nbr_nao_aplica(self):
        resp = self._post(nbr=False, tipo_passagem="REDUZIDA")
        self.assertEqual(resp.status_code, 200, resp.content)


class Iso14313EscopoTest(EspecialMixin, TestCase):
    """ISO 14313 7.2: "Valves covered by this International Standard shall be furnished in
    one of the following classes: PN 20 (class 150); PN 50 (class 300); PN 64 (class 400);
    PN 100 (class 600); PN 150 (class 900); PN 250 (class 1500); PN 420 (class 2500)".
    Ao contrario da API 6D, aceita a serie PN. Class 400/PN 64 nao existe no modelo."""

    def _post(self, **kw):
        p = {
            "tipo_valvula": "GAVETA", "funcao": "BLOQUEIO", "nbr": False,
            "norma": "ISO 14313", "diametro": '4"', "classe": "300",
            "tipo_extremidade": "FLANGE RF",
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_base_aceita(self):
        self.assertEqual(self._post().status_code, 200, self._post().content)

    # ── serie Class aceita ──
    def test_classes_ansi_aceitas(self):
        for c in ["150", "300", "600", "900", "1500", "2500"]:
            with self.subTest(classe=c):
                self.assertEqual(self._post(classe=c).status_code, 200)

    # ── serie PN aceita (a API 6D bloqueia PN; a ISO 14313 nao) ──
    def test_classes_pn_aceitas(self):
        for c in ["PN 20", "PN 50", "PN 100", "PN 150", "PN 250", "PN 420"]:
            with self.subTest(classe=c):
                self.assertEqual(self._post(classe=c).status_code, 200, c)

    # ── fora do escopo da 7.2 ──
    def test_classe_800_rejeitada(self):
        resp = self._post(classe="800")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_classe_4500_rejeitada(self):
        resp = self._post(classe="4500")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_pn_fora_da_serie_rejeitadas(self):
        for c in ["PN 10", "PN 16", "PN 25", "PN 40"]:
            with self.subTest(classe=c):
                resp = self._post(classe=c)
                self.assertEqual(resp.status_code, 400, c)
                self.assertIn("classe", resp.json()["errors"])

    def test_outra_norma_nao_restringe(self):
        """Classe 800 e' rejeitada pela 7.2 da ISO 14313, mas passa com outra norma
        cuja propria regra aceita 800 (API 602, Socket-Welding) — todas as normas de
        Gaveta ja tem regra propria de escopo; o que importa e' que a regra da
        ISO 14313 especificamente nao dispara fora dela."""
        resp = self._post(norma="API 602", classe="800",
                          tipo_extremidade="SOCKET-WELDING", diametro='1"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_api6d_continua_bloqueando_pn(self):
        """Regressao: API 6D e ISO 14313 sao harmonizadas mas divergem em PN."""
        resp = self._post(norma="API 6D", classe="PN 20", qsl="QSL2")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_iso14313_nao_exige_qsl(self):
        """QSL e' conceito da API 6D (Anexo I); nao existe na ISO 14313."""
        resp = self._post(classe="600")
        self.assertEqual(resp.status_code, 200, resp.content)


class Iso17292EscopoTest(EspecialMixin, TestCase):
    """ISO 17292 Secao 1: classes Class 150/300/600/800 e PN 16/25/40/63/100 (PN 63 fora
    do modelo); Class 800 so' em rosca/socket-welding; flange/butt-welding 1/2"-24";
    socket-welding/rosca 1/4"-2"; so' cobre flange/BW/SW/rosca (sem Wafer/Lug/Gray Loc).
    5.2.7: dispositivo antiestatico obrigatorio. Regras valem com ou sem NBR."""

    def _post(self, **kw):
        p = {
            "tipo_valvula": "ESFERA", "funcao": "BLOQUEIO", "nbr": False,
            "dispositivo_antiestatico": True, "tipo_montagem": "FLUTUANTE",
            "norma": "ISO 17292", "diametro": '2"', "classe": "300",
            "tipo_extremidade": "FLANGE RF",
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_base_aceita(self):
        resp = self._post()
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── classes ──
    def test_classes_aceitas_flange(self):
        for c in ["150", "300", "600", "PN 16", "PN 25", "PN 40", "PN 100"]:
            with self.subTest(classe=c):
                self.assertEqual(self._post(classe=c).status_code, 200, c)

    def test_classes_fora_do_escopo(self):
        for c in ["900", "1500", "2500", "4500", "PN 10", "PN 20", "PN 50"]:
            with self.subTest(classe=c):
                resp = self._post(classe=c)
                self.assertEqual(resp.status_code, 400, c)
                self.assertIn("classe", resp.json()["errors"])

    # ── classe 800 so' rosca/socket-welding ──
    def test_classe800_rosca_aceita(self):
        resp = self._post(classe="800", tipo_extremidade="ROSCA NPT", diametro='1"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe800_socket_aceita(self):
        resp = self._post(classe="800", tipo_extremidade="SOCKET-WELDING", diametro='1"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe800_flange_rejeitada(self):
        resp = self._post(classe="800")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    # ── diametro por extremidade ──
    def test_flange_24_aceito(self):
        resp = self._post(diametro='24"', tipo_montagem="TRUNNION")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_flange_26_rejeitado(self):
        resp = self._post(diametro='26"', tipo_montagem="TRUNNION")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_socket_acima_de_2_rejeitado(self):
        resp = self._post(tipo_extremidade="SOCKET-WELDING", diametro='2 1/2"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_rosca_2_aceita(self):
        resp = self._post(tipo_extremidade="ROSCA NPT")
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── extremidade fora da norma ──
    def test_gray_loc_rejeitado(self):
        resp = self._post(tipo_extremidade="GRAY LOC HUB")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    # ── 5.2.7: antiestatico obrigatorio ──
    def test_sem_antiestatico_rejeitado(self):
        resp = self._post(dispositivo_antiestatico=False)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("dispositivo_antiestatico", resp.json()["errors"])

    def test_outra_norma_nao_exige_antiestatico(self):
        resp = self._post(norma="API 608", dispositivo_antiestatico=False)
        self.assertEqual(resp.status_code, 200, resp.content)


class Bs7121EscopoTest(EspecialMixin, TestCase):
    """BS ISO 7121 Clausula 1: classes 150/300/600/900 e PN 10/16/25/40/63/100 (PN 63
    fora do modelo); classe 900 so' passagem reduzida (Tabela 2, nota de rodape);
    extremidades flange/BW ate' 20", socket-welding ate' 4", rosca ate' 2"; so' cobre
    flange/BW/SW/rosca (sem Wafer/Lug/Gray Loc). Antiestatico e' opcional (5.2.7
    "when specified"), diferente da ISO 17292 onde e' obrigatorio."""

    def _post(self, **kw):
        p = {
            "tipo_valvula": "ESFERA", "funcao": "BLOQUEIO", "nbr": False,
            "dispositivo_antiestatico": True, "tipo_montagem": "FLUTUANTE",
            "norma": "BS ISO 7121", "diametro": '2"', "classe": "300",
            "tipo_extremidade": "FLANGE RF", "tipo_passagem": "PLENA",
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_base_aceita(self):
        resp = self._post()
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── classes ──
    def test_classes_aceitas(self):
        for c in ["150", "300", "600", "PN 10", "PN 16", "PN 25", "PN 40", "PN 100"]:
            with self.subTest(classe=c):
                self.assertEqual(self._post(classe=c).status_code, 200, c)

    def test_classes_fora_do_escopo(self):
        for c in ["800", "1500", "2500", "4500", "PN 20", "PN 50", "PN 63"]:
            with self.subTest(classe=c):
                resp = self._post(classe=c)
                self.assertEqual(resp.status_code, 400, c)
                self.assertIn("classe", resp.json()["errors"])

    # ── classe 900 so' passagem reduzida ──
    def test_classe900_reduzida_aceita(self):
        resp = self._post(classe="900", tipo_passagem="REDUZIDA")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe900_plena_rejeitada(self):
        resp = self._post(classe="900")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_passagem", resp.json()["errors"])

    # ── diametro por extremidade ──
    def test_flange_20_aceito(self):
        resp = self._post(diametro='20"', tipo_montagem="TRUNNION")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_flange_22_rejeitado(self):
        resp = self._post(diametro='22"', tipo_montagem="TRUNNION")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_socket_4_aceito(self):
        resp = self._post(tipo_extremidade="SOCKET-WELDING", diametro='4"', tipo_montagem="TRUNNION")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_socket_6_rejeitado(self):
        resp = self._post(tipo_extremidade="SOCKET-WELDING", diametro='6"', tipo_montagem="TRUNNION")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_rosca_2_aceita(self):
        resp = self._post(tipo_extremidade="ROSCA NPT")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_rosca_acima_de_2_rejeitada(self):
        resp = self._post(tipo_extremidade="ROSCA NPT", diametro='2 1/2"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    # ── extremidade fora da norma ──
    def test_wafer_rejeitado(self):
        resp = self._post(tipo_extremidade="Wafer")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    # ── antiestatico e' opcional (diferente da ISO 17292) ──
    def test_sem_antiestatico_aceito(self):
        resp = self._post(dispositivo_antiestatico=False)
        self.assertEqual(resp.status_code, 200, resp.content)


class Api608EscopoTest(EspecialMixin, TestCase):
    """API 608 Clausula 1 (so' Esfera oferece a norma): 1.2 e' adicional a' ASME B16.34
    Standard Class. 1.1: Flange/Butt-Welding NPS 1/2-12; Socket-Welding/Rosca NPS 1/2-2
    (Niple conta como SW); sem Wafer/Lug/Gray Loc Hub. 1.3: Flange/BW so' Standard Class
    150/300 (sem 600); Socket-Welding/Rosca 150/300/600. 4.4 (continuidade
    eletrica/antiestatico) e' opcional ("when specified"), igual a BS ISO 7121."""

    def _post(self, **kw):
        p = {
            "tipo_valvula": "ESFERA", "funcao": "BLOQUEIO", "nbr": False,
            "dispositivo_antiestatico": True, "tipo_montagem": "FLUTUANTE",
            "norma": "API 608", "diametro": '2"', "classe": "300",
            "tipo_extremidade": "FLANGE RF",
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_base_aceita(self):
        resp = self._post()
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── classe por extremidade (1.3) ──
    def test_classe_flange_150_aceita(self):
        resp = self._post(classe="150")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe_flange_600_rejeitada(self):
        resp = self._post(classe="600")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_classe_sw_600_aceita(self):
        resp = self._post(classe="600", tipo_extremidade="SOCKET-WELDING", diametro='1"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe_sw_fora_do_escopo(self):
        resp = self._post(classe="900", tipo_extremidade="SOCKET-WELDING", diametro='1"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    # ── diametro por extremidade (1.1) ──
    def test_diametro_flange_12_aceito(self):
        resp = self._post(diametro='12"', tipo_montagem="TRUNNION")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_diametro_flange_acima_12_rejeitado(self):
        resp = self._post(diametro='14"', tipo_montagem="TRUNNION")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_diametro_sw_2_aceito(self):
        resp = self._post(tipo_extremidade="SOCKET-WELDING", diametro='2"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_diametro_sw_acima_2_rejeitado(self):
        resp = self._post(tipo_extremidade="SOCKET-WELDING", diametro='2 1/2"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_rosca_aceita(self):
        resp = self._post(tipo_extremidade="ROSCA NPT", diametro='1"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_rosca_acima_de_2_rejeitada(self):
        resp = self._post(tipo_extremidade="ROSCA NPT", diametro='2 1/2"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    # ── extremidade fora da norma ──
    def test_wafer_rejeitado(self):
        resp = self._post(tipo_extremidade="Wafer")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])


class MssSp72EscopoTest(EspecialMixin, TestCase):
    """MSS SP-72 (Secoes 1, 2, 3; so' Esfera oferece a norma, choice "MSS SP72"). 1.1:
    extremidade so' Flange ou Butt-Welding (sem Socket-Welding/Rosca/Niple/Wafer/Lug/
    Gray Loc Hub). 1.3: diametro NPS 1/2-36" (DN 15-900). 2.1 (rating por material) nao
    vira trava extra de classe: o modelo so' tem materiais de corpo em aco, cobertos pela
    designacao Class da B16.34 (generica, ja validada em outro lugar)."""

    def _post(self, **kw):
        p = {
            "tipo_valvula": "ESFERA", "funcao": "BLOQUEIO", "nbr": False,
            "dispositivo_antiestatico": True, "tipo_montagem": "FLUTUANTE",
            "norma": "MSS SP72", "diametro": '2"', "classe": "300",
            "tipo_extremidade": "FLANGE RF",
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                 content_type="application/json")

    def test_base_aceita(self):
        resp = self._post()
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_butt_welding_aceito(self):
        resp = self._post(tipo_extremidade="BUTT-WELDING 40")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_socket_welding_rejeitado(self):
        resp = self._post(tipo_extremidade="SOCKET-WELDING", diametro='1"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_rosca_rejeitada(self):
        resp = self._post(tipo_extremidade="ROSCA NPT", diametro='1"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_wafer_rejeitado(self):
        resp = self._post(tipo_extremidade="Wafer")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_diametro_36_aceito(self):
        resp = self._post(diametro='36"', tipo_montagem="TRUNNION")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_diametro_acima_36_rejeitado(self):
        resp = self._post(diametro='38"', tipo_montagem="TRUNNION")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_lug_rejeitado(self):
        resp = self._post(tipo_extremidade="LUG")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_gray_loc_rejeitado(self):
        resp = self._post(tipo_extremidade="GRAY LOC HUB")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    # ── 4.4: antiestatico e' opcional ──
    def test_sem_antiestatico_aceito(self):
        resp = self._post(dispositivo_antiestatico=False)
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_outra_norma_nao_restringe(self):
        """Class 600 e' rejeitada pela API 608 nessa extremidade, mas passa com outra
        norma de Esfera cuja propria regra aceita (ISO 17292, sem teto de classe na
        socket-welding)."""
        resp = self._post(norma="ISO 17292", classe="600",
                          tipo_extremidade="SOCKET-WELDING", diametro='1"')
        self.assertEqual(resp.status_code, 200, resp.content)


class Nbr14788EscopoTest(EspecialMixin, TestCase):
    """NBR 14788 (Objetivo/Secoes 1, 5, 6, so' Esfera oferece a norma, baseada na
    ISO 7121:1986/API 6D:1994): extremidade roscada/flangeada/solda de topo (sem
    Socket-Welding/Niple/Wafer/Lug/Gray Loc Hub); classe so' PN 10/16/20/25/40/50/100
    (sem Class ASME); diametro DN 10-500 -> teto 20" (DN 500). 8.6/8.1.3.6
    (antiestatico/dreno) sao "quando especificado" -> opcionais, nao travam."""

    def _post(self, **kw):
        p = {
            "tipo_valvula": "ESFERA", "funcao": "BLOQUEIO", "nbr": False,
            "dispositivo_antiestatico": True, "tipo_montagem": "FLUTUANTE",
            "norma": "NBR 14788", "diametro": '2"', "classe": "PN 40",
            "tipo_extremidade": "FLANGE RF",
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_base_aceita(self):
        resp = self._post()
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── classe (Secoes 5/6): so' serie ISO PN ──
    def test_classe_pn100_aceita(self):
        resp = self._post(classe="PN 100")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe_ansi_rejeitada(self):
        resp = self._post(classe="150")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_classe_pn_fora_do_escopo_rejeitada(self):
        resp = self._post(classe="PN 150")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    # ── extremidade (Objetivo: roscada, flangeada ou soldada) ──
    def test_rosca_aceita(self):
        resp = self._post(tipo_extremidade="ROSCA NPT", diametro='1"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_butt_welding_aceita(self):
        resp = self._post(tipo_extremidade="BUTT-WELDING 40")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_socket_welding_rejeitada(self):
        resp = self._post(tipo_extremidade="SOCKET-WELDING")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_wafer_rejeitada(self):
        resp = self._post(tipo_extremidade="Wafer")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_gray_loc_rejeitada(self):
        resp = self._post(tipo_extremidade="GRAY LOC HUB")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    # ── diametro (Secao 5: DN 10-500 -> teto NPS 20") ──
    def test_diametro_20_aceito(self):
        resp = self._post(diametro='20"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_diametro_acima_20_rejeitado(self):
        resp = self._post(diametro='24"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    # ── PN 20 so' em Rosca (Tabelas 6/7 nao tem coluna pra PN 20; 8.1.3.1 torna a
    # dimensao face a face obrigatoria pra Flange/Butt-Welding, so' Rosca e' isenta) ──
    def test_pn20_flange_rejeitado(self):
        resp = self._post(classe="PN 20")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_pn20_butt_welding_rejeitado(self):
        resp = self._post(classe="PN 20", tipo_extremidade="BUTT-WELDING 40")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_pn20_rosca_aceito(self):
        resp = self._post(classe="PN 20", tipo_extremidade="ROSCA NPT", diametro='1"')
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── 8.6: antiestatico e' opcional ──
    def test_sem_antiestatico_aceito(self):
        resp = self._post(dispositivo_antiestatico=False)
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_outra_norma_nao_restringe(self):
        """Classe 150 (ASME) e' rejeitada pela NBR 14788, mas passa com outra norma de
        Esfera cuja propria regra aceita Class ASME (ISO 17292)."""
        resp = self._post(norma="ISO 17292", classe="150")
        self.assertEqual(resp.status_code, 200, resp.content)


class Iso15761EscopoTest(EspecialMixin, TestCase):
    """ISO 15761 Clausula 1 (Gaveta/Globo/Retencao oferecem a norma): classes
    150/300/600/800/1500 (sem 900/2500/4500/PN). SW/Rosca/Niple so' em classe 800/1500
    (nao 150/300/600), diametro ate' 2 1/2". Flange/Butt-Welding ate' 4", mas Flange nao
    cobre classe 800 (so' Butt-Welding cobre nessa classe). So' cobre flange/BW/SW/rosca
    (sem Wafer/Lug/Gray Loc Hub)."""

    def _post(self, **kw):
        p = {
            "tipo_valvula": "GAVETA", "funcao": "BLOQUEIO", "nbr": False,
            "norma": "ISO 15761", "diametro": '2"', "classe": "300",
            "tipo_extremidade": "FLANGE RF",
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_base_aceita(self):
        self.assertEqual(self._post().status_code, 200, self._post().content)

    # ── classes ──
    def test_classes_aceitas_flange(self):
        for c in ["150", "300", "600", "1500"]:
            with self.subTest(classe=c):
                self.assertEqual(self._post(classe=c).status_code, 200, c)

    def test_classes_fora_do_escopo(self):
        for c in ["900", "2500", "4500", "PN 100"]:
            with self.subTest(classe=c):
                resp = self._post(classe=c)
                self.assertEqual(resp.status_code, 400, c)
                self.assertIn("classe", resp.json()["errors"])

    # ── classe 800: so' Butt-Welding/Socket-Welding/Rosca (Flange nao cobre) ──
    def test_classe800_flange_rejeitada(self):
        resp = self._post(classe="800")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_classe800_butt_welding_aceita(self):
        resp = self._post(classe="800", tipo_extremidade="BUTT-WELDING 40")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe800_socket_aceita(self):
        resp = self._post(classe="800", tipo_extremidade="SOCKET-WELDING", diametro='1"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe1500_flange_aceita(self):
        """Diferente da classe 800: a Clausula 1 exclui so' "flanged end Class 800"."""
        resp = self._post(classe="1500")
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── socket-welding/rosca/niple so' em classe 800/1500 ──
    def test_socket_classe_300_rejeitada(self):
        resp = self._post(tipo_extremidade="SOCKET-WELDING", diametro='1"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_rosca_classe_1500_aceita(self):
        resp = self._post(tipo_extremidade="ROSCA NPT", diametro='1"', classe="1500")
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── diametro por extremidade ──
    def test_flange_4_aceito(self):
        resp = self._post(diametro='4"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_flange_6_rejeitado(self):
        resp = self._post(diametro='6"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_socket_2_meio_aceito(self):
        resp = self._post(classe="800", tipo_extremidade="SOCKET-WELDING", diametro='2 1/2"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_socket_3_rejeitado(self):
        resp = self._post(classe="800", tipo_extremidade="SOCKET-WELDING", diametro='3"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    # ── extremidade fora da norma ──
    def test_wafer_rejeitado(self):
        resp = self._post(tipo_extremidade="Wafer")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_gray_loc_rejeitado(self):
        resp = self._post(tipo_extremidade="GRAY LOC HUB")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    # ── outros tipos que oferecem a norma ──
    def test_globo_aceita(self):
        resp = self._post(tipo_valvula="GLOBO", classe="800",
                          tipo_extremidade="SOCKET-WELDING", diametro='1"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_retencao_aceita(self):
        resp = self._post(tipo_valvula="RETENCAO", tipo_passagem="PLENA")
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── 5.5.1: bonnet por 1 de 4 metodos; union nut (Roscado) so' ate' classe 800 ──
    def test_roscado_classe_800_aceito(self):
        resp = self._post(classe="800", tipo_extremidade="BUTT-WELDING 40",
                          juncao_corpo_castelo="ROSCADO")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_roscado_classe_1500_rejeitado(self):
        resp = self._post(classe="1500", juncao_corpo_castelo="ROSCADO")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("juncao_corpo_castelo", resp.json()["errors"])

    def test_soldado_classe_1500_aceito(self):
        """Welding e' um dos 4 metodos de 5.5.1, sem limite de classe (diferente do
        union nut/Roscado)."""
        resp = self._post(classe="1500", juncao_corpo_castelo="SOLDADO")
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── vedacao nao pode ser Pressure Seal (nao e' um dos 4 metodos de 5.5.1) ──
    def test_pressure_seal_rejeitado(self):
        resp = self._post(vedacoes=[{"vedacao_junta": "PRESSURE SEAL"}])
        self.assertEqual(resp.status_code, 400)
        self.assertIn("vedacoes", resp.json()["errors"])

    def test_castelo_soldado_aceito(self):
        """Welding e' um dos 4 metodos de 5.5.1 — diferente do Pressure Seal."""
        resp = self._post(vedacoes=[{"vedacao_junta": "CASTELO SOLDADO"}])
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_outra_norma_nao_restringe(self):
        resp = self._post(norma="API 602", tipo_extremidade="SOCKET-WELDING",
                          diametro='1"', classe="800")
        self.assertEqual(resp.status_code, 200, resp.content)


class AsmeB1634EscopoTest(EspecialMixin, TestCase):
    """ASME B16.34 2.1.1: rating designado por Class 150/300/600/900/1500/2500/4500
    (sem PN, 125 ou PMT). (b) Class 4500 so' em extremidade de solda.
    (d) Rosca e Socket-Welding acima de NPS 2 1/2 estao fora do escopo."""

    def _post(self, **kw):
        p = {
            "tipo_valvula": "GAVETA", "funcao": "BLOQUEIO", "nbr": False,
            "norma": "ASME B16.34", "diametro": '1"', "classe": "1500",
            "tipo_extremidade": "SOCKET-WELDING",
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_base_aceita(self):
        self.assertEqual(self._post().status_code, 200, self._post().content)

    # ── 2.1.1: designacao de classe ──
    def test_classe_pn_rejeitada(self):
        resp = self._post(classe="PN 40")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_classe_pmt_rejeitada(self):
        resp = self._post(tipo_valvula="BORBOLETA", classe="PMT", classe_pmt="10 bar",
                          tipo_extremidade="WAFER", diametro='6"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_classe_125_rejeitada(self):
        resp = self._post(tipo_valvula="BORBOLETA", classe="125",
                          tipo_extremidade="WAFER", diametro='6"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_classe_800_rejeitada(self):
        """2.1.1 nao lista Class 800: e' designacao de forjado (API 602/ISO 15761)."""
        resp = self._post(classe="800")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    # ── 2.1.1 (b): Class 4500 so' welding-end ──
    def test_4500_flange_rejeitado(self):
        resp = self._post(classe="4500", tipo_extremidade="FLANGE RF", diametro='4"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_4500_butt_welding_aceito(self):
        resp = self._post(classe="4500", tipo_extremidade="BUTT-WELDING 80", diametro='4"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_4500_socket_aceito(self):
        resp = self._post(classe="4500", tipo_extremidade="SOCKET-WELDING", diametro='1"')
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── 2.1.1 (d): rosca / socket ate' NPS 2 1/2 ──
    def test_socket_acima_de_2_meio_rejeitado(self):
        resp = self._post(diametro='4"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_socket_2_meio_aceito(self):
        resp = self._post(diametro='2 1/2"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_rosca_acima_de_2_meio_rejeitada(self):
        resp = self._post(tipo_valvula="ESFERA", tipo_extremidade="ROSCA NPT",
                          diametro='4"', classe="150", tipo_montagem="FLUTUANTE")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_butt_welding_grande_aceito(self):
        """(d) so' restringe rosca e socket — butt-welding nao tem esse teto."""
        resp = self._post(tipo_extremidade="BUTT-WELDING 80", diametro='16"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_outra_norma_nao_restringe(self):
        resp = self._post(norma="API 602", tipo_extremidade="BUTT-WELDING 80", diametro='4"')
        self.assertEqual(resp.status_code, 200, resp.content)


class Api600EscopoTest(EspecialMixin, TestCase):
    """API 600 Secao 1 (so' Gaveta oferece a norma): bonnet aparafusado ("bolted
    bonnet" e' caracteristica definidora do escopo); extremidade so' Flange ou
    Butt-Welding; classe 150/300/600/900/1500/2500 (sem 800/PN); diametro DN 25-1050
    (NPS 1-42), com buraco no NPS 22 (a norma pula de 20" pra 24")."""

    def _post(self, **kw):
        p = {
            "tipo_valvula": "GAVETA", "funcao": "BLOQUEIO", "nbr": False,
            "norma": "API 600", "diametro": '2"', "classe": "300",
            "tipo_extremidade": "FLANGE RF", "juncao_corpo_castelo": "APARAFUSADO",
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_base_aceita(self):
        self.assertEqual(self._post().status_code, 200, self._post().content)

    # ── bonnet aparafusado: única opção do escopo -> força, não rejeita ──
    def test_juncao_soldado_forcada_para_aparafusado(self):
        resp = self._post(juncao_corpo_castelo="SOLDADO")
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertEqual(v.juncao_corpo_castelo, "APARAFUSADO")

    def test_juncao_roscado_forcada_para_aparafusado(self):
        resp = self._post(juncao_corpo_castelo="ROSCADO")
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertEqual(v.juncao_corpo_castelo, "APARAFUSADO")

    # ── extremidade so' flange/butt-welding ──
    def test_butt_welding_aceito(self):
        resp = self._post(tipo_extremidade="BUTT-WELDING 40")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_socket_welding_rejeitado(self):
        resp = self._post(tipo_extremidade="SOCKET-WELDING", diametro='1"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_rosca_rejeitada(self):
        resp = self._post(tipo_extremidade="ROSCA NPT", diametro='1"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_wafer_rejeitado(self):
        resp = self._post(tipo_extremidade="Wafer")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    # ── 5.5.11: vedação não pode ser Castelo Soldado (bonnet soldado != aparafusado) ──
    def test_castelo_soldado_rejeitado(self):
        resp = self._post(vedacoes=[{"vedacao_junta": "CASTELO SOLDADO"}])
        self.assertEqual(resp.status_code, 400)
        self.assertIn("vedacoes", resp.json()["errors"])

    def test_pressure_seal_aceito(self):
        resp = self._post(vedacoes=[{"vedacao_junta": "PRESSURE SEAL"}])
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_castelo_soldado_via_campo_legado_rejeitado(self):
        """Frontend manda o valor em vedacao_junta, mas a trava le com fallback pra
        vedacao_corpo_tampa (dados antigos)."""
        resp = self._post(vedacoes=[{"vedacao_corpo_tampa": "CASTELO SOLDADO"}])
        self.assertEqual(resp.status_code, 400)
        self.assertIn("vedacoes", resp.json()["errors"])

    # ── classe: 150-2500, sem 800/PN ──
    def test_classes_aceitas(self):
        for c in ["150", "300", "600", "900", "1500", "2500"]:
            with self.subTest(classe=c):
                self.assertEqual(self._post(classe=c).status_code, 200, c)

    def test_classe_800_rejeitada(self):
        resp = self._post(classe="800")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_classe_pn_rejeitada(self):
        resp = self._post(classe="PN 100")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    # ── diametro: DN 25-1050 (NPS 1-42), buraco no NPS 22 ──
    def test_diametros_aceitos(self):
        for d in ['1"', '4"', '20"', '24"', '42"']:
            with self.subTest(diametro=d):
                self.assertEqual(self._post(diametro=d).status_code, 200, d)

    def test_diametro_meia_polegada_rejeitado(self):
        resp = self._post(diametro='1/2"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_diametro_22_rejeitado(self):
        """A norma pula de NPS 20 pra NPS 24 — NPS 22 nao existe na Tabela 1/5."""
        resp = self._post(diametro='22"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_diametro_acima_de_42_rejeitado(self):
        resp = self._post(diametro='48"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_outra_norma_nao_restringe(self):
        resp = self._post(norma="API 602", juncao_corpo_castelo="SOLDADO", diametro='1/2"')
        self.assertEqual(resp.status_code, 200, resp.content)


class Iso10434EscopoTest(EspecialMixin, TestCase):
    """ISO 10434 Secao 1 (so' Gaveta oferece a norma): versao ISO/EN da API 600 — mesmo
    bonnet aparafusado forcado, extremidade so' Flange/Butt-Welding, classe 150-2500 sem
    800/PN. Diametro menor que a API 600 (DN 25-600, NPS 1-24, sem 26"-42"), com o mesmo
    buraco no NPS 22. Vedacao nao pode ser Castelo Soldado NEM Pressure Seal (diferente
    da API 600 — a ISO 10434 nao tem clausula de bonnet pressure-seal, so' flange+gasket)."""

    def _post(self, **kw):
        p = {
            "tipo_valvula": "GAVETA", "funcao": "BLOQUEIO", "nbr": False,
            "norma": "ISO 10434", "diametro": '2"', "classe": "300",
            "tipo_extremidade": "FLANGE RF", "juncao_corpo_castelo": "APARAFUSADO",
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_base_aceita(self):
        self.assertEqual(self._post().status_code, 200, self._post().content)

    # ── bonnet aparafusado: unica opcao do escopo -> forca, nao rejeita ──
    def test_juncao_soldado_forcada_para_aparafusado(self):
        resp = self._post(juncao_corpo_castelo="SOLDADO")
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertEqual(v.juncao_corpo_castelo, "APARAFUSADO")

    # ── extremidade so' flange/butt-welding ──
    def test_butt_welding_aceito(self):
        resp = self._post(tipo_extremidade="BUTT-WELDING 40")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_socket_welding_rejeitado(self):
        resp = self._post(tipo_extremidade="SOCKET-WELDING", diametro='1"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_wafer_rejeitado(self):
        resp = self._post(tipo_extremidade="Wafer")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    # ── vedacao: nem Castelo Soldado nem Pressure Seal (diferente da API 600) ──
    def test_castelo_soldado_rejeitado(self):
        resp = self._post(vedacoes=[{"vedacao_junta": "CASTELO SOLDADO"}])
        self.assertEqual(resp.status_code, 400)
        self.assertIn("vedacoes", resp.json()["errors"])

    def test_pressure_seal_rejeitado(self):
        """Diferente da API 600 (5.5.11 permite): ISO 10434 nao tem opcao pressure-seal."""
        resp = self._post(vedacoes=[{"vedacao_junta": "PRESSURE SEAL"}])
        self.assertEqual(resp.status_code, 400)
        self.assertIn("vedacoes", resp.json()["errors"])

    def test_junta_espiralada_aceita(self):
        resp = self._post(vedacoes=[{"vedacao_junta": "JUNTA ESPIRALADA"}])
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_rtj_aceita(self):
        resp = self._post(vedacoes=[{"vedacao_junta": "RTJ (FJA)"}])
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── classe: 150-2500, sem 800/PN ──
    def test_classes_aceitas(self):
        for c in ["150", "300", "600", "900", "1500", "2500"]:
            with self.subTest(classe=c):
                self.assertEqual(self._post(classe=c).status_code, 200, c)

    def test_classe_800_rejeitada(self):
        resp = self._post(classe="800")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_classe_pn_rejeitada(self):
        resp = self._post(classe="PN 100")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    # ── diametro: DN 25-600 (NPS 1-24), buraco no NPS 22, teto menor que a API 600 ──
    def test_diametros_aceitos(self):
        for d in ['1"', '4"', '20"', '24"']:
            with self.subTest(diametro=d):
                self.assertEqual(self._post(diametro=d).status_code, 200, d)

    def test_diametro_meia_polegada_rejeitado(self):
        resp = self._post(diametro='1/2"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_diametro_22_rejeitado(self):
        resp = self._post(diametro='22"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_diametro_acima_de_24_rejeitado(self):
        """Diferente da API 600 (teto 42"): a ISO 10434 para em NPS 24."""
        resp = self._post(diametro='30"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_outra_norma_nao_restringe(self):
        """ISO 14313 so' restringe classe (7.2) — nao opina sobre juncao/vedacao, entao
        serve de placeholder neutro (API 602 e ISO 15761 agora tem a mesma regra de
        5.5.1 desta norma e rejeitariam Pressure Seal tambem)."""
        resp = self._post(norma="ISO 14313", juncao_corpo_castelo="SOLDADO", diametro='1/2"',
                          vedacoes=[{"vedacao_junta": "PRESSURE SEAL"}])
        self.assertEqual(resp.status_code, 200, resp.content)


class Api602EscopoTest(EspecialMixin, TestCase):
    """API 602 Secao 1 (Gaveta/Globo/Retencao oferecem a norma): classes 150/300/600/
    800/1500 (sem 900/2500/4500/PN — diferente da API 600/ISO 10434, aqui o 800 ENTRA:
    e' a norma-base do 800). SW/Rosca/Niple so' em classe 800/1500 (nao 150/300/600),
    diametro ate' 2 1/2". Flange/Butt-Welding ate' 4", mas Flange nao cobre classe 800
    (5.4.4.1: "does not provide for flanged ends for class 800 valves" — so' Butt-Welding
    cobre nessa classe). Juncao Roscado (union nut, 5.5.1) so' ate' classe 800. Vedacao
    nao pode ser Pressure Seal (nao e' um dos 4 metodos de juncao corpo/castelo de 5.5.1)."""

    def _post(self, **kw):
        p = {
            "tipo_valvula": "GAVETA", "funcao": "BLOQUEIO", "nbr": False,
            "norma": "API 602", "diametro": '2"', "classe": "300",
            "tipo_extremidade": "FLANGE RF",
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_base_aceita(self):
        self.assertEqual(self._post().status_code, 200, self._post().content)

    # ── classes ──
    def test_classes_aceitas_flange(self):
        for c in ["150", "300", "600", "1500"]:
            with self.subTest(classe=c):
                self.assertEqual(self._post(classe=c).status_code, 200, c)

    def test_classes_fora_do_escopo(self):
        for c in ["900", "2500", "4500", "PN 100"]:
            with self.subTest(classe=c):
                resp = self._post(classe=c)
                self.assertEqual(resp.status_code, 400, c)
                self.assertIn("classe", resp.json()["errors"])

    # ── classe 800: so' Butt-Welding/Socket-Welding/Rosca (Flange nao cobre) ──
    def test_classe800_flange_rejeitada(self):
        resp = self._post(classe="800")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_classe800_butt_welding_aceita(self):
        resp = self._post(classe="800", tipo_extremidade="BUTT-WELDING 40")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe800_socket_aceita(self):
        resp = self._post(classe="800", tipo_extremidade="SOCKET-WELDING", diametro='1"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe1500_flange_aceita(self):
        """Diferente da classe 800: a Secao 1 exclui so' "flanged end class 800"."""
        resp = self._post(classe="1500")
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── socket-welding/rosca/niple so' em classe 800/1500 ──
    def test_socket_classe_300_rejeitada(self):
        resp = self._post(tipo_extremidade="SOCKET-WELDING", diametro='1"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_rosca_classe_1500_aceita(self):
        resp = self._post(tipo_extremidade="ROSCA NPT", diametro='1"', classe="1500")
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── diametro por extremidade ──
    def test_flange_4_aceito(self):
        resp = self._post(diametro='4"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_flange_6_rejeitado(self):
        resp = self._post(diametro='6"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_socket_2_meio_aceito(self):
        resp = self._post(classe="800", tipo_extremidade="SOCKET-WELDING", diametro='2 1/2"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_socket_3_rejeitado(self):
        resp = self._post(classe="800", tipo_extremidade="SOCKET-WELDING", diametro='3"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    # ── extremidade fora da norma ──
    def test_wafer_rejeitado(self):
        resp = self._post(tipo_extremidade="Wafer")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_gray_loc_rejeitado(self):
        resp = self._post(tipo_extremidade="GRAY LOC HUB")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    # ── juncao corpo/castelo (5.5.1): Roscado (union nut) so' ate' classe 800 ──
    def test_juncao_roscado_classe_800_aceita(self):
        resp = self._post(classe="800", tipo_extremidade="SOCKET-WELDING", diametro='1"',
                          juncao_corpo_castelo="ROSCADO")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_juncao_roscado_classe_1500_rejeitada(self):
        resp = self._post(classe="1500", juncao_corpo_castelo="ROSCADO")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("juncao_corpo_castelo", resp.json()["errors"])

    def test_juncao_soldado_classe_1500_aceita(self):
        """So' o Roscado (union nut) tem teto de classe — Soldado nao."""
        resp = self._post(classe="1500", juncao_corpo_castelo="SOLDADO")
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── vedacao: nao pode ser Pressure Seal (nao e' um dos 4 metodos de 5.5.1) ──
    def test_pressure_seal_rejeitado(self):
        resp = self._post(vedacoes=[{"vedacao_junta": "PRESSURE SEAL"}])
        self.assertEqual(resp.status_code, 400)
        self.assertIn("vedacoes", resp.json()["errors"])

    def test_castelo_soldado_aceito(self):
        """Diferente da API 600/ISO 10434: a API 602 5.5.1 lista "welding" como um dos
        4 metodos validos de juncao corpo/castelo — Castelo Soldado nao e' rejeitado."""
        resp = self._post(vedacoes=[{"vedacao_junta": "CASTELO SOLDADO"}])
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_junta_espiralada_aceita(self):
        resp = self._post(vedacoes=[{"vedacao_junta": "JUNTA ESPIRALADA"}])
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── outros tipos que oferecem a norma ──
    def test_globo_aceita(self):
        resp = self._post(tipo_valvula="GLOBO", classe="800",
                          tipo_extremidade="SOCKET-WELDING", diametro='1"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_retencao_aceita(self):
        resp = self._post(tipo_valvula="RETENCAO", tipo_passagem="PLENA")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_outra_norma_nao_restringe(self):
        resp = self._post(norma="ISO 15761", tipo_extremidade="SOCKET-WELDING",
                          diametro='1"', classe="800")
        self.assertEqual(resp.status_code, 200, resp.content)


class Bs1868EscopoTest(EspecialMixin, TestCase):
    """BS 1868 (Clausulas 1, 4, 6, 9.3): so' Retencao oferece a norma. Extremidade so'
    Flange ou Butt-Welding (nao cobre Socket-Welding/Rosca/Niple/Wafer/Lug/Gray Loc Hub).
    Classe 150/300/600/900/1500/2500 (sem 800 nem PN; Class 400 da Clausula 4 nao existe
    como opcao no modelo). Diametro 1/2"-24", com buraco no 22" (Clausula 6 pula de 20"
    pra 24", igual API 600/ISO 10434). 9.3: body-to-cover connection e'
    male-and-female/tongue-and-groove/ring-joint — vedacao nao pode ser Castelo Soldado
    nem Pressure Seal."""

    def _post(self, **kw):
        p = {
            "tipo_valvula": "RETENCAO", "funcao": "BLOQUEIO", "nbr": False,
            "norma": "BS 1868", "diametro": '2"', "classe": "300",
            "tipo_extremidade": "FLANGE RF", "tipo_passagem": "PLENA",
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_base_aceita(self):
        resp = self._post()
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── classes ──
    def test_classes_aceitas(self):
        for c in ["150", "300", "400", "600", "900", "1500", "2500"]:
            with self.subTest(classe=c):
                self.assertEqual(self._post(classe=c).status_code, 200, c)

    def test_classe_800_rejeitada(self):
        resp = self._post(classe="800")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_classe_pn_rejeitada(self):
        resp = self._post(classe="PN 100")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_classe_400_rejeitada_em_api6d(self):
        """400 foi adicionada ao CLASSES_RETENCAO_GLOBO especificamente pra BS 1868 —
        a API 6D (blacklist PN/400/800/4500) nao cobre essa designacao, regressao pra
        confirmar que a classe nova nao vaza pra outra norma de Retencao."""
        resp = self._post(norma="API 6D", classe="400", qsl="QSL1")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_classe_400_rejeitada_em_b1634(self):
        """Mesma regressao pra ASME B16.34 (blacklist PN/125/400/800/PMT)."""
        resp = self._post(norma="ASME B16.34", classe="400")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    # ── extremidade: so' Flange/Butt-Welding ──
    def test_butt_welding_aceita(self):
        resp = self._post(tipo_extremidade="BUTT-WELDING 40")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_socket_welding_rejeitada(self):
        resp = self._post(tipo_extremidade="SOCKET-WELDING", diametro='1"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_rosca_rejeitada(self):
        resp = self._post(tipo_extremidade="ROSCA NPT", diametro='1"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_wafer_rejeitada(self):
        resp = self._post(tipo_extremidade="Wafer")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_gray_loc_rejeitada(self):
        resp = self._post(tipo_extremidade="GRAY LOC HUB")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_lug_rejeitada(self):
        resp = self._post(tipo_extremidade="LUG")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    # ── diametro: 1/2" a 24", com buraco no 22" ──
    def test_diametro_24_aceito(self):
        resp = self._post(diametro='24"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_diametro_acima_24_rejeitado(self):
        resp = self._post(diametro='26"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_diametro_22_rejeitado(self):
        """Clausula 6 pula de 20" pra 24" — 22" nao existe na norma."""
        resp = self._post(diametro='22"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    # ── vedacao (9.3): nao pode ser Castelo Soldado nem Pressure Seal ──
    def test_castelo_soldado_rejeitado(self):
        resp = self._post(vedacoes=[{"vedacao_junta": "CASTELO SOLDADO"}])
        self.assertEqual(resp.status_code, 400)
        self.assertIn("vedacoes", resp.json()["errors"])

    def test_pressure_seal_rejeitado(self):
        resp = self._post(vedacoes=[{"vedacao_junta": "PRESSURE SEAL"}])
        self.assertEqual(resp.status_code, 400)
        self.assertIn("vedacoes", resp.json()["errors"])

    def test_junta_espiralada_aceita(self):
        resp = self._post(vedacoes=[{"vedacao_junta": "JUNTA ESPIRALADA"}])
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_rtj_aceita(self):
        resp = self._post(vedacoes=[{"vedacao_junta": "RTJ (FJA)"}])
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_outra_norma_nao_restringe(self):
        resp = self._post(norma="ISO 15761", tipo_extremidade="SOCKET-WELDING",
                          diametro='1"', classe="800")
        self.assertEqual(resp.status_code, 200, resp.content)


class Api594EscopoTest(EspecialMixin, TestCase):
    """API 594 Secao 1 (so' Retencao oferece a norma): extremidade so' Flange/Lug/Wafer/
    Butt-Welding (nao cobre Socket-Welding/Rosca/Niple/Gray Loc Hub). Classe 150/300/600/
    900/1500/2500 (sem 800 nem PN; 125/250 de ferro fundido nao existem no modelo).
    Diametro minimo NPS 2 sempre. Teto por classe/extremidade: 150/300 -> NPS 48 (Wafer/
    Lug/Flange) ou 24 (Butt-Welding, Type B); 600 -> NPS 42 ou 24; 900/1500 -> NPS 24 pra
    qualquer extremidade (Type A e B coincidem); 2500 -> NPS 12. 5.1.14/6.3: vedacao nao
    pode ser Castelo Soldado nem Pressure Seal (mesmo caso da BS 1868)."""

    def _post(self, **kw):
        p = {
            "tipo_valvula": "RETENCAO", "funcao": "BLOQUEIO", "nbr": False,
            "norma": "API 594", "diametro": '4"', "classe": "300",
            "tipo_extremidade": "FLANGE RF", "tipo_passagem": "PLENA",
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_base_aceita(self):
        resp = self._post()
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── classes ──
    def test_classes_aceitas(self):
        for c in ["150", "300", "600", "900", "1500", "2500"]:
            with self.subTest(classe=c):
                self.assertEqual(self._post(classe=c).status_code, 200, c)

    def test_classe_800_rejeitada(self):
        resp = self._post(classe="800")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_classe_400_rejeitada(self):
        """Diferente da BS 1868: a API 594 nunca lista Class 400."""
        resp = self._post(classe="400")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_classe_pn_rejeitada(self):
        resp = self._post(classe="PN 100")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    # ── extremidade: Flange/Lug/Wafer/Butt-Welding ──
    def test_wafer_aceita(self):
        resp = self._post(tipo_extremidade="Wafer")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_lug_aceita(self):
        resp = self._post(tipo_extremidade="LUG")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_butt_welding_aceita(self):
        resp = self._post(tipo_extremidade="BUTT-WELDING 40")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_socket_welding_rejeitada(self):
        resp = self._post(tipo_extremidade="SOCKET-WELDING", diametro='2"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_rosca_rejeitada(self):
        resp = self._post(tipo_extremidade="ROSCA NPT", diametro='2"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_gray_loc_rejeitada(self):
        resp = self._post(tipo_extremidade="GRAY LOC HUB")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    # ── diametro minimo NPS 2 ──
    def test_diametro_abaixo_de_2_rejeitado(self):
        resp = self._post(diametro='1 1/2"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    # ── teto por classe/extremidade ──
    def test_classe150_wafer_42_aceito(self):
        resp = self._post(classe="150", tipo_extremidade="Wafer", diametro='42"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe150_wafer_48_aceito(self):
        """DIAMETROS_RETENCAO estendido ate' 48" (2026-07-17) pra bater com o teto real
        do Type A nas classes 150/300 — antes disso 48" nem existia como opcao."""
        resp = self._post(classe="150", tipo_extremidade="Wafer", diametro='48"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe150_butt_welding_48_rejeitado(self):
        """48" passa no Type A (Wafer/Lug/Flange), mas Butt-Welding e' sempre Type B —
        teto continua 24"."""
        resp = self._post(classe="150", tipo_extremidade="BUTT-WELDING 40", diametro='48"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_classe150_butt_welding_24_aceito(self):
        resp = self._post(classe="150", tipo_extremidade="BUTT-WELDING 40", diametro='24"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe150_butt_welding_acima_24_rejeitado(self):
        resp = self._post(classe="150", tipo_extremidade="BUTT-WELDING 40", diametro='26"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_classe600_flange_42_aceito(self):
        resp = self._post(classe="600", diametro='42"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe600_butt_welding_acima_24_rejeitado(self):
        resp = self._post(classe="600", tipo_extremidade="BUTT-WELDING 40", diametro='26"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_classe900_24_aceito(self):
        resp = self._post(classe="900", diametro='24"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe900_acima_24_rejeitado(self):
        resp = self._post(classe="900", diametro='26"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_classe900_butt_welding_acima_24_rejeitado(self):
        """900 e' igual pros dois tipos — nao ha' teto maior pra Wafer/Lug/Flange aqui."""
        resp = self._post(classe="900", tipo_extremidade="BUTT-WELDING 40", diametro='26"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_classe2500_12_aceito(self):
        resp = self._post(classe="2500", diametro='12"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe2500_acima_12_rejeitado(self):
        resp = self._post(classe="2500", diametro='14"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    # ── categoria da junta (Materiais -> JUNTA): so' Tipo B (5.1.14, bolted cover) nao
    # pode ser Castelo Soldado nem Pressure Seal. Tipo A nao tem esse requisito no escopo.
    def test_castelo_soldado_rejeitado_tipo_b(self):
        resp = self._post(categoria_594="TIPO B", materiais=[{"tipo_material": "JUNTA", "material": "CASTELO SOLDADO"}])
        self.assertEqual(resp.status_code, 400)
        self.assertIn("materiais", resp.json()["errors"])

    def test_pressure_seal_rejeitado_tipo_b(self):
        resp = self._post(categoria_594="TIPO B", materiais=[{"tipo_material": "JUNTA", "material": "PRESSURE SEAL"}])
        self.assertEqual(resp.status_code, 400)
        self.assertIn("materiais", resp.json()["errors"])

    def test_junta_espiralada_aceita_tipo_b(self):
        resp = self._post(categoria_594="TIPO B", materiais=[{"tipo_material": "JUNTA", "material": "JUNTA ESPIRALADA"}])
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_castelo_soldado_aceito_tipo_a(self):
        """Tipo A (wafer/lug/duplo-flangeado) nao tem bolted cover no escopo — 5.1.14 e'
        exclusivo do Tipo B, entao a restricao de junta nao se aplica aqui."""
        resp = self._post(categoria_594="TIPO A", tipo_extremidade="Wafer",
                           materiais=[{"tipo_material": "JUNTA", "material": "CASTELO SOLDADO"}])
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_outra_norma_nao_restringe(self):
        resp = self._post(norma="BS 1868", diametro='1"')
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── categoria_594 (Tipo A/Tipo B, 5.1.3) ──
    def test_tipo_a_butt_welding_rejeitado(self):
        """5.1.3: Tipo A e' wafer/lug/duplo-flangeado — Butt-Welding so' existe no Tipo B."""
        resp = self._post(categoria_594="TIPO A", tipo_extremidade="BUTT-WELDING 40")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_tipo_a_wafer_aceito(self):
        resp = self._post(categoria_594="TIPO A", tipo_extremidade="Wafer")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_tipo_b_wafer_rejeitado(self):
        """5.1.3: Tipo B e' bolted cover, flange ou butt-welding — nao cobre Wafer/Lug."""
        resp = self._post(categoria_594="TIPO B", tipo_extremidade="Wafer")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_tipo_b_lug_rejeitado(self):
        resp = self._post(categoria_594="TIPO B", tipo_extremidade="LUG")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_tipo_b_flange_aceito(self):
        resp = self._post(categoria_594="TIPO B", tipo_extremidade="FLANGE RF")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_tipo_b_butt_welding_aceito(self):
        resp = self._post(categoria_594="TIPO B", tipo_extremidade="BUTT-WELDING 40")
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── teto por classe/tipo (Secao 1) ──
    def test_tipo_a_classe150_flange_48_aceito(self):
        """Tipo A classe 150/300: DN 50-1200/NPS 2-48 (Secao 1), independente da
        extremidade ser wafer/lug/flange."""
        resp = self._post(categoria_594="TIPO A", classe="150", tipo_extremidade="FLANGE RF", diametro='48"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_tipo_a_classe900_acima_24_rejeitado(self):
        """Tipo A classe 900/1500: DN 50-600/NPS 2-24."""
        resp = self._post(categoria_594="TIPO A", classe="900", tipo_extremidade="Wafer", diametro='26"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_tipo_b_classe150_flange_24_aceito(self):
        """Tipo B classe 150-1500: DN 50-600/NPS 2-24, mesmo teto pra Flange ou
        Butt-Welding (a Secao 1 nao diferencia dimensao por extremidade no Tipo B)."""
        resp = self._post(categoria_594="TIPO B", classe="150", tipo_extremidade="FLANGE RF", diametro='24"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_tipo_b_classe150_flange_acima_24_rejeitado(self):
        """Diferente do Tipo A (que aceita ate' 48" na classe 150) — Tipo B para' em 24"
        mesmo com extremidade Flange."""
        resp = self._post(categoria_594="TIPO B", classe="150", tipo_extremidade="FLANGE RF", diametro='26"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_tipo_b_classe2500_12_aceito(self):
        resp = self._post(categoria_594="TIPO B", classe="2500", tipo_extremidade="FLANGE RF", diametro='12"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_tipo_b_classe2500_acima_12_rejeitado(self):
        resp = self._post(categoria_594="TIPO B", classe="2500", tipo_extremidade="FLANGE RF", diametro='14"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_sem_categoria_mantem_comportamento_legado(self):
        """categoria_594 em branco (dado legado): extremidade aceita as 4 opcoes e o
        teto usa a coluna B (Butt-Welding) ou a mais permissiva — mesmo comportamento
        de antes do campo existir."""
        resp = self._post(classe="150", tipo_extremidade="Wafer", diametro='48"')
        self.assertEqual(resp.status_code, 200, resp.content)


class Bs1873EscopoTest(EspecialMixin, TestCase):
    """BS 1873 (Clausulas 1, 4, 6, 9.3, Apendice A): so' Globo oferece a norma.
    Extremidade so' Flange ou Butt-Welding. Classe 150/300/600/900/1500/2500 (sem 800
    nem PN; Class 400 existe no CLASSES_RETENCAO_GLOBO — adicionada p/ BS 1868 — mas
    a BS 1873 nao a cobre, whitelist bloqueia normalmente). Diametro por classe (Apendice A):
    150 ate' 16"; 300/600/2500 ate' 12"; 1500 ate' 14"; 900 de 3" a 14" (unica com piso,
    a Tabela 7 comeca em DN 80/NPS 3). 9.3: body-to-bonnet e' sempre flange aparafusado
    (forcado) e a vedacao nao pode ser Castelo Soldado nem Pressure Seal (so' Junta
    Espiralada ou RTJ, igual ISO 10434)."""

    def _post(self, **kw):
        p = {
            "tipo_valvula": "GLOBO", "funcao": "BLOQUEIO", "nbr": False,
            "norma": "BS 1873", "diametro": '4"', "classe": "300",
            "tipo_extremidade": "FLANGE RF",
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_base_aceita(self):
        resp = self._post()
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── classes ──
    def test_classes_aceitas(self):
        for c in ["150", "300", "600", "900", "1500", "2500"]:
            with self.subTest(classe=c):
                diam = '4"' if c == "900" else '2"'
                self.assertEqual(self._post(classe=c, diametro=diam).status_code, 200, c)

    def test_classe_800_rejeitada(self):
        resp = self._post(classe="800")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_classe_pn_rejeitada(self):
        resp = self._post(classe="PN 100")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    # ── extremidade: so' Flange/Butt-Welding ──
    def test_butt_welding_aceita(self):
        resp = self._post(tipo_extremidade="BUTT-WELDING 40")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_socket_welding_rejeitada(self):
        resp = self._post(tipo_extremidade="SOCKET-WELDING", diametro='1"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_rosca_rejeitada(self):
        resp = self._post(tipo_extremidade="ROSCA NPT", diametro='1"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_wafer_rejeitada(self):
        resp = self._post(tipo_extremidade="Wafer")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_gray_loc_rejeitada(self):
        resp = self._post(tipo_extremidade="GRAY LOC HUB")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    # ── diametro por classe (Apendice A) ──
    def test_classe150_16_aceito(self):
        resp = self._post(classe="150", diametro='16"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe150_acima_16_rejeitado(self):
        resp = self._post(classe="150", diametro='18"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_classe300_12_aceito(self):
        resp = self._post(classe="300", diametro='12"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe300_acima_12_rejeitado(self):
        resp = self._post(classe="300", diametro='14"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_classe1500_14_aceito(self):
        resp = self._post(classe="1500", diametro='14"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe1500_acima_14_rejeitado(self):
        resp = self._post(classe="1500", diametro='16"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_classe900_3_aceito(self):
        resp = self._post(classe="900", diametro='3"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe900_abaixo_de_3_rejeitado(self):
        """900 e' a unica classe com piso — a Tabela 7 comeca em DN 80 (NPS 3)."""
        resp = self._post(classe="900", diametro='2"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_classe900_14_aceito(self):
        resp = self._post(classe="900", diametro='14"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe900_acima_14_rejeitado(self):
        resp = self._post(classe="900", diametro='16"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    # ── 9.3: bonnet sempre aparafusado (forca, nao rejeita) ──
    def test_juncao_soldado_forcada_para_aparafusado(self):
        resp = self._post(juncao_corpo_castelo="SOLDADO")
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertEqual(v.juncao_corpo_castelo, "APARAFUSADO")

    # ── vedacao: nao pode ser Castelo Soldado nem Pressure Seal ──
    def test_castelo_soldado_rejeitado(self):
        resp = self._post(vedacoes=[{"vedacao_junta": "CASTELO SOLDADO"}])
        self.assertEqual(resp.status_code, 400)
        self.assertIn("vedacoes", resp.json()["errors"])

    def test_pressure_seal_rejeitado(self):
        resp = self._post(vedacoes=[{"vedacao_junta": "PRESSURE SEAL"}])
        self.assertEqual(resp.status_code, 400)
        self.assertIn("vedacoes", resp.json()["errors"])

    def test_junta_espiralada_aceita(self):
        resp = self._post(vedacoes=[{"vedacao_junta": "JUNTA ESPIRALADA"}])
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_rtj_aceita(self):
        resp = self._post(vedacoes=[{"vedacao_junta": "RTJ (FJA)"}])
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_outra_norma_nao_restringe(self):
        resp = self._post(norma="API 602", tipo_extremidade="SOCKET-WELDING",
                          diametro='1"', classe="800")
        self.assertEqual(resp.status_code, 200, resp.content)


class Api623EscopoTest(EspecialMixin, TestCase):
    """API 623 (Secao 1): so' Globo oferece a norma. "bolted bonnet, ... flanged or
    butt-welding ends" -> junc corpo/castelo sempre Aparafusado (forcado); extremidade
    so' Flange/Butt-Welding. Classe 150/300/600/900/1500/2500 (sem 800 nem PN). Diametro
    NPS 2-24 (2, 2 1/2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24 -- sem 1/2"-1 1/2", com
    buraco no 22"). 5.5.1/5.5.2: bonnet-to-body joint e' flange-and-gasket -> vedacao nao
    pode ser Castelo Soldado nem Pressure Seal (mesmo caso da ISO 10434)."""

    def _post(self, **kw):
        p = {
            "tipo_valvula": "GLOBO", "funcao": "BLOQUEIO", "nbr": False,
            "norma": "API 623", "diametro": '4"', "classe": "300",
            "tipo_extremidade": "FLANGE RF",
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_base_aceita(self):
        resp = self._post()
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── classes ──
    def test_classes_aceitas(self):
        for c in ["150", "300", "600", "900", "1500", "2500"]:
            with self.subTest(classe=c):
                self.assertEqual(self._post(classe=c).status_code, 200, c)

    def test_classe_800_rejeitada(self):
        resp = self._post(classe="800")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_classe_pn_rejeitada(self):
        resp = self._post(classe="PN 100")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    # ── extremidade: so' Flange/Butt-Welding ──
    def test_butt_welding_aceita(self):
        resp = self._post(tipo_extremidade="BUTT-WELDING 40")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_socket_welding_rejeitada(self):
        resp = self._post(tipo_extremidade="SOCKET-WELDING")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_rosca_rejeitada(self):
        resp = self._post(tipo_extremidade="ROSCA NPT")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_wafer_rejeitada(self):
        resp = self._post(tipo_extremidade="Wafer")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    def test_gray_loc_rejeitada(self):
        resp = self._post(tipo_extremidade="GRAY LOC HUB")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo_extremidade", resp.json()["errors"])

    # ── diametro: NPS 2-24, com buraco no 22" ──
    def test_diametro_2_aceito(self):
        resp = self._post(diametro='2"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_diametro_abaixo_de_2_rejeitado(self):
        resp = self._post(diametro='1 1/2"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_diametro_24_aceito(self):
        resp = self._post(diametro='24"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_diametro_acima_de_24_rejeitado(self):
        resp = self._post(diametro='26"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_diametro_22_rejeitado(self):
        resp = self._post(diametro='22"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    # ── Classe 2500 so' at NPS 12 (Tabela 1 nao tem espessura pra 2500 acima de NPS 12) ──
    def test_classe2500_12_aceito(self):
        resp = self._post(classe="2500", diametro='12"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_classe2500_acima_12_rejeitado(self):
        resp = self._post(classe="2500", diametro='14"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_classe1500_14_aceito_sem_teto_de_2500(self):
        """Classe 1500 nao tem o teto de 12" — so' a 2500 tem o buraco na Tabela 1."""
        resp = self._post(classe="1500", diametro='14"')
        self.assertEqual(resp.status_code, 200, resp.content)

    # ── Secao 1: bonnet sempre aparafusado (forca, nao rejeita) ──
    def test_juncao_soldado_forcada_para_aparafusado(self):
        resp = self._post(juncao_corpo_castelo="SOLDADO")
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(pk=resp.json()["valvula"]["id"])
        self.assertEqual(v.juncao_corpo_castelo, "APARAFUSADO")

    # ── vedacao: nao pode ser Castelo Soldado nem Pressure Seal ──
    def test_castelo_soldado_rejeitado(self):
        resp = self._post(vedacoes=[{"vedacao_junta": "CASTELO SOLDADO"}])
        self.assertEqual(resp.status_code, 400)
        self.assertIn("vedacoes", resp.json()["errors"])

    def test_pressure_seal_rejeitado(self):
        resp = self._post(vedacoes=[{"vedacao_junta": "PRESSURE SEAL"}])
        self.assertEqual(resp.status_code, 400)
        self.assertIn("vedacoes", resp.json()["errors"])

    def test_junta_espiralada_aceita(self):
        resp = self._post(vedacoes=[{"vedacao_junta": "JUNTA ESPIRALADA"}])
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_rtj_aceita(self):
        resp = self._post(vedacoes=[{"vedacao_junta": "RTJ (FJA)"}])
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_outra_norma_nao_restringe(self):
        resp = self._post(norma="API 602", tipo_extremidade="SOCKET-WELDING",
                          diametro='1"', classe="800")
        self.assertEqual(resp.status_code, 200, resp.content)


class Classe800NaoEhDeFlangeTest(EspecialMixin, TestCase):
    """Classe 800 e' designacao de valvula forjada (API 602 / ISO 15761) e so' aparece
    na coluna "Encaixe para solda" das Tabelas 1, 2 e 4 da NBR 15827. Nao existe flange
    classe 800 — a sequencia de flange e' 150/300/600/900/1500/2500."""

    CORPO = "ASTM A105"

    def _post(self, **kw):
        make_material(self.CORPO)
        p = {
            "funcao": "BLOQUEIO", "nbr": True, "diametro": '4"', "classe": "800",
            "materiais": [{"tipo_material": "CORPO_TAMPA", "material": self.CORPO},
                          {"tipo_material": "JUNTA", "material": "GRAFITE"},
                          {"tipo_material": "PARAFUSOS", "material": "ASTM A193 B7"},
                          {"tipo_material": "PORCAS", "material": "ASTM A194 2H"}],
        }
        p.update(kw)
        for m in p.get("materiais", []):
            make_material(m["material"])
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_gaveta_flange_800_rejeitada(self):
        resp = self._post(tipo_valvula="GAVETA", tipo_extremidade="FLANGE RF",
                          norma="ISO 10434")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_gaveta_flange_900_aceita(self):
        resp = self._post(tipo_valvula="GAVETA", tipo_extremidade="FLANGE RF",
                          norma="ISO 10434", classe="900")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_globo_flange_800_rejeitada(self):
        resp = self._post(tipo_valvula="GLOBO", tipo_extremidade="FLANGE RF",
                          norma="BS 1873")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_retencao_flange_800_rejeitada(self):
        resp = self._post(tipo_valvula="RETENCAO", tipo_extremidade="FLANGE RF",
                          norma="BS 1868")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_retencao_wafer_800_rejeitada(self):
        resp = self._post(tipo_valvula="RETENCAO", tipo_extremidade="Wafer",
                          norma="API 594")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_esfera_flange_800_ja_era_rejeitada(self):
        """Regressao: a regra da Esfera ja' lia a Tabela 3 certo."""
        resp = self._post(tipo_valvula="ESFERA", tipo_extremidade="FLANGE RF",
                          norma="API 6D", qsl="QSL2", tipo_montagem="TRUNNION",
                          dispositivo_antiestatico=True)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    # ── socket-weld: 800 existe, mas sem ASME B16.34 ──
    def test_gaveta_socket_800_com_b1634_rejeitada(self):
        resp = self._post(tipo_valvula="GAVETA", tipo_extremidade="SOCKET-WELDING",
                          diametro='1"', norma="ASME B16.34")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("norma", resp.json()["errors"])

    def test_gaveta_socket_800_com_iso15761_aceita(self):
        resp = self._post(tipo_valvula="GAVETA", tipo_extremidade="SOCKET-WELDING",
                          diametro='1"', norma="ISO 15761")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_gaveta_socket_1500_com_b1634_aceita(self):
        resp = self._post(tipo_valvula="GAVETA", tipo_extremidade="SOCKET-WELDING",
                          diametro='1"', classe="1500", norma="ASME B16.34")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_globo_socket_800_com_b1634_rejeitada(self):
        resp = self._post(tipo_valvula="GLOBO", tipo_extremidade="SOCKET-WELDING",
                          diametro='1"', norma="ASME B16.34")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("norma", resp.json()["errors"])

    def test_globo_socket_800_com_api602_aceita(self):
        resp = self._post(tipo_valvula="GLOBO", tipo_extremidade="SOCKET-WELDING",
                          diametro='1"', norma="API 602")
        self.assertEqual(resp.status_code, 200, resp.content)


class BorboletaApi609EscopoTest(EspecialMixin, TestCase):
    """API 609 1.3: Categoria A e' NPS 2-48, Class 125/150, so' lug e wafer.
    Categoria B e' NPS 3-48 (duplo flange longo ate' 36; curto classe 600 ate' 24).
    Escopo da norma: Classes 125-600."""

    def _post(self, **kw):
        p = {
            "tipo_valvula": "BORBOLETA", "funcao": "BLOQUEIO", "nbr": False,
            "norma": "API 609", "diametro": '4"', "classe": "150",
            "configuracao_disco": "CONCÊNTRICA", "face_a_face": "LUG",
            "categoria_borboleta": "CATEGORIA A",
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    # ── Categoria A: so' lug e wafer ──
    def test_cat_a_lug_aceito(self):
        self.assertEqual(self._post().status_code, 200, "cat A base deve passar")

    def test_cat_a_wafer_aceito(self):
        self.assertEqual(self._post(face_a_face="WAFER").status_code, 200)

    def test_cat_a_duplo_flange_rejeitado(self):
        resp = self._post(face_a_face="FLANGEADA PADRÃO LONGO")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("face_a_face", resp.json()["errors"])

    # ── Categoria B: 3"-48" mesmo sem face a face ──
    def test_cat_b_sem_faf_diametro_2_rejeitado(self):
        resp = self._post(categoria_borboleta="CATEGORIA B", classe="300",
                          face_a_face="", diametro='2"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_cat_b_sem_faf_diametro_54_rejeitado(self):
        resp = self._post(categoria_borboleta="CATEGORIA B", classe="300",
                          face_a_face="", diametro='54"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_cat_b_sem_faf_diametro_48_aceito(self):
        resp = self._post(categoria_borboleta="CATEGORIA B", classe="300",
                          face_a_face="", diametro='48"')
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_cat_b_curto_600_ate_24(self):
        resp = self._post(categoria_borboleta="CATEGORIA B", classe="600",
                          face_a_face="FLANGEADA PADRÃO CURTO", diametro='30"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    # ── Escopo de classe (pega categoria em branco) ──
    def test_sem_categoria_classe_900_rejeitada(self):
        resp = self._post(categoria_borboleta="", classe="900")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_sem_categoria_classe_300_aceita(self):
        resp = self._post(categoria_borboleta="", classe="300")
        self.assertEqual(resp.status_code, 200, resp.content)


class BorboletaTriExcRuleTest(EspecialMixin, TestCase):
    def _post(self, **kw):
        p = {
            "tipo_valvula": "BORBOLETA", "nbr": True,
            "face_a_face": "LUG", "configuracao_disco": "TRI-EXCÊNTRICA",
            "diametro": '24"', "classe": "900", "norma": "ASME B16.34",
            "materiais": [{"tipo_material": "CORPO_TAMPA", "material": "ASTM A216 WCB"}],
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_aceito(self):
        self.assertEqual(self._post().status_code, 200, "borboleta tri base deve passar")

    def test_classe_invalida(self):
        resp = self._post(classe="2500")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_diametro_invalido(self):
        resp = self._post(diametro='54"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_norma_invalida(self):
        resp = self._post(norma="MSS SP67")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("norma", resp.json()["errors"])


# ── Borboleta Categoria A: disco Concêntrica; diâmetro 2"-48"; classe 125/150/PMT ──

class BorboletaCategoriaARuleTest(EspecialMixin, TestCase):
    def _post(self, **kw):
        p = {
            "tipo_valvula": "BORBOLETA", "nbr": False,
            "categoria_borboleta": "CATEGORIA A",
            "configuracao_disco": "CONCÊNTRICA",
            "diametro": '24"', "classe": "150", "norma": "API 609",
            "materiais": [{"tipo_material": "CORPO_TAMPA", "material": "ASTM A216 WCB"}],
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_aceito(self):
        self.assertEqual(self._post().status_code, 200, "categoria A base deve passar")

    def test_classe_125_aceita(self):
        self.assertEqual(self._post(classe="125").status_code, 200)

    def test_classe_invalida(self):
        resp = self._post(classe="300")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_diametro_invalido(self):
        resp = self._post(diametro='54"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_disco_invalido(self):
        resp = self._post(configuracao_disco="BI-EXCÊNTRICA")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("configuracao_disco", resp.json()["errors"])

    def test_pmt_sem_valor(self):
        resp = self._post(classe="PMT")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe_pmt", resp.json()["errors"])

    def test_pmt_com_valor_persiste(self):
        resp = self._post(classe="PMT", classe_pmt="PMT 20 bar")
        self.assertEqual(resp.status_code, 200, resp.content)
        codigo = resp.json()["valvula"]["codigo"]
        v = Valvula.objects.get(codigo=codigo)
        self.assertEqual(v.classe, "PMT")
        self.assertEqual(v.classe_pmt, "PMT 20 bar")

    def test_classe_pmt_limpo_quando_classe_nao_pmt(self):
        resp = self._post(classe="150", classe_pmt="PMT 20 bar")
        self.assertEqual(resp.status_code, 200, resp.content)
        codigo = resp.json()["valvula"]["codigo"]
        v = Valvula.objects.get(codigo=codigo)
        self.assertEqual(v.classe_pmt, "")


# ── Borboleta + NBR + Wafer/Lug + Concêntrica + corpo A536 → PMT / API 609 ──────

class BorboletaConcA536RuleTest(EspecialMixin, TestCase):
    def _post(self, **kw):
        p = {
            "tipo_valvula": "BORBOLETA", "nbr": True,
            "face_a_face": "WAFER", "configuracao_disco": "CONCÊNTRICA",
            "diametro": '24"', "classe": "PMT", "classe_pmt": "PMT 16 bar",
            "norma": "API 609",
            "materiais": [{"tipo_material": "CORPO_TAMPA", "material": "ASTM A536 65-45-12"}],
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_aceito(self):
        self.assertEqual(self._post().status_code, 200, "cenário base deve passar")

    def test_lug_aceito(self):
        self.assertEqual(self._post(face_a_face="LUG").status_code, 200)

    def test_diametro_invalido(self):
        resp = self._post(diametro='54"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_classe_nao_pmt(self):
        resp = self._post(classe="150", classe_pmt="")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_norma_invalida(self):
        resp = self._post(norma="ASME B16.34")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("norma", resp.json()["errors"])

    def test_pmt_sem_valor(self):
        resp = self._post(classe_pmt="")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe_pmt", resp.json()["errors"])

    def test_corpo_diferente_nao_aplica(self):
        """Corpo fora de A536 → regra não aplica; classe 150 deve passar."""
        resp = self._post(classe="150", classe_pmt="",
                          materiais=[{"tipo_material": "CORPO_TAMPA", "material": "ASTM A216 WCB"}])
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_persiste(self):
        resp = self._post()
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Valvula.objects.get(codigo=resp.json()["valvula"]["codigo"])
        self.assertEqual(v.classe, "PMT")
        self.assertEqual(v.classe_pmt, "PMT 16 bar")
        self.assertEqual(v.norma, "API 609")


# ── Borboleta Categoria B + norma API 609 → classe 150/300/600; diâmetro por faf/classe ──

class BorboletaCategoriaBRuleTest(EspecialMixin, TestCase):
    def _post(self, **kw):
        p = {
            "tipo_valvula": "BORBOLETA",
            "categoria_borboleta": "CATEGORIA B", "norma": "API 609",
            "face_a_face": "WAFER", "classe": "150", "diametro": '24"',
            "materiais": [{"tipo_material": "CORPO_TAMPA", "material": "ASTM A216 WCB"}],
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_aceito(self):
        self.assertEqual(self._post().status_code, 200, "cat B base deve passar")

    def test_classe_invalida(self):
        resp = self._post(classe="900")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_lug_wafer_600_ate_48(self):
        self.assertEqual(self._post(face_a_face="LUG", classe="600", diametro='48"').status_code, 200)

    def test_lug_wafer_abaixo_3_invalido(self):
        resp = self._post(diametro='2"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_padrao_longo_600_36_ok(self):
        self.assertEqual(self._post(face_a_face="FLANGEADA PADRÃO LONGO", classe="600", diametro='36"').status_code, 200)

    def test_padrao_longo_600_40_invalido(self):
        resp = self._post(face_a_face="FLANGEADA PADRÃO LONGO", classe="600", diametro='40"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_padrao_curto_150_48_ok(self):
        self.assertEqual(self._post(face_a_face="FLANGEADA PADRÃO CURTO", classe="150", diametro='48"').status_code, 200)

    def test_padrao_curto_600_24_ok(self):
        self.assertEqual(self._post(face_a_face="FLANGEADA PADRÃO CURTO", classe="600", diametro='24"').status_code, 200)

    def test_padrao_curto_600_30_invalido(self):
        resp = self._post(face_a_face="FLANGEADA PADRÃO CURTO", classe="600", diametro='30"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_norma_diferente_nao_aplica(self):
        """Norma != API 609 → regra não aplica; classe 900 passa."""
        resp = self._post(norma="ASME B16.34", classe="900")
        self.assertEqual(resp.status_code, 200, resp.content)


class MssSp67EscopoTest(EspecialMixin, TestCase):
    """MSS SP-67: diametro em lista fechada (decisao de negocio 2026-07-21) - 1 1/2", 2",
    2 1/2", 3", 4", 5", 6", 8", 10", 12", 14", 16", 18", 20", 24", 30", 36", 42", 48",
    54", 60", 64", 66", 72". 5"/64"/66"/72" nao existem em DIAMETROS_POR_TIPO, injetados
    so' no frontend p/ essa norma. 3.1-3.3 + 4.3: flange so' ate' Classe 150 -> classe
    125/150/PMT."""

    def _post(self, **kw):
        p = {
            "tipo_valvula": "BORBOLETA", "funcao": "BLOQUEIO", "nbr": False,
            "norma": "MSS SP67", "diametro": '4"', "classe": "150",
            "face_a_face": "LUG",
        }
        p.update(kw)
        return self.client.post(reverse("core:valvula_criar"), json.dumps(p),
                                content_type="application/json")

    def test_base_aceita(self):
        resp = self._post()
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_diametro_1_rejeitado(self):
        resp = self._post(diametro='1"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_diametro_1_1_4_rejeitado(self):
        resp = self._post(diametro='1 1/4"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_diametro_1_1_2_aceito(self):
        self.assertEqual(self._post(diametro='1 1/2"').status_code, 200)

    def test_diametro_60_aceito(self):
        self.assertEqual(self._post(diametro='60"').status_code, 200)

    def test_diametro_72_aceito(self):
        """Teto real da norma; fora de DIAMETROS_POR_TIPO, so' aceito por essa norma."""
        self.assertEqual(self._post(diametro='72"').status_code, 200)

    def test_diametro_5_aceito(self):
        """Fora de DIAMETROS_POR_TIPO, so' aceito por essa norma."""
        self.assertEqual(self._post(diametro='5"').status_code, 200)

    def test_diametro_22_rejeitado(self):
        """22" existe em DIAMETROS_POR_TIPO mas nao entra na lista fechada da norma."""
        resp = self._post(diametro='22"')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("diametro", resp.json()["errors"])

    def test_classe_125_aceita(self):
        self.assertEqual(self._post(classe="125").status_code, 200)

    def test_classe_300_rejeitada(self):
        resp = self._post(classe="300")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_classe_pn_rejeitada(self):
        resp = self._post(classe="PN 100")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe", resp.json()["errors"])

    def test_classe_pmt_sem_texto_rejeitada(self):
        resp = self._post(classe="PMT")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("classe_pmt", resp.json()["errors"])

    def test_classe_pmt_com_texto_aceita(self):
        resp = self._post(classe="PMT", classe_pmt="10 in. Hg")
        self.assertEqual(resp.status_code, 200, resp.content)

    def test_norma_diferente_nao_aplica(self):
        """Norma != MSS SP-67 → regra não aplica; classe 300 e diâmetro 1" passam."""
        resp = self._post(norma="ASME B16.34", classe="300", diametro='1"')
        self.assertEqual(resp.status_code, 200, resp.content)

# .
