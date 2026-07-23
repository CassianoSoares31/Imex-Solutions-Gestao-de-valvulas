from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid
from django.core.exceptions import ValidationError


class UsuarioManager(BaseUserManager):
    def create_user(self, email, nome, password=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, nome=nome, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nome, password=None, **extra_fields):
        extra_fields.setdefault('nivel_permissao', 'ESPECIAL')
        extra_fields.setdefault('confirmado', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, nome, password, **extra_fields)


class Tb_Usuario(AbstractBaseUser, PermissionsMixin):
    NIVEL_PERMISSAO = [
        ('ESPECIAL', 'Especial'),
        ('COMUM', 'Comum'),
    ]

    nome = models.CharField(max_length=255, verbose_name="Nome")
    email = models.EmailField(unique=True, verbose_name="Email")
    nivel_permissao = models.CharField(
        max_length=10,
        choices=NIVEL_PERMISSAO,
        default='COMUM',
        verbose_name="Nível de Permissão"
    )
    confirmado = models.BooleanField(
        default=False,
        verbose_name="Confirmado"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Acesso ao Admin"
    )

    token_verificacao = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        verbose_name="Token de Verificação"
    )
    token_expiracao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Expiração do Token"
    )
    senha_alterada_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Última alteração de senha"
    )
    trocas_senha_hoje = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Trocas de senha hoje"
    )
    ultima_data_troca = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data da última troca de senha"
    )

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome']

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        db_table = 'core_tb_usuario'

    def __str__(self):
        return self.email


class Material(models.Model):
    id_material = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiais"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Projeto(models.Model):
    STATUS_CHOICES = [
        ("ATIVO", "Ativo"),
        ("CONCLUIDO", "Concluído"),
    ]

    id_projeto = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=120, unique=True, verbose_name="Projeto")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="ATIVO", verbose_name="Status")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Projeto"
        verbose_name_plural = "Projetos"
        ordering = ["-criado_em"]

    def __str__(self):
        return self.nome


class OpcaoSimples(models.Model):
    """Base p/ listas de opção 'folha' editáveis via admin (só alimentam
    dropdowns, não entram em regra NBR). Cada subclasse vira uma tabela."""
    valor = models.CharField(max_length=100, unique=True, verbose_name="Valor")
    ordem = models.PositiveIntegerField(default=0, verbose_name="Ordem")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        abstract = True
        ordering = ["ordem", "valor"]

    def __str__(self):
        return self.valor


class OpcaoFlange(OpcaoSimples):
    class Meta(OpcaoSimples.Meta):
        verbose_name = "Norma de Flange"
        verbose_name_plural = "Normas de Flange"


class OpcaoPlacaIdentificacao(OpcaoSimples):
    class Meta(OpcaoSimples.Meta):
        verbose_name = "Placa de Identificação"
        verbose_name_plural = "Placas de Identificação"


class Valvula(models.Model):
    # === Choices por tipo de válvula ===

    TIPO_VALVULA = [
        ("ESFERA", "Esfera"),
        ("GAVETA", "Gaveta"),
        ("GLOBO", "Globo"),
        ("RETENCAO", "Retenção"),
        ("BORBOLETA", "Borboleta"),
        ("GLOBO_CONTROLE", "Globo Controle"),
    ]

    # Função da válvula: Bloqueio (sem instrumentação) ou Controle (mostra
    # instrumentação). Independe do posicionador — quem decide é a função.
    FUNCAO = [
        ("BLOQUEIO", "Bloqueio"),
        ("CONTROLE", "Controle"),
    ]

    NORMA_ESFERA = [
        ("API 6D", "API 6D"),
        ("ISO 14313", "ISO 14313"),
        ("API 608", "API 608"),
        ("ASME B16.34", "ASME B16.34"),
        ("ISO 17292", "ISO 17292"),
        ("MSS SP72", "MSS SP72"),
        ("NBR 14788", "NBR 14788"),
        ("BS ISO 7121", "BS ISO 7121"),
    ]

    NORMA_GAVETA = [
        ("API 6D", "API 6D"),
        ("ISO 14313", "ISO 14313"),
        ("API 600", "API 600"),
        ("ISO 10434", "ISO 10434"),
        ("API 602", "API 602"),
        ("ISO 15761", "ISO 15761"),
        ("ASME B16.34", "ASME B16.34"),
    ]

    NORMA_GLOBO = [
        ("BS 1873", "BS 1873"),
        ("API 602", "API 602"),
        ("ISO 15761", "ISO 15761"),
        ("API 623", "API 623"),
        ("ASME B16.34", "ASME B16.34"),
    ]

    NORMA_RETENCAO = [
        ("BS 1868", "BS 1868"),
        ("API 602", "API 602"),
        ("ISO 15761", "ISO 15761"),
        ("API 6D", "API 6D"),
        ("ASME B16.34", "ASME B16.34"),
        ("API 594", "API 594"),
        ("ISO 14313", "ISO 14313"),
    ]

    NORMA_BORBOLETA = [
        ("API 609", "API 609"),
        ("ASME B16.34", "ASME B16.34"),
        ("MSS SP67", "MSS SP67"),
    ]

    NORMA_GLOBO_CONTROLE = [
        ("Conforme Fabricante", "Conforme Fabricante"),
    ]

    NORMAS_POR_TIPO = {
        "ESFERA": NORMA_ESFERA,
        "GAVETA": NORMA_GAVETA,
        "GLOBO": NORMA_GLOBO,
        "RETENCAO": NORMA_RETENCAO,
        "BORBOLETA": NORMA_BORBOLETA,
        "GLOBO_CONTROLE": NORMA_GLOBO_CONTROLE,
    }

    DIAMETROS = [
        ('1/2"', '1/2"'), ('3/4"', '3/4"'), ('1"', '1"'),
        ('1 1/4"', '1 1/4"'), ('1 1/2"', '1 1/2"'), ('2"', '2"'),
        ('2 1/2"', '2 1/2"'), ('3"', '3"'), ('4"', '4"'),
        ('6"', '6"'), ('8"', '8"'), ('10"', '10"'),
        ('12"', '12"'), ('14"', '14"'), ('16"', '16"'),
        ('18"', '18"'), ('20"', '20"'), ('22"', '22"'),
        ('24"', '24"'), ('26"', '26"'), ('28"', '28"'),
        ('30"', '30"'), ('32"', '32"'), ('34"', '34"'),
        ('36"', '36"'), ('38"', '38"'), ('40"', '40"'),
        ('42"', '42"'), ('48"', '48"'), ('54"', '54"'),
        ('56"', '56"'), ('60"', '60"'),
    ]

    DIAMETROS_RETENCAO = [
        ('1/2"', '1/2"'), ('3/4"', '3/4"'), ('1"', '1"'),
        ('1 1/4"', '1 1/4"'), ('1 1/2"', '1 1/2"'), ('2"', '2"'),
        ('2 1/2"', '2 1/2"'), ('3"', '3"'), ('4"', '4"'),
        ('6"', '6"'), ('8"', '8"'), ('10"', '10"'),
        ('12"', '12"'), ('14"', '14"'), ('16"', '16"'),
        ('18"', '18"'), ('20"', '20"'), ('22"', '22"'),
        ('24"', '24"'), ('26"', '26"'), ('28"', '28"'),
        ('30"', '30"'), ('32"', '32"'), ('34"', '34"'),
        ('36"', '36"'), ('38"', '38"'), ('40"', '40"'),
        ('42"', '42"'), ('48"', '48"'),
    ]

    CLASSES = [
        ("150", "150"), ("300", "300"), ("600", "600"), ("800", "800"),
        ("900", "900"), ("1500", "1500"), ("2500", "2500"), ("4500", "4500"),
        ("PN 10", "PN 10"), ("PN 16", "PN 16"), ("PN 20", "PN 20"),
        ("PN 25", "PN 25"), ("PN 40", "PN 40"), ("PN 50", "PN 50"),
        ("PN 100", "PN 100"), ("PN 150", "PN 150"), ("PN 250", "PN 250"),
        ("PN 420", "PN 420"),
    ]

    CLASSES_RETENCAO_GLOBO = [
        ("150", "150"), ("300", "300"), ("400", "400"), ("600", "600"), ("800", "800"),
        ("900", "900"), ("1500", "1500"), ("2500", "2500"), ("4500", "4500"),
    ]

    # Borboleta: classes padrão + 125 e PMT (PMT abre campo de texto livre)
    CLASSES_BORBOLETA = [("125", "125")] + CLASSES + [("PMT", "PMT")]

    TIPO_EXTREMIDADE = [
        ("FLANGE FACE PLANA", "Flange Face Plana"),
        ("FLANGE RF", "Flange RF"),
        ("FLANGE RTJ (FJA)", "Flange RTJ (FJA)"),
        ("BUTT-WELDING 10", "Butt-Welding 10"),
        ("BUTT-WELDING 20", "Butt-Welding 20"),
        ("BUTT-WELDING 30", "Butt-Welding 30"),
        ("BUTT-WELDING 40", "Butt-Welding 40"),
        ("BUTT-WELDING 50", "Butt-Welding 50"),
        ("BUTT-WELDING 60", "Butt-Welding 60"),
        ("BUTT-WELDING 70", "Butt-Welding 70"),
        ("BUTT-WELDING 80", "Butt-Welding 80"),
        ("BUTT-WELDING 100", "Butt-Welding 100"),
        ("BUTT-WELDING 110", "Butt-Welding 110"),
        ("BUTT-WELDING 120", "Butt-Welding 120"),
        ("BUTT-WELDING 130", "Butt-Welding 130"),
        ("BUTT-WELDING 140", "Butt-Welding 140"),
        ("BUTT-WELDING 150", "Butt-Welding 150"),
        ("BUTT-WELDING 160", "Butt-Welding 160"),
        ("BUTT-WELDING 170", "Butt-Welding 170"),
        ("BUTT-WELDING 180", "Butt-Welding 180"),
        ("SOCKET-WELDING", "Socket-Welding"),
        ("ROSCA NPT", "Rosca NPT"),
        ("ROSCA BSP", "Rosca BSP"),
        ("NIPLE 4\" COMP. SCH 5", 'Niple 4" Comp. SCH 5'),
        ("NIPLE 4\" COMP. SCH 10", 'Niple 4" Comp. SCH 10'),
        ("NIPLE 4\" COMP. SCH 30", 'Niple 4" Comp. SCH 30'),
        ("NIPLE 4\" COMP. SCH 40", 'Niple 4" Comp. SCH STD'),
        ("NIPLE 4\" COMP. SCH 80", 'Niple 4" Comp. SCH 80 XS'),
        ("NIPLE 4\" COMP. SCH 160", 'Niple 4" Comp. SCH 160'),
        ("NIPLE 4\" COMP. SCH XXS", 'Niple 4" Comp. SCH XXS'),
        ("Wafer", "Wafer"),
        ("GRAY LOC HUB", "Gray Loc Hub"),
        ("LUG", "Lug"),
    ]

    TIPO_EXTREMIDADE_GC = [
        ("FLANGE FACE PLANA", "Flange Face Plana"),
        ("FLANGE RF", "Flange RF"),
        ("FLANGE RTJ (FJA)", "Flange RTJ (FJA)"),
        ("BUTT-WELDING", "Butt-Welding"),
        ("SOCKET-WELDING", "Socket-Welding"),
        ("ROSCA NPT", "Rosca NPT"),
        ("ROSCA BSP", "Rosca BSP"),
    ]

    TIPO_RANHURA = [
        ("125-250 μin ESPIRAL", "125-250 μin Espiral"),
        ("125-250 μin CONCÊNTRICA", "125-250 μin Concêntrica"),
        ("LISO (125 μin)", "Liso (125 μin)"),
        ("N/A", "N/A"),
    ]

    # Material do Corpo / Tampa — itens separados conforme documentação
    MATERIAIS_CORPO_TAMPA = [
        ("ASTM A105", "ASTM A105"),
        ("ASTM A105N revestimento interno de INCONEL", "ASTM A105N revestimento interno de INCONEL"),
        ("ASTM A105N revestimento interno orgânico", "ASTM A105N revestimento interno orgânico"),
        ("ASTM A105N revestimento interno de PTFE", "ASTM A105N revestimento interno de PTFE"),
        ("ASTM A105N revestimento em SS316", "ASTM A105N revestimento em SS316"),

        ("ASTM A182 F11 CL1", "ASTM A182 F11 CL1"),
        ("ASTM A182 F11 CL2", "ASTM A182 F11 CL2"),
        ("ASTM A182 F5", "ASTM A182 F5"),
        ("ASTM A182 F6a", "ASTM A182 F6a"),
        ("ASTM A182 F304", "ASTM A182 F304"),
        ("ASTM A182 F304 L", "ASTM A182 F304 L"),
        ("ASTM A182 F316", "ASTM A182 F316"),
        ("ASTM A182 F316 L", "ASTM A182 F316 L"),
        ("ASTM A182 F317", "ASTM A182 F317"),
        ("ASTM A182 F321", "ASTM A182 F321"),
        ("ASTM A182 F347", "ASTM A182 F347"),
        ("ASTM A182 F51", "ASTM A182 F51"),
        ("ASTM A182 F53", "ASTM A182 F53"),
        ("ASTM A182 F54", "ASTM A182 F54"),
        ("ASTM A182 F55", "ASTM A182 F55"),
        ("ASTM A216 WCB", "ASTM A216 WCB"),
        ("ASTM A216 WCB revestimento em EPOXY", "ASTM A216 WCB revestimento em EPOXY"),
        ("ASTM A216 WCB revestimento em BUNA-N", "ASTM A216 WCB revestimento em BUNA-N"),
        ("ASTM A216 WCB revestimento em VITON", "ASTM A216 WCB revestimento em VITON"),
        ("ASTM A216 WCB revestimento em NEOPRENE", "ASTM A216 WCB revestimento em NEOPRENE"),
        ("ASTM A216 WCB revestimento em EPDM", "ASTM A216 WCB revestimento em EPDM"),
        ("ASTM A216 WCB revestimento INCONEL", "ASTM A216 WCB revestimento INCONEL"),
        ("ASTM A216 WCB revestimento interno orgânico", "ASTM A216 WCB revestimento interno orgânico"),
        ("ASTM A216 WCC", "ASTM A216 WCC"),
        ("ASTM A217 WC5", "ASTM A217 WC5"),
        ("ASTM A217 WC6", "ASTM A217 WC6"),
        ("ASTM A217 C5", "ASTM A217 C5"),
        ("ASTM A217 C12", "ASTM A217 C12"),
        ("ASTM A217 CA15", "ASTM A217 CA15"),
        ("ASTM A350 LF1", "ASTM A350 LF1"),
        ("ASTM A350 LF2", "ASTM A350 LF2"),
        ("ASTM A350 LF2 Cl1 revestimento interno de INCONEL", "ASTM A350 LF2 Cl1 revestimento interno de INCONEL"),
        ("ASTM A350 LF3", "ASTM A350 LF3"),
        ("ASTM A351 CF3", "ASTM A351 CF3"),
        ("ASTM A351 CF8", "ASTM A351 CF8"),
        ("ASTM A351 CF3M", "ASTM A351 CF3M"),
        ("ASTM A351 CF8M", "ASTM A351 CF8M"),
        ("ASTM A351 CG8M", "ASTM A351 CG8M"),
        ("ASTM A351 CF8C", "ASTM A351 CF8C"),
        ("ASTM A351 CN7M", "ASTM A351 CN7M"),
        ("ASTM A352 LCA", "ASTM A352 LCA"),
        ("ASTM A352 LCB", "ASTM A352 LCB"),
        ("ASTM A352 LC3", "ASTM A352 LC3"),
        ("ASTM A352 LCC", "ASTM A352 LCC"),
        ("ASTM A352 CA6NM", "ASTM A352 CA6NM"),
        ("ASTM A995 3A", "ASTM A995 3A"),
        ("ASTM A995 4A", "ASTM A995 4A"),
        ("ASTM A995 5A", "ASTM A995 5A"),
        ("ASTM A995 6A", "ASTM A995 6A"),
        ("ASTM B564 N04400", "ASTM B564 N04400"),
        ("ASTM B865 N05500", "ASTM B865 N05500"),
    ]

    MATERIAIS_CORPO_BORBOLETA = [
        ("ASTM A536 65-45-12", "ASTM A536 65-45-12"),
        ("ASTM A105", "ASTM A105"),
        ("ASTM A216 GR WCB", "ASTM A216 GR WCB"),
        ("ASTM A216 GR WCC", "ASTM A216 GR WCC"),
    ]

    # Esfera: formato longo com refs ASTM
    MATERIAIS_OBTURADOR_ESFERA = [
        ("AISI 304", "AISI 304"),
        ("AISI 304L", "AISI 304L"),
        ("AISI 316", "AISI 316"),
        ("AISI 316L", "AISI 316L"),
        ("AISI 321", "AISI 321"),
        ("AISI 347", "AISI 347"),
        ("AISI 410", "AISI 410"),
        ("STELLITE 6", "STELLITE 6"),
        ("STELLITE 21", "STELLITE 21"),
        ("MONEL 400", "MONEL 400"),
        ("MONEL K500", "MONEL K500"),
        ("ASTM A217 CA15", "ASTM A217 CA15"),
        ("ASTM A182 F51 + Grafite", "ASTM A182 F51 + Grafite"),
        ("ASTM A182 F316 + Grafite", "ASTM A182 F316 + Grafite"),
        ("ASTM A536 GR 65-45-12", "ASTM A536 GR 65-45-12"),
        ("ASTM A182 F53 + Grafite", "ASTM A182 F53 + Grafite"),
        ("Inconel 625 + Grafite", "Inconel 625 + Grafite"),
        ("ASTM A182 F55 + Grafite", "ASTM A182 F55 + Grafite"),
        ("ASTM A182 F6NM", "ASTM A182 F6NM"),
        ("CF3M", "CF3M"),
        ("B62", "B62"),
        ("ASTM B148 C95500", "ASTM B148 C95500"),
        ("ASTM B148 C95800", "ASTM B148 C95800"),
        ("BUNA N", "BUNA N"),
        ("ASTM A105N", "ASTM A105N"),
        ("ASTM A105N + ENP", "ASTM A105N + ENP"),
        ("ASTM A216 WCB", "ASTM A216 WCB"),
        ("ASTM A216 WCB (revestido em PTFE)", "ASTM A216 WCB (revestido em PTFE)"),
        ("Cromo duro", "Cromo duro"),
        ("Carbeto de Tungstênio", "Carbeto de Tungstênio"),
        ("ASTM A182 F51", "ASTM A182 F51"),
        ("ASTM A182 F53", "ASTM A182 F53"),
        ("ASTM A182 F55", "ASTM A182 F55"),
        ("ASTM A182 F60", "ASTM A182 F60"),
        ("ASTM A182 F61", "ASTM A182 F61"),
        ("ASTM A182 F71", "ASTM A182 F71"),
        ("AISI 316 + Stellite", "AISI 316 + Stellite"),
        ("DEVLON", "DEVLON"),
        ("EPDM", "EPDM"),
        ("INCONEL 625 (UNS N06625)", "INCONEL 625 (UNS N06625)"),
        ("INCONEL X-750 (UNS N07750)", "INCONEL X-750 (UNS N07750)"),
        ("ASTM A182 F5", "ASTM A182 F5"),
        ("ASTM A182 F5A", "ASTM A182 F5A"),
        ("ASTM A182 F9", "ASTM A182 F9"),
        ("ASTM A182 F91", "ASTM A182 F91"),
        ("UNS 04400", "UNS 04400"),
        ("AISI 420", "AISI 420"),
        ("AISI 430", "AISI 430"),
        ("XM-19", "XM-19"),
        ("17-4PH", "17-4PH"),
        ("MONEL", "MONEL"),
        ("AISI 304 + ENP", "AISI 304 + ENP"),
        ("AISI 410 + ENP", "AISI 410 + ENP"),
        ("Neoprene", "Neoprene"),
        ("Nylon 12", "Nylon 12"),
        ("PCTFE", "PCTFE"),
        ("PEEK", "PEEK"),
        ("PTFE", "PTFE"),
        ("RPTFE (25% C)", "RPTFE (25% C)"),
        ("RPTFE (25% FV)", "RPTFE (25% FV)"),
        ("Stellite .12", "Stellite .12"),
        ("Stellite .21", "Stellite .21"),
        ("Stellite .6", "Stellite .6"),
        ("VITON", "VITON"),
        ("UNS N06001", "UNS N06001"),
        ("AISI 304H", "AISI 304H"),
        ("INCONEL 718", "INCONEL 718"),
        ("ASTM A890/A995 4A", "ASTM A890/A995 4A"),
        ("ASTM A890/A995 5A", "ASTM A890/A995 5A"),
        ("ASTM A890/A995 6A", "ASTM A890/A995 6A"),
        ("AISI 316 + ENP", "AISI 316 + ENP"),
        ("ASTM A182 F51 + ENP", "ASTM A182 F51 + ENP"),
        ("ASTM A182 F53 + ENP", "ASTM A182 F53 + ENP"),
        ("ASTM A182 F55 + ENP", "ASTM A182 F55 + ENP"),
        ("ASTM B564 (UNS N06625)", "ASTM B564 (UNS N06625)"),
        ("ASTM B564 type 630", "ASTM B564 type 630"),
        ("UNS N08811", "UNS N08811"),
        ("AISI 304 + Stellite", "AISI 304 + Stellite"),
        ("AISI 410 + Stellite", "AISI 410 + Stellite"),
        ("CF8M", "CF8M"),
        ("Não aplicável", "Não aplicável"),
        ("AISI 304 + carbeto de tungstênio", "AISI 304 + carbeto de tungstênio"),
        ("AISI 316 + carbeto de tungstênio", "AISI 316 + carbeto de tungstênio"),
        ("AISI 410 + carbeto de tungstênio", "AISI 410 + carbeto de tungstênio"),
        ("AISI 410 + cromo duro", "AISI 410 + cromo duro"),
        ("AISI 304 + cromo duro", "AISI 304 + cromo duro"),
        ("AISI 316 + cromo duro", "AISI 316 + cromo duro"),
        ("ASTM A350 LF2 (ENP)", "ASTM A350 LF2 (ENP)"),
        ("ASTM A536 GR 65-45-12 + NYLON 11", "ASTM A536 GR 65-45-12 + NYLON 11"),
        ("AISI 316 + Ni60", "AISI 316 + Ni60"),
        ("Padrão fabricante", "Padrão fabricante"),
        ("ASTM A216 WCC", "ASTM A216 WCC"),
        ("ASTM A182 F316 + Carbeto de Tungstênio", "ASTM A182 F316 + Carbeto de Tungstênio"),
        ("ASTM A182 F6A", "ASTM A182 F6A"),
        ("ASTM A182 F316", "ASTM A182 F316"),
        ("ASTM A747 C", "ASTM A747 C"),
        ("ASTM A352 LCC + INCONEL (UNS N06625)", "ASTM A352 LCC + INCONEL (UNS N06625)"),
        ("A217 CA15 + Stellite", "A217 CA15 + Stellite"),
        ("A182 F6A + Stellite", "A182 F6A + Stellite"),
        ("A217 WC6 + Stellite", "A217 WC6 + Stellite"),
        ("A217 WC9 + Stellite", "A217 WC9 + Stellite"),
        ("AISI 410 + INCONEL (UNS N06625)", "AISI 410 + INCONEL (UNS N06625)"),
        ("INCONEL 625 + Carbeto de Tungstênio", "INCONEL 625 + Carbeto de Tungstênio"),
        ("ASTM A182 F55 + Carbeto de Tungstênio", "ASTM A182 F55 + Carbeto de Tungstênio"),
        ("ASTM A182 F51 + TCC", "ASTM A182 F51 + TCC"),
        ("A995 6A + STL", "A995 6A + STL"),
        ("ASTM A216 WCB + STL", "ASTM A216 WCB + STL"),
        ("ASTM A182 F6A + Carbeto de Tungstênio", "ASTM A182 F6A + Carbeto de Tungstênio"),
        ("ASTM A522 type 1 + Carbeto de Tungstênio", "ASTM A522 type 1 + Carbeto de Tungstênio"),
        ("A105 + 13CR", "A105 + 13CR"),
        ("ASTM A479 410", "ASTM A479 410"),
        ("ASTM A182 F304", "ASTM A182 F304"),
        ("ASTM A216 WCB + B62", "ASTM A216 WCB + B62"),
        ("ASTM A216 WCB + 13CR", "ASTM A216 WCB + 13CR"),
        ("ASTM A105 + B62", "ASTM A105 + B62"),
        ("ASTM A182 F316L + STL", "ASTM A182 F316L + STL"),
        ("ASTM A351 CF8M + STL", "ASTM A351 CF8M + STL"),
        ("ASTM A182 F11", "ASTM A182 F11"),
        ("ASTM A182 F11 + Stellite", "ASTM A182 F11 + Stellite"),
        ("ASTM A182 F91 + Stellite", "ASTM A182 F91 + Stellite"),
        ("M5 (17-4PH) + ST (Stellite .6)", "M5 (17-4PH) + ST (Stellite .6)"),
        ("B150 C63000", "B150 C63000"),
        ("A182 F55 + STL", "A182 F55 + STL"),
        ("ASTM A522 Type I", "ASTM A522 Type I"),
        ("AISI 431", "AISI 431"),
        ("ASTM A105 + ENP + DEVLON", "ASTM A105 + ENP + DEVLON"),
        ("ASTM A105 + ENP + PEEK", "ASTM A105 + ENP + PEEK"),
        ("ASTM A105 + ENP + RPTFE", "ASTM A105 + ENP + RPTFE"),
        ("ASTM A351 CF8", "ASTM A351 CF8"),
        ("AISI 321H + Stellite", "AISI 321H + Stellite"),
        ("AISI 321H", "AISI 321H"),
        ("INCONEL 718 + Carbeto de Tungstênio", "INCONEL 718 + Carbeto de Tungstênio"),
        ("ASTM A350 Gr LF3 + revestimento de solda INCONEL 625 + Carbeto de Tungstênio", "ASTM A350 Gr LF3 + revestimento de solda INCONEL 625 + Carbeto de Tungstênio"),
        ("INCONEL 625 + RPTFE (25% C)", "INCONEL 625 + RPTFE (25% C)"),
        ("ASTM A182 F6A Cl 2 + ENP", "ASTM A182 F6A Cl 2 + ENP"),
        ("ASTM A350 LF2 + INCONEL 625", "ASTM A350 LF2 + INCONEL 625"),
        ("ASTM A352 LCB", "ASTM A352 LCB"),
        ("UNS 32750 + Hard Chrome", "UNS 32750 + Hard Chrome"),
        ("AISI 4130", "AISI 4130"),
        ("MONEL 400 (UNS N04400)", "MONEL 400 (UNS N04400)"),
        ("INTEGRAL+MONEL 400 (UNS N04400)", "INTEGRAL+MONEL 400 (UNS N04400)"),
        ("F316+STL.6", "F316+STL.6"),
        ("C5+SS304", "C5+SS304"),
        ("F5+STL.6", "F5+STL.6"),
        ("CI+B62", "CI+B62"),
        ("ASTM A276 (UNS S32750)", "ASTM A276 (UNS S32750)"),
        ("F6A+HFC", "F6A+HFC"),
        ("INCONEL 718-API 6A", "INCONEL 718-API 6A"),
        ("A694 F60+TCC", "A694 F60+TCC"),
        ("A182 F6A+PEEK+PTFE", "A182 F6A+PEEK+PTFE"),
        ("A182 F6A+RPTFE", "A182 F6A+RPTFE"),
        ("ASTM A182 F316 + ENP", "ASTM A182 F316 + ENP"),
        ("ASTM A217 CA15 + SF", "ASTM A217 CA15 + SF"),
        ("AISI 410 + SF", "AISI 410 + SF"),
        ("AISI 316 SF", "AISI 316 SF"),
        ("ASTM A995 4A + SF", "ASTM A995 4A + SF"),
        ("A276 316", "A276 316"),
        ("Monel 400", "Monel 400"),
        ("ASTM A995 4A + RAM 21 (TCC)", "ASTM A995 4A + RAM 21 (TCC)"),
        ("A565 616HT", "A565 616HT"),
        ("AISI 410 Hardened", "AISI 410 Hardened"),
        ("ASTM A351 CF8M + FSF", "ASTM A351 CF8M + FSF"),
        ("A182 F6A + PEEK", "A182 F6A + PEEK"),
        ("ASTM A522 type 1 + carbeto de Tungstênio", "ASTM A522 type 1 + carbeto de Tungstênio"),
        ("CF8+PFA", "CF8+PFA"),
        ("CF8M+PFA", "CF8M+PFA"),
        ("17-4PH+Cr", "17-4PH+Cr"),
        ("F51+Cr", "F51+Cr"),
        ("ASTM A182 F55 + PEEK", "ASTM A182 F55 + PEEK"),
        ("ASTM A182 F53 + NYLON", "ASTM A182 F53 + NYLON"),
        ("13 CR", "13 CR"),
        ("AISI 410 + Carbeto de Cromo", "AISI 410 + Carbeto de Cromo"),
        ("ASTM A890/A995 6A + Carbeto de Tungstênio", "ASTM A890/A995 6A + Carbeto de Tungstênio"),
        ("AISI 316L + PTFE", "AISI 316L + PTFE"),
        ("AISI 410 Nitretado", "AISI 410 Nitretado"),
    ]

    # Gaveta, Globo, Retenção, Globo Controle: formato curto
    MATERIAIS_OBTURADOR = [
        ("AISI 304", "AISI 304"),
        ("AISI 304L", "AISI 304L"),
        ("AISI 316", "AISI 316"),
        ("AISI 316L", "AISI 316L"),
        ("AISI 321", "AISI 321"),
        ("AISI 347", "AISI 347"),
        ("AISI 410", "AISI 410"),
        ("STELLITE 6", "STELLITE 6"),
        ("STELLITE 21", "STELLITE 21"),
        ("MONEL 400", "MONEL 400"),
        ("MONEL K500", "MONEL K500"),
        ("ASTM A217 CA15", "ASTM A217 CA15"),
        ("ASTM A182 F51 + Grafite", "ASTM A182 F51 + Grafite"),
        ("ASTM A182 F316 + Grafite", "ASTM A182 F316 + Grafite"),
        ("ASTM A536 GR 65-45-12", "ASTM A536 GR 65-45-12"),
        ("ASTM A182 F53 + Grafite", "ASTM A182 F53 + Grafite"),
        ("Inconel 625 + Grafite", "Inconel 625 + Grafite"),
        ("ASTM A182 F55 + Grafite", "ASTM A182 F55 + Grafite"),
        ("ASTM A182 F6NM", "ASTM A182 F6NM"),
        ("CF3M", "CF3M"),
        ("B62", "B62"),
        ("ASTM B148 C95500", "ASTM B148 C95500"),
        ("ASTM B148 C95800", "ASTM B148 C95800"),
        ("BUNA N", "BUNA N"),
        ("ASTM A105N", "ASTM A105N"),
        ("ASTM A105N + ENP", "ASTM A105N + ENP"),
        ("ASTM A216 WCB", "ASTM A216 WCB"),
        ("ASTM A216 WCB (revestido em PTFE)", "ASTM A216 WCB (revestido em PTFE)"),
        ("Cromo duro", "Cromo duro"),
        ("Carbeto de Tungstênio", "Carbeto de Tungstênio"),
        ("ASTM A182 F51", "ASTM A182 F51"),
        ("ASTM A182 F53", "ASTM A182 F53"),
        ("ASTM A182 F55", "ASTM A182 F55"),
        ("ASTM A182 F60", "ASTM A182 F60"),
        ("ASTM A182 F61", "ASTM A182 F61"),
        ("ASTM A182 F71", "ASTM A182 F71"),
        ("AISI 316 + Stellite", "AISI 316 + Stellite"),
        ("DEVLON", "DEVLON"),
        ("EPDM", "EPDM"),
        ("INCONEL 625 (UNS N06625)", "INCONEL 625 (UNS N06625)"),
        ("INCONEL X-750 (UNS N07750)", "INCONEL X-750 (UNS N07750)"),
        ("ASTM A182 F5", "ASTM A182 F5"),
        ("ASTM A182 F5A", "ASTM A182 F5A"),
        ("ASTM A182 F9", "ASTM A182 F9"),
        ("ASTM A182 F91", "ASTM A182 F91"),
        ("UNS 04400", "UNS 04400"),
        ("AISI 420", "AISI 420"),
        ("AISI 430", "AISI 430"),
        ("XM-19", "XM-19"),
        ("17-4PH", "17-4PH"),
        ("MONEL", "MONEL"),
        ("AISI 304 + ENP", "AISI 304 + ENP"),
        ("AISI 410 + ENP", "AISI 410 + ENP"),
        ("Neoprene", "Neoprene"),
        ("Nylon 12", "Nylon 12"),
        ("PCTFE", "PCTFE"),
        ("PEEK", "PEEK"),
        ("PTFE", "PTFE"),
        ("RPTFE (25% C)", "RPTFE (25% C)"),
        ("RPTFE (25% FV)", "RPTFE (25% FV)"),
        ("Stellite .12", "Stellite .12"),
        ("Stellite .21", "Stellite .21"),
        ("Stellite .6", "Stellite .6"),
        ("VITON", "VITON"),
        ("UNS N06001", "UNS N06001"),
        ("AISI 304H", "AISI 304H"),
        ("INCONEL 718", "INCONEL 718"),
        ("ASTM A890/A995 4A", "ASTM A890/A995 4A"),
        ("ASTM A890/A995 5A", "ASTM A890/A995 5A"),
        ("ASTM A890/A995 6A", "ASTM A890/A995 6A"),
        ("AISI 316 + ENP", "AISI 316 + ENP"),
        ("ASTM A182 F51 + ENP", "ASTM A182 F51 + ENP"),
        ("ASTM A182 F53 + ENP", "ASTM A182 F53 + ENP"),
        ("ASTM A182 F55 + ENP", "ASTM A182 F55 + ENP"),
        ("ASTM B564 (UNS N06625)", "ASTM B564 (UNS N06625)"),
        ("ASTM B564 type 630", "ASTM B564 type 630"),
        ("UNS N08811", "UNS N08811"),
        ("AISI 304 + Stellite", "AISI 304 + Stellite"),
        ("AISI 410 + Stellite", "AISI 410 + Stellite"),
        ("CF8M", "CF8M"),
        ("Não aplicável", "Não aplicável"),
        ("AISI 304 + carbeto de tungstênio", "AISI 304 + carbeto de tungstênio"),
        ("AISI 316 + carbeto de tungstênio", "AISI 316 + carbeto de tungstênio"),
        ("AISI 410 + carbeto de tungstênio", "AISI 410 + carbeto de tungstênio"),
        ("AISI 410 + cromo duro", "AISI 410 + cromo duro"),
        ("AISI 304 + cromo duro", "AISI 304 + cromo duro"),
        ("AISI 316 + cromo duro", "AISI 316 + cromo duro"),
        ("ASTM A350 LF2 (ENP)", "ASTM A350 LF2 (ENP)"),
        ("ASTM A536 GR 65-45-12 + NYLON 11", "ASTM A536 GR 65-45-12 + NYLON 11"),
        ("AISI 316 + Ni60", "AISI 316 + Ni60"),
        ("Padrão fabricante", "Padrão fabricante"),
        ("ASTM A216 WCC", "ASTM A216 WCC"),
        ("ASTM A182 F316 + Carbeto de Tungstênio", "ASTM A182 F316 + Carbeto de Tungstênio"),
        ("ASTM A182 F6A", "ASTM A182 F6A"),
        ("ASTM A182 F316", "ASTM A182 F316"),
        ("ASTM A747 C", "ASTM A747 C"),
        ("ASTM A352 LCC + INCONEL (UNS N06625)", "ASTM A352 LCC + INCONEL (UNS N06625)"),
        ("A217 CA15 + Stellite", "A217 CA15 + Stellite"),
        ("A182 F6A + Stellite", "A182 F6A + Stellite"),
        ("A217 WC6 + Stellite", "A217 WC6 + Stellite"),
        ("A217 WC9 + Stellite", "A217 WC9 + Stellite"),
        ("AISI 410 + INCONEL (UNS N06625)", "AISI 410 + INCONEL (UNS N06625)"),
        ("INCONEL 625 + Carbeto de Tungstênio", "INCONEL 625 + Carbeto de Tungstênio"),
        ("ASTM A182 F55 + Carbeto de Tungstênio", "ASTM A182 F55 + Carbeto de Tungstênio"),
        ("ASTM A182 F51 + TCC", "ASTM A182 F51 + TCC"),
        ("A995 6A + STL", "A995 6A + STL"),
        ("ASTM A216 WCB + STL", "ASTM A216 WCB + STL"),
        ("ASTM A182 F6A + Carbeto de Tungstênio", "ASTM A182 F6A + Carbeto de Tungstênio"),
        ("ASTM A522 type 1 + Carbeto de Tungstênio", "ASTM A522 type 1 + Carbeto de Tungstênio"),
        ("A105 + 13CR", "A105 + 13CR"),
        ("ASTM A479 410", "ASTM A479 410"),
        ("ASTM A182 F304", "ASTM A182 F304"),
        ("ASTM A216 WCB + B62", "ASTM A216 WCB + B62"),
        ("ASTM A216 WCB + 13CR", "ASTM A216 WCB + 13CR"),
        ("ASTM A105 + B62", "ASTM A105 + B62"),
        ("ASTM A182 F316L + STL", "ASTM A182 F316L + STL"),
        ("ASTM A351 CF8M + STL", "ASTM A351 CF8M + STL"),
        ("ASTM A182 F11", "ASTM A182 F11"),
        ("ASTM A182 F11 + Stellite", "ASTM A182 F11 + Stellite"),
        ("ASTM A182 F91 + Stellite", "ASTM A182 F91 + Stellite"),
        ("M5 (17-4PH) + ST (Stellite .6)", "M5 (17-4PH) + ST (Stellite .6)"),
        ("B150 C63000", "B150 C63000"),
        ("A182 F55 + STL", "A182 F55 + STL"),
        ("ASTM A522 Type I", "ASTM A522 Type I"),
        ("AISI 431", "AISI 431"),
        ("ASTM A105 + ENP + DEVLON", "ASTM A105 + ENP + DEVLON"),
        ("ASTM A105 + ENP + PEEK", "ASTM A105 + ENP + PEEK"),
        ("ASTM A105 + ENP + RPTFE", "ASTM A105 + ENP + RPTFE"),
        ("ASTM A351 CF8", "ASTM A351 CF8"),
        ("AISI 321H + Stellite", "AISI 321H + Stellite"),
        ("AISI 321H", "AISI 321H"),
        ("INCONEL 718 + Carbeto de Tungstênio", "INCONEL 718 + Carbeto de Tungstênio"),
        ("ASTM A350 Gr LF3 + revestimento de solda INCONEL 625 + Carbeto de Tungstênio", "ASTM A350 Gr LF3 + revestimento de solda INCONEL 625 + Carbeto de Tungstênio"),
        ("INCONEL 625 + RPTFE (25% C)", "INCONEL 625 + RPTFE (25% C)"),
        ("ASTM A182 F6A Cl 2 + ENP", "ASTM A182 F6A Cl 2 + ENP"),
        ("ASTM A350 LF2 + INCONEL 625", "ASTM A350 LF2 + INCONEL 625"),
        ("ASTM A352 LCB", "ASTM A352 LCB"),
        ("UNS 32750 + Hard Chrome", "UNS 32750 + Hard Chrome"),
        ("AISI 4130", "AISI 4130"),
        ("MONEL 400 (UNS N04400)", "MONEL 400 (UNS N04400)"),
        ("INTEGRAL+MONEL 400 (UNS N04400)", "INTEGRAL+MONEL 400 (UNS N04400)"),
        ("F316+STL.6", "F316+STL.6"),
        ("C5+SS304", "C5+SS304"),
        ("F5+STL.6", "F5+STL.6"),
        ("CI+B62", "CI+B62"),
        ("ASTM A276 (UNS S32750)", "ASTM A276 (UNS S32750)"),
        ("F6A+HFC", "F6A+HFC"),
        ("INCONEL 718-API 6A", "INCONEL 718-API 6A"),
        ("A694 F60+TCC", "A694 F60+TCC"),
        ("A182 F6A+PEEK+PTFE", "A182 F6A+PEEK+PTFE"),
        ("A182 F6A+RPTFE", "A182 F6A+RPTFE"),
        ("ASTM A182 F316 + ENP", "ASTM A182 F316 + ENP"),
        ("ASTM A217 CA15 + SF", "ASTM A217 CA15 + SF"),
        ("AISI 410 + SF", "AISI 410 + SF"),
        ("AISI 316 SF", "AISI 316 SF"),
        ("ASTM A995 4A + SF", "ASTM A995 4A + SF"),
        ("A276 316", "A276 316"),
        ("Monel 400", "Monel 400"),
        ("ASTM A995 4A + RAM 21 (TCC)", "ASTM A995 4A + RAM 21 (TCC)"),
        ("A565 616HT", "A565 616HT"),
        ("AISI 410 Hardened", "AISI 410 Hardened"),
        ("ASTM A351 CF8M + FSF", "ASTM A351 CF8M + FSF"),
        ("A182 F6A + PEEK", "A182 F6A + PEEK"),
        ("ASTM A522 type 1 + carbeto de Tungstênio", "ASTM A522 type 1 + carbeto de Tungstênio"),
        ("CF8+PFA", "CF8+PFA"),
        ("CF8M+PFA", "CF8M+PFA"),
        ("17-4PH+Cr", "17-4PH+Cr"),
        ("F51+Cr", "F51+Cr"),
        ("ASTM A182 F55 + PEEK", "ASTM A182 F55 + PEEK"),
        ("ASTM A182 F53 + NYLON", "ASTM A182 F53 + NYLON"),
        ("13 CR", "13 CR"),
        ("AISI 410 + Carbeto de Cromo", "AISI 410 + Carbeto de Cromo"),
        ("ASTM A890/A995 6A + Carbeto de Tungstênio", "ASTM A890/A995 6A + Carbeto de Tungstênio"),
        ("AISI 316L + PTFE", "AISI 316L + PTFE"),
        ("AISI 410 Nitretado", "AISI 410 Nitretado"),
    ]

    MATERIAIS_OBTURADOR_BORBOLETA = [
        ("ASTM A536 65-45-12", "ASTM A536 65-45-12"),
        ("ASTM A106", "ASTM A106"),
        ("ASTM A216 GR WCB", "ASTM A216 GR WCB"),
        ("ASTM A216 GR WCC", "ASTM A216 GR WCC"),
    ]

    # Esfera: formato longo com refs ASTM em 410/Stellite, MONEL sem refs
    MATERIAIS_SEDE_ESFERA = [
        ("AISI 304", "AISI 304"),
        ("AISI 304L", "AISI 304L"),
        ("AISI 316", "AISI 316"),
        ("AISI 316L", "AISI 316L"),
        ("AISI 321", "AISI 321"),
        ("AISI 347", "AISI 347"),
        ("AISI 410 (ASTM A182 F6A)", "AISI 410 (ASTM A182 F6A)"),
        ("STELLITE 6 (ASTM A564 T630)", "STELLITE 6 (ASTM A564 T630)"),
        ("MONEL 400", "MONEL 400"),
        ("MONEL K500", "MONEL K500"),
        ("N/A", "N/A")
    ]

    # Gaveta, Globo, Retenção, Globo Controle: formato curto
    # Lista alinhada 1:1 com a tabela de código universal da SEDE
    # (_CODIGO_I_MATERIAL_RAW, views.py) — todo item aqui resolve pra um código.
    # Materiais elastoméricos (Buna N, Viton, EPDM...) tb aparecem aqui pq a
    # tabela de código não distingue Borboleta; a Borboleta usa sua própria
    # lista (MATERIAIS_SEDE_BORBOLETA, abaixo), sem os itens novos.
    MATERIAIS_SEDE = [
        ("AISI 304", "AISI 304"),
        ("AISI 304L", "AISI 304L"),
        ("AISI 316", "AISI 316"),
        ("AISI 316L", "AISI 316L"),
        ("AISI 321", "AISI 321"),
        ("AISI 347", "AISI 347"),
        ("AISI 410", "AISI 410"),
        ("STELLITE 6", "STELLITE 6"),
        ("MONEL 400", "MONEL 400"),
        ("MONEL K500", "MONEL K500"),
        ("ASTM A217 CA15", "ASTM A217 CA15"),
        ("ASTM A182 F51 + Grafite", "ASTM A182 F51 + Grafite"),
        ("ASTM A182 F316 + Grafite", "ASTM A182 F316 + Grafite"),
        ("ASTM A536 GR 65-45-12", "ASTM A536 GR 65-45-12"),
        ("ASTM A182 F53 + Grafite", "ASTM A182 F53 + Grafite"),
        ("INCONEL 625 + Grafite", "INCONEL 625 + Grafite"),
        ("ASTM A182 F55 + Grafite", "ASTM A182 F55 + Grafite"),
        ("ASTM A182 F6NM", "ASTM A182 F6NM"),
        ("AISI 304 + Stellite", "AISI 304 + Stellite"),
        ("AISI 317", "AISI 317"),
        ("B62", "B62"),
        ("ASTM B148 C95500", "ASTM B148 C95500"),
        ("ASTM B148 C95800", "ASTM B148 C95800"),
        ("BUNA N", "BUNA N"),
        ("ASTM A105N", "ASTM A105N"),
        ("ASTM A105N + ENP", "ASTM A105N + ENP"),
        ("ASTM A216 WCB", "ASTM A216 WCB"),
        ("ASTM A216 WCB (revestido em PTFE)", "ASTM A216 WCB (revestido em PTFE)"),
        ("Cromo duro", "Cromo duro"),
        ("Carbeto de Tungstênio", "Carbeto de Tungstênio"),
        ("ASTM A182 F51", "ASTM A182 F51"),
        ("ASTM A182 F53", "ASTM A182 F53"),
        ("ASTM A182 F55", "ASTM A182 F55"),
        ("ASTM A182 F60", "ASTM A182 F60"),
        ("ASTM A182 F61", "ASTM A182 F61"),
        ("ASTM A182 F71", "ASTM A182 F71"),
        ("ASTM A182 F51 + Stellite .21", "ASTM A182 F51 + Stellite .21"),
        ("DEVLON", "DEVLON"),
        ("EPDM", "EPDM"),
        ("INCONEL (UNS N06625)", "INCONEL (UNS N06625)"),
        ("INCONEL X-750 (UNS N07750)", "INCONEL X-750 (UNS N07750)"),
        ("ASTM A182 F5", "ASTM A182 F5"),
        ("ASTM A182 F5A", "ASTM A182 F5A"),
        ("ASTM A182 F9", "ASTM A182 F9"),
        ("ASTM A182 F91", "ASTM A182 F91"),
        ("UNS 04400", "UNS 04400"),
        ("AISI 420", "AISI 420"),
        ("AISI 430", "AISI 430"),
        ("XM-19", "XM-19"),
        ("17-4PH", "17-4PH"),
        ("MONEL", "MONEL"),
        ("AISI 304 + ENP", "AISI 304 + ENP"),
        ("AISI 410 + ENP", "AISI 410 + ENP"),
        ("Neoprene", "Neoprene"),
        ("Nylon 12", "Nylon 12"),
        ("PCTFE", "PCTFE"),
        ("PEEK", "PEEK"),
        ("PTFE", "PTFE"),
        ("RPTFE (25% C)", "RPTFE (25% C)"),
        ("RPTFE (25% FV)", "RPTFE (25% FV)"),
        ("Stellite .12", "Stellite .12"),
        ("Stellite .21", "Stellite .21"),
        ("VITON", "VITON"),
        ("UNS N06001", "UNS N06001"),
        ("AISI 304H", "AISI 304H"),
        ("INCONEL 718", "INCONEL 718"),
        ("ASTM A890/A995 4A", "ASTM A890/A995 4A"),
        ("ASTM A890/A995 5A", "ASTM A890/A995 5A"),
        ("ASTM A890/A995 6A", "ASTM A890/A995 6A"),
        ("ASTM A182 F51 + ENP", "ASTM A182 F51 + ENP"),
        ("ASTM A182 F53 + ENP", "ASTM A182 F53 + ENP"),
        ("ASTM A182 F55 + ENP", "ASTM A182 F55 + ENP"),
        ("ASTM B564 (UNS N06625)", "ASTM B564 (UNS N06625)"),
        ("ASTM B564 type 630", "ASTM B564 type 630"),
        ("Ni UNS N10276+Grafite", "Ni UNS N10276+Grafite"),
        ("UNS N08811", "UNS N08811"),
        ("AISI 316 + Stellite", "AISI 316 + Stellite"),
        ("Sede resiliente", "Sede resiliente"),
        ("Sede metal/metal", "Sede metal/metal"),
        ("Não aplicável", "Não aplicável"),
        ("AISI 410 + Stellite", "AISI 410 + Stellite"),
        ("CF8M", "CF8M"),
        ("AISI 304 + carbeto de tungstênio", "AISI 304 + carbeto de tungstênio"),
        ("AISI 316 + carbeto de tungstênio", "AISI 316 + carbeto de tungstênio"),
        ("AISI 410 + carbeto de tungstênio", "AISI 410 + carbeto de tungstênio"),
        ("NBR", "NBR"),
        ("Padrão fabricante", "Padrão fabricante"),
        ("ASTM A182 F316 + carbeto de Tungstênio", "ASTM A182 F316 + carbeto de Tungstênio"),
        ("ASTM A182 F6A", "ASTM A182 F6A"),
        ("ASTM A217 CA15 + Stellite", "ASTM A217 CA15 + Stellite"),
        ("ASTM A182 F6A + Stellite", "ASTM A182 F6A + Stellite"),
        ("ASTM A494 UNS N26625", "ASTM A494 UNS N26625"),
        ("ASTM B148 C95800 + Revestimento Metálico", "ASTM B148 C95800 + Revestimento Metálico"),
        ("ASTM B148 C95800/TC4 + Grafite", "ASTM B148 C95800/TC4 + Grafite"),
        ("AISI 317 + Stellite", "AISI 317 + Stellite"),
        ("INTEGRAL + STL", "INTEGRAL + STL"),
        ("ASTM A105 + STL", "ASTM A105 + STL"),
        ("ASTM A522 type 1 + Carbeto de Tungstênio", "ASTM A522 type 1 + Carbeto de Tungstênio"),
        ("ASTM A351 CF8M + Carbeto de Tungstênio", "ASTM A351 CF8M + Carbeto de Tungstênio"),
        ("ASTM A182 F51 + Carbeto de Tungstênio", "ASTM A182 F51 + Carbeto de Tungstênio"),
        ("ASTM A216 WCB + B62", "ASTM A216 WCB + B62"),
        ("ASTM A216 WCB + 13CR", "ASTM A216 WCB + 13CR"),
        ("ASTM A105 + B62", "ASTM A105 + B62"),
        ("ASTM A182 F316L + STL", "ASTM A182 F316L + STL"),
        ("ASTM A351 CF8M + STL", "ASTM A351 CF8M + STL"),
        ("ASTM A182 F11", "ASTM A182 F11"),
        ("ASTM A182 F11 + Stellite", "ASTM A182 F11 + Stellite"),
        ("ASTM A182 F91 + Stellite", "ASTM A182 F91 + Stellite"),
        ("INCONEL 625 + RPTFE (25% C)", "INCONEL 625 + RPTFE (25% C)"),
        ("ASTM A182 F6A + DEVLON V", "ASTM A182 F6A + DEVLON V"),
        ("ASTM A182 F51 + DEVLON", "ASTM A182 F51 + DEVLON"),
        ("ASTM A182 F316 + RPTFE", "ASTM A182 F316 + RPTFE"),
        ("ASTM A182 F51 + PEEK", "ASTM A182 F51 + PEEK"),
        ("B150 C63000", "B150 C63000"),
        ("INTEGRAL+STL. UNS 32760 + GRAPHITE", "INTEGRAL+STL. UNS 32760 + GRAPHITE"),
        ("ASTM A182 F51 + RPTFE (25% C)", "ASTM A182 F51 + RPTFE (25% C)"),
        ("ASTM F53 + Carbeto de Tungstênio", "ASTM F53 + Carbeto de Tungstênio"),
        ("AISI 431", "AISI 431"),
        ("ASTM A182 F55 + Carbeto de Tungstênio", "ASTM A182 F55 + Carbeto de Tungstênio"),
        ("ASTM A105 + ENP + DEVLON", "ASTM A105 + ENP + DEVLON"),
        ("ASTM A105 + ENP + PEEK", "ASTM A105 + ENP + PEEK"),
        ("ASTM A105 + ENP + RPTFE", "ASTM A105 + ENP + RPTFE"),
        ("INTEGRAL", "INTEGRAL"),
        ("AISI 321H + Stellite", "AISI 321H + Stellite"),
        ("AISI 321H", "AISI 321H"),
        ("INCONEL 625 + Carbeto de Tungstênio", "INCONEL 625 + Carbeto de Tungstênio"),
        ("INCONEL 718 + Carbeto de Tungstênio", "INCONEL 718 + Carbeto de Tungstênio"),
        ("ASTM A522 Type I", "ASTM A522 Type I"),
        ("PEEK + METAL", "PEEK + METAL"),
        ("INTEGRAL + SS316", "INTEGRAL + SS316"),
        ("PEEK XP108 com anéis de inserto em Inconel X750", "PEEK XP108 com anéis de inserto em Inconel X750"),
        ("AISI 4130", "AISI 4130"),
        ("MONEL 400 (UNS N04400)", "MONEL 400 (UNS N04400)"),
        ("INTEGRAL+MONEL 400 (UNS N04400)", "INTEGRAL+MONEL 400 (UNS N04400)"),
        ("F316+STL.6", "F316+STL.6"),
        ("C5+SS304", "C5+SS304"),
        ("F5+STL.6", "F5+STL.6"),
        ("INT+B62", "INT+B62"),
        ("ASTM A182 F6A + HFC", "ASTM A182 F6A + HFC"),
        ("INCONEL 718-API 6A", "INCONEL 718-API 6A"),
        ("A694 F60+TCC", "A694 F60+TCC"),
        ("ASTM A182 F6A + PEEK + PTFE", "ASTM A182 F6A + PEEK + PTFE"),
        ("ASTM A182 F6A+RPTFE", "ASTM A182 F6A+RPTFE"),
        ("UNS S32760 (SUPER DUPLEX) + CoCr Alloy (Stellite)", "UNS S32760 (SUPER DUPLEX) + CoCr Alloy (Stellite)"),
        ("ASTM A182 F316 + PEEK", "ASTM A182 F316 + PEEK"),
        ("ASTM A182 F53 + RPTFE (25% C)", "ASTM A182 F53 + RPTFE (25% C)"),
        ("AISI 416", "AISI 416"),
        ("ASTM A182 F53 + Stellite", "ASTM A182 F53 + Stellite"),
        ("ASTM A217 CA15 + CP", "ASTM A217 CA15 + CP"),
        ("AISI 410 + SF", "AISI 410 + SF"),
        ("ASTM A890/A995 6A + PTFE", "ASTM A890/A995 6A + PTFE"),
        ("AISI 410 + CP", "AISI 410 + CP"),
        ("AISI 316 SF", "AISI 316 SF"),
        ("ASTM A995 4A + SF", "ASTM A995 4A + SF"),
        ("STL/UNS S32760 + Grafite", "STL/UNS S32760 + Grafite"),
        ("STL/UNS S31803 + Grafite", "STL/UNS S31803 + Grafite"),
        ("A276 316", "A276 316"),
        ("AISI 410 + RPTFE (25% C)", "AISI 410 + RPTFE (25% C)"),
        ("AISI 410 + Carbeto de Cromo", "AISI 410 + Carbeto de Cromo"),
        ("ASTM A995 4A + RAM 21 (TCC)", "ASTM A995 4A + RAM 21 (TCC)"),
        ("ASTM A182 F55 + PEEK", "ASTM A182 F55 + PEEK"),
        ("UNS S32750 + RPTFE (25% C)", "UNS S32750 + RPTFE (25% C)"),
        ("A565 616HT", "A565 616HT"),
        ("ASTM A351 CF8M + CP", "ASTM A351 CF8M + CP"),
        ("B148 C95800 + STL.6", "B148 C95800 + STL.6"),
        ("ASTM A182 F6A Cl 2 + PEEK", "ASTM A182 F6A Cl 2 + PEEK"),
        ("A182 F6A + PEEK", "A182 F6A + PEEK"),
        ("CF8+PFA", "CF8+PFA"),
        ("CF8M+PFA", "CF8M+PFA"),
        ("ASTM A182 GR F316", "ASTM A182 GR F316"),
        ("17-4PH+PEEK", "17-4PH+PEEK"),
        ("ASTM A182 F53 + NYLON", "ASTM A182 F53 + NYLON"),
        ("WCB + STL", "WCB + STL"),
        ("ASTM B150 C63200", "ASTM B150 C63200"),
        ("ASTM A182 F304", "ASTM A182 F304"),
        ("ASTM A182 F55 + STL", "ASTM A182 F55 + STL"),
        ("AISI 410 + PEEK", "AISI 410 + PEEK"),
        ("ASTM A182 F55 + RPTFE (25% C)", "ASTM A182 F55 + RPTFE (25% C)"),
        ("AISI 410 + NYLON", "AISI 410 + NYLON"),
        ("ASTM A182 F316 + NYLON", "ASTM A182 F316 + NYLON"),
        ("AISI 316 + PTFE", "AISI 316 + PTFE"),
        ("MONEL + PTFE", "MONEL + PTFE"),
        ("ASTM A274 T316", "ASTM A274 T316"),
        ("TEFLON", "TEFLON"),
    ]

    MATERIAIS_SEDE_BORBOLETA = [
        ("BUNA N", "Buna N"),
        ("VITON", "Viton"),
        ("EPDM", "EPDM"),
        ("PTFE", "PTFE"),
        ("RPTFE (25% C)", "RPTFE (25% C)"),
        ("N/A", "N/A"),
    ]

    INSERTO_SEDE = [
        ("PEEK", "PEEK"),
        ("PTFE", "PTFE"),
        ("RPTFE (25% C)", "RPTFE (25% C)"),
        ("DEVLON", "DEVLON"),
        ("DEVLON V-API", "DEVLON V-API"),
        ("N/A", "N/A"),
    ]

    # Esfera, Gaveta, Globo, Globo Controle: haste com STELLITE 6 e MONEL
    MATERIAIS_HASTE = [
        ("AISI 304", "AISI 304"),
        ("AISI 304L", "AISI 304L"),
        ("AISI 316", "AISI 316"),
        ("AISI 316L", "AISI 316L"),
        ("AISI 321", "AISI 321"),
        ("AISI 347", "AISI 347"),
        ("AISI 410", "AISI 410"),
        ("STELLITE 6", "STELLITE 6"),
        ("STELLITE 21", "STELLITE 21"),
        ("MONEL 400", "MONEL 400"),
        ("MONEL K500", "MONEL K500"),
        ("ASTM A217 CA15", "ASTM A217 CA15"),
        ("ASTM A182 F51 + Grafite", "ASTM A182 F51 + Grafite"),
        ("ASTM A182 F316 + Grafite", "ASTM A182 F316 + Grafite"),
        ("ASTM A536 GR 65-45-12", "ASTM A536 GR 65-45-12"),
        ("ASTM A182 F53 + Grafite", "ASTM A182 F53 + Grafite"),
        ("Inconel 625 + Grafite", "Inconel 625 + Grafite"),
        ("ASTM A182 F55 + Grafite", "ASTM A182 F55 + Grafite"),
        ("ASTM A182 F6NM", "ASTM A182 F6NM"),
        ("CF3M", "CF3M"),
        ("AISI 317", "AISI 317"),
        ("B62", "B62"),
        ("ASTM B148 C95500", "ASTM B148 C95500"),
        ("ASTM B148 C95800", "ASTM B148 C95800"),
        ("BUNA N", "BUNA N"),
        ("ASTM A105N", "ASTM A105N"),
        ("ASTM A105N + ENP", "ASTM A105N + ENP"),
        ("ASTM A216 WCB", "ASTM A216 WCB"),
        ("ASTM A216 WCB (revestido em PTFE)", "ASTM A216 WCB (revestido em PTFE)"),
        ("Cromo duro", "Cromo duro"),
        ("Carbeto de Tungstênio", "Carbeto de Tungstênio"),
        ("ASTM A182 F51", "ASTM A182 F51"),
        ("ASTM A182 F53", "ASTM A182 F53"),
        ("ASTM A182 F55", "ASTM A182 F55"),
        ("ASTM A182 F60", "ASTM A182 F60"),
        ("ASTM A182 F61", "ASTM A182 F61"),
        ("ASTM A182 F71", "ASTM A182 F71"),
        ("AISI 316 + Stellite", "AISI 316 + Stellite"),
        ("DEVLON", "DEVLON"),
        ("EPDM", "EPDM"),
        ("INCONEL 625 (UNS N06625)", "INCONEL 625 (UNS N06625)"),
        ("INCONEL X-750 (UNS N07750)", "INCONEL X-750 (UNS N07750)"),
        ("ASTM A182 F5", "ASTM A182 F5"),
        ("ASTM A182 F5A", "ASTM A182 F5A"),
        ("ASTM A182 F9", "ASTM A182 F9"),
        ("ASTM A182 F91", "ASTM A182 F91"),
        ("UNS 04400", "UNS 04400"),
        ("AISI 420", "AISI 420"),
        ("AISI 430", "AISI 430"),
        ("XM-19", "XM-19"),
        ("17-4PH", "17-4PH"),
        ("MONEL", "MONEL"),
        ("AISI 304 + ENP", "AISI 304 + ENP"),
        ("AISI 410 + ENP", "AISI 410 + ENP"),
        ("Neoprene", "Neoprene"),
        ("Nylon 12", "Nylon 12"),
        ("PCTFE", "PCTFE"),
        ("PEEK", "PEEK"),
        ("PTFE", "PTFE"),
        ("RPTFE (25% C)", "RPTFE (25% C)"),
        ("RPTFE (25% FV)", "RPTFE (25% FV)"),
        ("Stellite .12", "Stellite .12"),
        ("Stellite .21", "Stellite .21"),
        ("Stellite .6", "Stellite .6"),
        ("VITON", "VITON"),
        ("UNS N06001", "UNS N06001"),
        ("AISI 304H", "AISI 304H"),
        ("INCONEL 718", "INCONEL 718"),
        ("ASTM A890/A995 4A", "ASTM A890/A995 4A"),
        ("ASTM A890/A995 5A", "ASTM A890/A995 5A"),
        ("ASTM A890/A995 6A", "ASTM A890/A995 6A"),
        ("AISI 316 + ENP", "AISI 316 + ENP"),
        ("ASTM A182 F51 + ENP", "ASTM A182 F51 + ENP"),
        ("ASTM A182 F53 + ENP", "ASTM A182 F53 + ENP"),
        ("ASTM A182 F55 + ENP", "ASTM A182 F55 + ENP"),
        ("ASTM B564 (UNS N06625)", "ASTM B564 (UNS N06625)"),
        ("ASTM B564 type 630", "ASTM B564 type 630"),
        ("UNS N08811", "UNS N08811"),
        ("AISI 304 + Stellite", "AISI 304 + Stellite"),
        ("AISI 410 + Stellite", "AISI 410 + Stellite"),
        ("CF8M", "CF8M"),
        ("Não aplicável", "Não aplicável"),
        ("AISI 304 + carbeto de tungstênio", "AISI 304 + carbeto de tungstênio"),
        ("AISI 316 + carbeto de tungstênio", "AISI 316 + carbeto de tungstênio"),
        ("AISI 410 + carbeto de tungstênio", "AISI 410 + carbeto de tungstênio"),
        ("AISI 410 + cromo duro", "AISI 410 + cromo duro"),
        ("AISI 304 + cromo duro", "AISI 304 + cromo duro"),
        ("AISI 316 + cromo duro", "AISI 316 + cromo duro"),
        ("ASTM A350 LF2 (ENP)", "ASTM A350 LF2 (ENP)"),
        ("ASTM A536 GR 65-45-12 + NYLON 11", "ASTM A536 GR 65-45-12 + NYLON 11"),
        ("AISI 316 + Ni60", "AISI 316 + Ni60"),
        ("Padrão fabricante", "Padrão fabricante"),
        ("ASTM A216 WCC", "ASTM A216 WCC"),
        ("ASTM A182 F316 + Carbeto de Tungstênio", "ASTM A182 F316 + Carbeto de Tungstênio"),
        ("ASTM A182 F6A", "ASTM A182 F6A"),
        ("ASTM A182 F316", "ASTM A182 F316"),
        ("ASTM A747 C", "ASTM A747 C"),
        ("ASTM A352 LCC + INCONEL (UNS N06625)", "ASTM A352 LCC + INCONEL (UNS N06625)"),
        ("A217 CA15 + Stellite", "A217 CA15 + Stellite"),
        ("A182 F6A + Stellite", "A182 F6A + Stellite"),
        ("A217 WC6 + Stellite", "A217 WC6 + Stellite"),
        ("A217 WC9 + Stellite", "A217 WC9 + Stellite"),
        ("AISI 410 + INCONEL (UNS N06625)", "AISI 410 + INCONEL (UNS N06625)"),
        ("INCONEL 625 + Carbeto de Tungstênio", "INCONEL 625 + Carbeto de Tungstênio"),
        ("ASTM A182 F55 + Carbeto de Tungstênio", "ASTM A182 F55 + Carbeto de Tungstênio"),
        ("ASTM A182 F51 + TCC", "ASTM A182 F51 + TCC"),
        ("A995 6A + STL", "A995 6A + STL"),
        ("ASTM A216 WCB + STL", "ASTM A216 WCB + STL"),
        ("ASTM A182 F6A + Carbeto de Tungstênio", "ASTM A182 F6A + Carbeto de Tungstênio"),
        ("ASTM A522 type 1 + Carbeto de Tungstênio", "ASTM A522 type 1 + Carbeto de Tungstênio"),
        ("A105 + 13CR", "A105 + 13CR"),
        ("ASTM A479 410", "ASTM A479 410"),
        ("ASTM A182 F304", "ASTM A182 F304"),
        ("ASTM A216 WCB + B62", "ASTM A216 WCB + B62"),
        ("ASTM A216 WCB + 13CR", "ASTM A216 WCB + 13CR"),
        ("ASTM A105 + B62", "ASTM A105 + B62"),
        ("ASTM A182 F316L + STL", "ASTM A182 F316L + STL"),
        ("ASTM A351 CF8M + STL", "ASTM A351 CF8M + STL"),
        ("ASTM A182 F11", "ASTM A182 F11"),
        ("ASTM A182 F11 + Stellite", "ASTM A182 F11 + Stellite"),
        ("ASTM A182 F91 + Stellite", "ASTM A182 F91 + Stellite"),
        ("M5 (17-4PH) + ST (Stellite .6)", "M5 (17-4PH) + ST (Stellite .6)"),
        ("B150 C63000", "B150 C63000"),
        ("A182 F55 + STL", "A182 F55 + STL"),
        ("ASTM A522 Type I", "ASTM A522 Type I"),
        ("AISI 431", "AISI 431"),
        ("ASTM A105 + ENP + DEVLON", "ASTM A105 + ENP + DEVLON"),
        ("ASTM A105 + ENP + PEEK", "ASTM A105 + ENP + PEEK"),
        ("ASTM A105 + ENP + RPTFE", "ASTM A105 + ENP + RPTFE"),
        ("ASTM A351 CF8", "ASTM A351 CF8"),
        ("AISI 321H + Stellite", "AISI 321H + Stellite"),
        ("AISI 321H", "AISI 321H"),
        ("INCONEL 718 + Carbeto de Tungstênio", "INCONEL 718 + Carbeto de Tungstênio"),
        ("ASTM A350 Gr LF3 + revestimento de solda INCONEL 625 + Carbeto de Tungstênio", "ASTM A350 Gr LF3 + revestimento de solda INCONEL 625 + Carbeto de Tungstênio"),
        ("INCONEL 625 + RPTFE (25% C)", "INCONEL 625 + RPTFE (25% C)"),
        ("ASTM A182 F6A Cl 2 + ENP", "ASTM A182 F6A Cl 2 + ENP"),
        ("ASTM A350 LF2 + INCONEL 625", "ASTM A350 LF2 + INCONEL 625"),
        ("ASTM A352 LCB", "ASTM A352 LCB"),
        ("UNS 32750 + Hard Chrome", "UNS 32750 + Hard Chrome"),
        ("AISI 4130", "AISI 4130"),
        ("MONEL 400 (UNS N04400)", "MONEL 400 (UNS N04400)"),
        ("INTEGRAL+MONEL 400 (UNS N04400)", "INTEGRAL+MONEL 400 (UNS N04400)"),
        ("F316+STL.6", "F316+STL.6"),
        ("C5+SS304", "C5+SS304"),
        ("F5+STL.6", "F5+STL.6"),
        ("CI+B62", "CI+B62"),
        ("ASTM A276 (UNS S32750)", "ASTM A276 (UNS S32750)"),
        ("F6A+HFC", "F6A+HFC"),
        ("INCONEL 718-API 6A", "INCONEL 718-API 6A"),
        ("A694 F60+TCC", "A694 F60+TCC"),
        ("A182 F6A+PEEK+PTFE", "A182 F6A+PEEK+PTFE"),
        ("A182 F6A+RPTFE", "A182 F6A+RPTFE"),
        ("ASTM A182 F316 + ENP", "ASTM A182 F316 + ENP"),
        ("ASTM A217 CA15 + SF", "ASTM A217 CA15 + SF"),
        ("AISI 410 + SF", "AISI 410 + SF"),
        ("AISI 316 SF", "AISI 316 SF"),
        ("ASTM A995 4A + SF", "ASTM A995 4A + SF"),
        ("A276 316", "A276 316"),
        ("Monel 400", "Monel 400"),
        ("ASTM A995 4A + RAM 21 (TCC)", "ASTM A995 4A + RAM 21 (TCC)"),
        ("A565 616HT", "A565 616HT"),
        ("AISI 410 Hardened", "AISI 410 Hardened"),
        ("ASTM A351 CF8M + FSF", "ASTM A351 CF8M + FSF"),
        ("A182 F6A + PEEK", "A182 F6A + PEEK"),
        ("ASTM A522 type 1 + carbeto de Tungstênio", "ASTM A522 type 1 + carbeto de Tungstênio"),
        ("CF8+PFA", "CF8+PFA"),
        ("CF8M+PFA", "CF8M+PFA"),
        ("17-4PH+Cr", "17-4PH+Cr"),
        ("F51+Cr", "F51+Cr"),
        ("ASTM A182 F55 + PEEK", "ASTM A182 F55 + PEEK"),
        ("ASTM A182 F53 + NYLON", "ASTM A182 F53 + NYLON"),
        ("13 CR", "13 CR"),
        ("AISI 410 + Carbeto de Cromo", "AISI 410 + Carbeto de Cromo"),
        ("ASTM A890/A995 6A + Carbeto de Tungstênio", "ASTM A890/A995 6A + Carbeto de Tungstênio"),
        ("AISI 316L + PTFE", "AISI 316L + PTFE"),
        ("AISI 410 Nitretado", "AISI 410 Nitretado"),
    ]

    MATERIAIS_HASTE_BORBOLETA = [
        ("AISI 304", "AISI 304"),
        ("AISI 304L", "AISI 304L"),
        ("AISI 316", "AISI 316"),
        ("AISI 316L", "AISI 316L"),
        ("AISI 321", "AISI 321"),
        ("AISI 347", "AISI 347"),
        ("AISI 410", "AISI 410"),
    ]

    MATERIAIS_HASTE_RETENCAO = [
        ("AISI 304", "AISI 304"),
        ("AISI 304L", "AISI 304L"),
        ("AISI 316", "AISI 316"),
        ("AISI 316L", "AISI 316L"),
        ("AISI 321", "AISI 321"),
        ("AISI 347", "AISI 347"),
        ("AISI 410", "AISI 410"),
    ]

    MATERIAIS_MOLAS = [
        ("AISI 304", "AISI 304"),
        ("AISI 316", "AISI 316"),
        ("INCONEL 625", "INCONEL 625"),
        ("INCONEL X750", "INCONEL X750"),
        ("N/A", "N/A"),
    ]

    MATERIAIS_MOLAS_RETENCAO = [
        ("AISI 304", "AISI 304"),
        ("AISI 304L", "AISI 304L"),
        ("AISI 316", "AISI 316"),
        ("AISI 316L", "AISI 316L"),
        ("AISI 321", "AISI 321"),
        ("AISI 347", "AISI 347"),
        ("AISI 410", "AISI 410"),
        ("MONEL 400", "MONEL 400"),
        ("MONEL K500", "MONEL K500"),
        ("ASTM A217 CA15", "ASTM A217 CA15"),
        ("ASTM A182 F51 + Grafite", "ASTM A182 F51 + Grafite"),
        ("ASTM A182 F316 + Grafite", "ASTM A182 F316 + Grafite"),
        ("ASTM A536 GR 65-45-12", "ASTM A536 GR 65-45-12"),
        ("ASTM A182 F53 + Grafite", "ASTM A182 F53 + Grafite"),
        ("Inconel 625 + Grafite", "Inconel 625 + Grafite"),
        ("ASTM A182 F55 + Grafite", "ASTM A182 F55 + Grafite"),
        ("ASTM A182 F6NM", "ASTM A182 F6NM"),
        ("CF3M", "CF3M"),
        ("AISI 317", "AISI 317"),
        ("B62", "B62"),
        ("ASTM B148 C95500", "ASTM B148 C95500"),
        ("ASTM B148 C95800", "ASTM B148 C95800"),
        ("BUNA N", "BUNA N"),
        ("ASTM A105N", "ASTM A105N"),
        ("ASTM A105N + ENP", "ASTM A105N + ENP"),
        ("ASTM A216 WCB", "ASTM A216 WCB"),
        ("ASTM A216 WCB (revestido em PTFE)", "ASTM A216 WCB (revestido em PTFE)"),
        ("Cromo duro", "Cromo duro"),
        ("Carbeto de Tungstênio", "Carbeto de Tungstênio"),
        ("ASTM A182 F51", "ASTM A182 F51"),
        ("ASTM A182 F53", "ASTM A182 F53"),
        ("ASTM A182 F55", "ASTM A182 F55"),
        ("ASTM A182 F60", "ASTM A182 F60"),
        ("ASTM A182 F61", "ASTM A182 F61"),
        ("ASTM A182 F71", "ASTM A182 F71"),
        ("AISI 316 + Stellite", "AISI 316 + Stellite"),
        ("DEVLON", "DEVLON"),
        ("EPDM", "EPDM"),
        ("INCONEL 625 (UNS N06625)", "INCONEL 625 (UNS N06625)"),
        ("INCONEL X-750 (UNS N07750)", "INCONEL X-750 (UNS N07750)"),
        ("ASTM A182 F5", "ASTM A182 F5"),
        ("ASTM A182 F5A", "ASTM A182 F5A"),
        ("ASTM A182 F9", "ASTM A182 F9"),
        ("ASTM A182 F91", "ASTM A182 F91"),
        ("UNS 04400", "UNS 04400"),
        ("AISI 420", "AISI 420"),
        ("AISI 430", "AISI 430"),
        ("XM-19", "XM-19"),
        ("17-4PH", "17-4PH"),
        ("MONEL", "MONEL"),
        ("AISI 304 + ENP", "AISI 304 + ENP"),
        ("AISI 410 + ENP", "AISI 410 + ENP"),
        ("Neoprene", "Neoprene"),
        ("Nylon 12", "Nylon 12"),
        ("PCTFE", "PCTFE"),
        ("PEEK", "PEEK"),
        ("PTFE", "PTFE"),
        ("RPTFE (25% C)", "RPTFE (25% C)"),
        ("RPTFE (25% FV)", "RPTFE (25% FV)"),
        ("Stellite .12", "Stellite .12"),
        ("Stellite .21", "Stellite .21"),
        ("Stellite .6", "Stellite .6"),
        ("VITON", "VITON"),
        ("UNS N06001", "UNS N06001"),
        ("AISI 304H", "AISI 304H"),
        ("INCONEL 718", "INCONEL 718"),
        ("ASTM A890/A995 4A", "ASTM A890/A995 4A"),
        ("ASTM A890/A995 5A", "ASTM A890/A995 5A"),
        ("ASTM A890/A995 6A", "ASTM A890/A995 6A"),
        ("AISI 316 + ENP", "AISI 316 + ENP"),
        ("ASTM A182 F51 + ENP", "ASTM A182 F51 + ENP"),
        ("ASTM A182 F53 + ENP", "ASTM A182 F53 + ENP"),
        ("ASTM A182 F55 + ENP", "ASTM A182 F55 + ENP"),
        ("ASTM B564 (UNS N06625)", "ASTM B564 (UNS N06625)"),
        ("ASTM B564 type 630", "ASTM B564 type 630"),
        ("UNS N08811", "UNS N08811"),
        ("AISI 304 + Stellite", "AISI 304 + Stellite"),
        ("AISI 410 + Stellite", "AISI 410 + Stellite"),
        ("CF8M", "CF8M"),
        ("Não aplicável", "Não aplicável"),
        ("AISI 304 + carbeto de tungstênio", "AISI 304 + carbeto de tungstênio"),
        ("AISI 316 + carbeto de tungstênio", "AISI 316 + carbeto de tungstênio"),
        ("AISI 410 + carbeto de tungstênio", "AISI 410 + carbeto de tungstênio"),
        ("AISI 410 + cromo duro", "AISI 410 + cromo duro"),
        ("AISI 304 + cromo duro", "AISI 304 + cromo duro"),
        ("AISI 316 + cromo duro", "AISI 316 + cromo duro"),
        ("ASTM A350 LF2 (ENP)", "ASTM A350 LF2 (ENP)"),
        ("ASTM A536 GR 65-45-12 + NYLON 11", "ASTM A536 GR 65-45-12 + NYLON 11"),
        ("AISI 316 + Ni60", "AISI 316 + Ni60"),
        ("Padrão fabricante", "Padrão fabricante"),
        ("ASTM A216 WCC", "ASTM A216 WCC"),
        ("ASTM A182 F316 + Carbeto de Tungstênio", "ASTM A182 F316 + Carbeto de Tungstênio"),
        ("ASTM A182 F6A", "ASTM A182 F6A"),
        ("ASTM A182 F316", "ASTM A182 F316"),
        ("ASTM A747 C", "ASTM A747 C"),
        ("ASTM A352 LCC + INCONEL (UNS N06625)", "ASTM A352 LCC + INCONEL (UNS N06625)"),
        ("A217 CA15 + Stellite", "A217 CA15 + Stellite"),
        ("A182 F6A + Stellite", "A182 F6A + Stellite"),
        ("A217 WC6 + Stellite", "A217 WC6 + Stellite"),
        ("A217 WC9 + Stellite", "A217 WC9 + Stellite"),
        ("AISI 410 + INCONEL (UNS N06625)", "AISI 410 + INCONEL (UNS N06625)"),
        ("INCONEL 625 + Carbeto de Tungstênio", "INCONEL 625 + Carbeto de Tungstênio"),
        ("ASTM A182 F55 + Carbeto de Tungstênio", "ASTM A182 F55 + Carbeto de Tungstênio"),
        ("ASTM A182 F51 + TCC", "ASTM A182 F51 + TCC"),
        ("A995 6A + STL", "A995 6A + STL"),
        ("ASTM A216 WCB + STL", "ASTM A216 WCB + STL"),
        ("ASTM A182 F6A + Carbeto de Tungstênio", "ASTM A182 F6A + Carbeto de Tungstênio"),
        ("ASTM A522 type 1 + Carbeto de Tungstênio", "ASTM A522 type 1 + Carbeto de Tungstênio"),
        ("A105 + 13CR", "A105 + 13CR"),
        ("ASTM A479 410", "ASTM A479 410"),
        ("ASTM A182 F304", "ASTM A182 F304"),
        ("ASTM A216 WCB + B62", "ASTM A216 WCB + B62"),
        ("ASTM A216 WCB + 13CR", "ASTM A216 WCB + 13CR"),
        ("ASTM A105 + B62", "ASTM A105 + B62"),
        ("ASTM A182 F316L + STL", "ASTM A182 F316L + STL"),
        ("ASTM A351 CF8M + STL", "ASTM A351 CF8M + STL"),
        ("ASTM A182 F11", "ASTM A182 F11"),
        ("ASTM A182 F11 + Stellite", "ASTM A182 F11 + Stellite"),
        ("ASTM A182 F91 + Stellite", "ASTM A182 F91 + Stellite"),
        ("M5 (17-4PH) + ST (Stellite .6)", "M5 (17-4PH) + ST (Stellite .6)"),
        ("B150 C63000", "B150 C63000"),
        ("A182 F55 + STL", "A182 F55 + STL"),
        ("ASTM A522 Type I", "ASTM A522 Type I"),
        ("AISI 431", "AISI 431"),
        ("ASTM A105 + ENP + DEVLON", "ASTM A105 + ENP + DEVLON"),
        ("ASTM A105 + ENP + PEEK", "ASTM A105 + ENP + PEEK"),
        ("ASTM A105 + ENP + RPTFE", "ASTM A105 + ENP + RPTFE"),
        ("ASTM A351 CF8", "ASTM A351 CF8"),
        ("AISI 321H + Stellite", "AISI 321H + Stellite"),
        ("AISI 321H", "AISI 321H"),
        ("INCONEL 718 + Carbeto de Tungstênio", "INCONEL 718 + Carbeto de Tungstênio"),
        ("ASTM A350 Gr LF3 + revestimento de solda INCONEL 625 + Carbeto de Tungstênio", "ASTM A350 Gr LF3 + revestimento de solda INCONEL 625 + Carbeto de Tungstênio"),
        ("INCONEL 625 + RPTFE (25% C)", "INCONEL 625 + RPTFE (25% C)"),
        ("ASTM A182 F6A Cl 2 + ENP", "ASTM A182 F6A Cl 2 + ENP"),
        ("ASTM A350 LF2 + INCONEL 625", "ASTM A350 LF2 + INCONEL 625"),
        ("ASTM A352 LCB", "ASTM A352 LCB"),
        ("UNS 32750 + Hard Chrome", "UNS 32750 + Hard Chrome"),
        ("AISI 4130", "AISI 4130"),
        ("MONEL 400 (UNS N04400)", "MONEL 400 (UNS N04400)"),
        ("INTEGRAL+MONEL 400 (UNS N04400)", "INTEGRAL+MONEL 400 (UNS N04400)"),
        ("F316+STL.6", "F316+STL.6"),
        ("C5+SS304", "C5+SS304"),
        ("F5+STL.6", "F5+STL.6"),
        ("CI+B62", "CI+B62"),
        ("ASTM A276 (UNS S32750)", "ASTM A276 (UNS S32750)"),
        ("F6A+HFC", "F6A+HFC"),
        ("INCONEL 718-API 6A", "INCONEL 718-API 6A"),
        ("A694 F60+TCC", "A694 F60+TCC"),
        ("A182 F6A+PEEK+PTFE", "A182 F6A+PEEK+PTFE"),
        ("A182 F6A+RPTFE", "A182 F6A+RPTFE"),
        ("ASTM A182 F316 + ENP", "ASTM A182 F316 + ENP"),
        ("ASTM A217 CA15 + SF", "ASTM A217 CA15 + SF"),
        ("AISI 410 + SF", "AISI 410 + SF"),
        ("AISI 316 SF", "AISI 316 SF"),
        ("ASTM A995 4A + SF", "ASTM A995 4A + SF"),
        ("A276 316", "A276 316"),
        ("Monel 400", "Monel 400"),
        ("ASTM A995 4A + RAM 21 (TCC)", "ASTM A995 4A + RAM 21 (TCC)"),
        ("A565 616HT", "A565 616HT"),
        ("AISI 410 Hardened", "AISI 410 Hardened"),
        ("ASTM A351 CF8M + FSF", "ASTM A351 CF8M + FSF"),
        ("A182 F6A + PEEK", "A182 F6A + PEEK"),
        ("ASTM A522 type 1 + carbeto de Tungstênio", "ASTM A522 type 1 + carbeto de Tungstênio"),
        ("CF8+PFA", "CF8+PFA"),
        ("CF8M+PFA", "CF8M+PFA"),
        ("17-4PH+Cr", "17-4PH+Cr"),
        ("F51+Cr", "F51+Cr"),
        ("ASTM A182 F55 + PEEK", "ASTM A182 F55 + PEEK"),
        ("ASTM A182 F53 + NYLON", "ASTM A182 F53 + NYLON"),
        ("13 CR", "13 CR"),
        ("AISI 410 + Carbeto de Cromo", "AISI 410 + Carbeto de Cromo"),
        ("ASTM A890/A995 6A + Carbeto de Tungstênio", "ASTM A890/A995 6A + Carbeto de Tungstênio"),
        ("AISI 316L + PTFE", "AISI 316L + PTFE"),
        ("AISI 410 Nitretado", "AISI 410 Nitretado"),
    ]

    VEDACAO_CORPO_TAMPA = [
        ("O'RING VITON", "O'Ring Viton"),
        ("O'RING BUNA N", "O'Ring Buna N"),
        ("O'RING EPDM", "O'Ring EPDM"),
        ("O'RING PTFE", "O'Ring PTFE"),
    ]

    # Vedação da junta (Esfera) — desacoplada da vedação sede/tampa (que virou O'Ring).
    # Mantém os itens que a junta tinha antes de sede/tampa mudar para O'Ring.
    VEDACAO_JUNTA_ESFERA = [
        ("JUNTA ESPIRALADA", "Junta Espiralada"),
        ("RTJ (FJA)", "RTJ (FJA)"),
        ("O'RING VITON", "O'Ring Viton"),
    ]

    VEDACAO_CORPO_TAMPA_GAVETA_GLOBO = [
        ("JUNTA ESPIRALADA", "Junta Espiralada"),
        ("RTJ (FJA)", "RTJ (FJA)"),
        ("PRESSURE SEAL", "Pressure Seal"),
        ("CASTELO SOLDADO", "Tampa Soldado"),
    ]

    VEDACAO_CORPO_TAMPA_RETENCAO = [
        ("JUNTA ESPIRALADA", "Junta Espiralada"),
        ("RTJ (FJA)", "RTJ (FJA)"),
        ("PRESSURE SEAL", "Pressure Seal"),
        ("CASTELO SOLDADO", "Castelo Soldado"),
    ]

    MATERIAIS_JUNTA = [
        ("AISI 304 + GRAFITE FLEXÍVEL", "AISI 304 + Grafite Flexível"),
        ("AISI 316 + GRAFITE FLEXÍVEL", "AISI 316 + Grafite Flexível"),
        ("S32750 + GRAFITE", "S32750 + Grafite"),
        ("PADRÃO FABRICANTE", "Padrão Fabricante"),
        ("AISI 304 + PTFE", "AISI 304 + PTFE"),
        ("AISI 316 + PTFE", "AISI 316 + PTFE"),
        ("AISI 304 + GRAFITE", "AISI 304 + Grafite"),
        ("AISI 316 + GRAFITE", "AISI 316 + Grafite"),
        ("AISI 304L + GRAFITE", "AISI 304L + Grafite"),
        ("AISI 304L + PTFE", "AISI 304L + PTFE"),
        ("AISI 316L + GRAFITE", "AISI 316L + Grafite"),
        ("AISI 316L + PTFE", "AISI 316L + PTFE"),
        ("GRAFITE", "Grafite"),
        ("GRAFITE + LIP SEAL", "Grafite + Lip Seal"),
        ("HNBR + GRAFITE", "HNBR + Grafite"),
        ("HNBR", "HNBR"),
        ("SELADO À PRESSÃO", "Selado à Pressão"),
        ("PTFE", "PTFE"),
        ("EPDM", "EPDM"),
        ("VITON", "Viton"),
        ("VITON + GRAFITE", "Viton + Grafite"),
        ("NÃO APLICÁVEL", "Não Aplicável"),
        ("AISI 347 + GRAFITE", "AISI 347 + Grafite"),
        ("AISI 317 + GRAFITE", "AISI 317 + Grafite"),
        ("AISI 321 + GRAFITE", "AISI 321 + Grafite"),
        ("AISI 321H + GRAFITE", "AISI 321H + Grafite"),
        ("S31803 + GRAFITE", "S31803 + Grafite"),
        ("AISI + PTFE", "AISI + PTFE"),
        ("S32760 + PTFE", "S32760 + PTFE"),
        ("S32550 + PTFE", "S32550 + PTFE"),
        ("PAPELÃO HIDRÁULICO C/ BORRACHA SBR", "Papelão Hidráulico c/ Borracha SBR"),
        ("N/A", "N/A"),
    ]

    # Esfera: sem N/A
    MATERIAIS_GAXETA_ESFERA = [
        ("GRAFITE", "Grafite"),
        ("GRAFITE FLEXÍVEL + FIO DE INCONEL", "Grafite Flexível + Fio de Inconel"),
        ("GRAFITE FLEXÍVEL + FIO DE INCONEL C/ INIBIDOR DE CORROSÃO", "Grafite Flex. + Fio Inconel c/ Inibidor Corrosão"),
        ("PTFE", "PTFE"),
    ]

    # Globo: com N/A
    MATERIAIS_GAXETA_GLOBO = [
        ("GRAFITE", "Grafite"),
        ("GRAFITE FLEXÍVEL + FIO DE INCONEL", "Grafite Flexível + Fio de Inconel"),
        ("GRAFITE FLEXÍVEL + FIO DE INCONEL C/ INIBIDOR DE CORROSÃO", "Grafite Flex. + Fio Inconel c/ Inibidor Corrosão"),
        ("PTFE", "PTFE"),
        ("N/A", "N/A"),
    ]

    # Gaveta: sem N/A, com item molibdato
    MATERIAIS_GAXETA_GAVETA = [
        ("GRAFITE", "Grafite"),
        ("GRAFITE FLEXÍVEL + FIO DE INCONEL", "Grafite Flexível + Fio de Inconel"),
        ("GRAFITE FLEXÍVEL + FIO DE INCONEL C/ INIBIDOR DE CORROSÃO", "Grafite Flex. + Fio Inconel c/ Inibidor Corrosão"),
        ("GRAFITE FLEXÍVEL + FIO DE INCONEL C/ INIBIDOR (molibdato de bário e/ou fios de zinco)", "Grafite Flex. + Fio Inconel c/ Inibidor (molibdato bário/zinco)"),
        ("PTFE", "PTFE"),
    ]

    # Borboleta: com N/A
    MATERIAIS_GAXETA_BORBOLETA = [
        ("GRAFITE", "Grafite"),
        ("GRAFITE FLEXÍVEL + FIO DE INCONEL", "Grafite Flexível + Fio de Inconel"),
        ("GRAFITE FLEXÍVEL + FIO DE INCONEL C/ INIBIDOR DE CORROSÃO", "Grafite Flex. + Fio Inconel c/ Inibidor Corrosão"),
        ("N/A", "N/A"),
    ]

    # Globo Controle: sem N/A
    MATERIAIS_GAXETA_GLOBO_CONTROLE = [
        ("GRAFITE", "Grafite"),
        ("GRAFITE FLEXÍVEL + FIO DE INCONEL", "Grafite Flexível + Fio de Inconel"),
        ("GRAFITE FLEXÍVEL + FIO DE INCONEL C/ INIBIDOR DE CORROSÃO", "Grafite Flex. + Fio Inconel c/ Inibidor Corrosão"),
        ("PTFE", "PTFE"),
    ]

    # Esfera, Globo Controle: sem N/A
    MATERIAIS_PARAFUSOS = [
        ("ASTM A193 B7", "ASTM A193 B7"),
        ("ASTM A193 B8", "ASTM A193 B8"),
        ("ASTM A193 Gr B8M", "ASTM A193 Gr B8M"),
        ("ASTM A193 Gr B8M CL2", "ASTM A193 Gr B8M CL2"),
        ("ASTM A193 Gr B16", "ASTM A193 Gr B16"),
        ("ASTM A320 Gr L7", "ASTM A320 Gr L7"),
        ("ASTM A193 Grade B7M", "ASTM A193 Grade B7M"),
        ("ASTM A193 Grade B8MA, Class 1A", "ASTM A193 Grade B8MA, Class 1A"),
        ("ASTM A320 Grade L7M", "ASTM A320 Grade L7M"),
        ("ASTM A193 B8A", "ASTM A193 B8A"),
        ("ASTM A193 B8T", "ASTM A193 B8T"),
        ("ZERON 100 FG", "Zeron 100 FG"),
        ("UNS S32760", "UNS S32760"),
        ("UNS S32550", "UNS S32550"),
        ("PADRÃO FABRICANTE", "Padrão Fabricante"),
        ("N/A", "N/A"),
    ]

    # Gaveta, Globo, Retenção: com N/A
    MATERIAIS_PARAFUSOS_COM_NA = [
        ("ASTM A193 B7", "ASTM A193 B7"),
        ("ASTM A193 B8", "ASTM A193 B8"),
        ("ASTM A193 Gr B8M", "ASTM A193 Gr B8M"),
        ("ASTM A193 Gr B8M CL2", "ASTM A193 Gr B8M CL2"),
        ("ASTM A193 Gr B16", "ASTM A193 Gr B16"),
        ("ASTM A320 Gr L7", "ASTM A320 Gr L7"),
        ("ASTM A193 Grade B7M", "ASTM A193 Grade B7M"),
        ("ASTM A193 Grade B8MA, Class 1A", "ASTM A193 Grade B8MA, Class 1A"),
        ("ASTM A320 Grade L7M", "ASTM A320 Grade L7M"),
        ("ASTM A193 B8A", "ASTM A193 B8A"),
        ("ASTM A193 B8T", "ASTM A193 B8T"),
        ("ZERON 100 FG", "Zeron 100 FG"),
        ("UNS S32760", "UNS S32760"),
        ("UNS S32550", "UNS S32550"),
        ("PADRÃO FABRICANTE", "Padrão Fabricante"),
        ("N/A", "N/A"),
    ]

    # Esfera, Globo Controle: sem N/A
    MATERIAIS_PORCAS = [
        ("ASTM A194 2H", "ASTM A194 2H"),
        ("ASTM A194 Gr 8", "ASTM A194 Gr 8"),
        ("ASTM A194 Gr 8M", "ASTM A194 Gr 8M"),
        ("ASTM A194 Gr 7", "ASTM A194 Gr 7"),
        ("ASTM A194 Gr 7L", "ASTM A194 Gr 7L"),
        ("ASTM A194 Gr 4", "ASTM A194 Gr 4"),
        ("ASTM A194 Gr 4L", "ASTM A194 Gr 4L"),
        ("ASTM A194 Grade 2HM", "ASTM A194 Grade 2HM"),
        ("ASTM A194 Grade 7M", "ASTM A194 Grade 7M"),
        ("ASTM A194 Grade 8MA", "ASTM A194 Grade 8MA"),
        ("ASTM A194 8A", "ASTM A194 8A"),
        ("ASTM A194 8T", "ASTM A194 8T"),
        ("ASTM A194 2H + HDG", "ASTM A194 2H + HDG"),
        ("ZERON 100 FG", "Zeron 100 FG"),
        ("UNS S32760", "UNS S32760"),
        ("UNS S32550", "UNS S32550"),
        ("PADRÃO FABRICANTE", "Padrão Fabricante"),
        ("N/A", "N/A"),
    ]

    # Gaveta, Globo, Retenção: com N/A
    MATERIAIS_PORCAS_COM_NA = [
        ("ASTM A194 2H", "ASTM A194 2H"),
        ("ASTM A194 Gr 8", "ASTM A194 Gr 8"),
        ("ASTM A194 Gr 8M", "ASTM A194 Gr 8M"),
        ("ASTM A194 Gr 7", "ASTM A194 Gr 7"),
        ("ASTM A194 Gr 7L", "ASTM A194 Gr 7L"),
        ("ASTM A194 Gr 4", "ASTM A194 Gr 4"),
        ("ASTM A194 Gr 4L", "ASTM A194 Gr 4L"),
        ("ASTM A194 Grade 2HM", "ASTM A194 Grade 2HM"),
        ("ASTM A194 Grade 7M", "ASTM A194 Grade 7M"),
        ("ASTM A194 Grade 8MA", "ASTM A194 Grade 8MA"),
        ("ASTM A194 8A", "ASTM A194 8A"),
        ("ASTM A194 8T", "ASTM A194 8T"),
        ("ASTM A194 2H + HDG", "ASTM A194 2H + HDG"),
        ("ZERON 100 FG", "Zeron 100 FG"),
        ("UNS S32760", "UNS S32760"),
        ("UNS S32550", "UNS S32550"),
        ("PADRÃO FABRICANTE", "Padrão Fabricante"),
        ("N/A", "N/A"),
    ]

    TIPO_MONTAGEM_ESFERA = [
        ("TRUNNION", "Trunnion"),
        ("FLUTUANTE", "Flutuante"),
    ]

    TIPO_PASSAGEM = [
        ("PLENA", "Plena"),
        ("REDUZIDA", "Reduzida"),
    ]

    TIPO_PASSAGEM_RETENCAO = [
        ("PLENA", "Plena"),
        ("REDUZIDA", "Reduzida"),
    ]

    TIPO_ACIONAMENTO = [
        ("ALAVANCA", "Alavanca"),
        ("VOLANTE", "Volante"),
        ("VOLANTE COM ENGRENAGEM DE REDUÇÃO", "Caixa de Redução com volante"),
        ("ATUADOR ELÉTRICO", "Atuador Elétrico"),
        ("ATUADOR ELÉTRICO COM VOLANTE", "Atuador Elétrico com Volante"),
        ("ATUADOR PNEUMÁTICO RETORNO POR MOLA TIPO PISTÃO", "Atuador Pneumático Retorno por Mola Tipo Pistão"),
        ("ATUADOR PNEUMÁTICO RETORNO POR MOLA TIPO DIAFRAGMA", "Atuador Pneumático Retorno por Mola Tipo Diafragma"),
        ("ATUADOR PNEUMÁTICO RETORNO POR MOLA COM VOLANTE TIPO PISTÃO", "Atuador Pneumático Ret. por Mola com Volante Tipo Pistão"),
        ("ATUADOR PNEUMÁTICO RETORNO POR MOLA COM VOLANTE TIPO DIAFRAGMA", "Atuador Pneumático Ret. por Mola com Volante Tipo Diafragma"),
        ("ATUADOR PNEUMÁTICO DUPLA AÇÃO TIPO PISTÃO", "Atuador Pneumático Dupla Ação tipo Pistão"),
        ("ATUADOR PNEUMÁTICO DUPLA AÇÃO TIPO DIAFRAGMA", "Atuador Pneumático Dupla Ação tipo Diafragma"),
        ("ATUADOR ELETROHIDRÁULICO RETORNO POR MOLA", "Atuador Eletrohidráulico Retorno por Mola"),
        ("ATUADOR ELETROHIDRÁULICO RETORNO POR MOLA COM VOLANTE", "Atuador Eletrohidr. Ret. por Mola com Volante"),
        ("ATUADOR ELETROHIDRÁULICO DUPLA AÇÃO", "Atuador Eletrohidráulico Dupla Ação"),
        ("ATUADOR ELETROHIDRÁULICO RETORNO POR MOLA COM VOLANTE", "Atuador Eletrohidr. Ret. por Mola com Volante"),
        ("ATUADOR ELETROHIDRAULICO RETORNO POR MOLA", "Atuador Eletrohidráulico Retorno por Mola"),
        ("N/A", "N/A"),
    ]

    # Marca do atuador: aparece assim que um acionamento é escolhido. Acionamentos
    # manuais (Alavanca/Volante/Volante c/ Caixa de Redução) travam em "Padrão Fabricante".
    MARCA_ATUADOR = [
        ("ROTORK", "Rotork"),
        ("LT", "LT"),
        ("BIFFI", "Biffi"),
        ("EXTRA", "Extra"),
        ("ZHONGHUAN", "Zhonghuan"),
        ("PADRÃO FABRICANTE", "Padrão Fabricante"),
    ]

    FLANGE_ACOPLAMENTO_ISO5211 = [
        ("F03", "F03"),
        ("F04", "F04"),
        ("F05", "F05"),
        ("F07", "F07"),
        ("F10", "F10"),
        ("F12", "F12"),
        ("F14", "F14"),
        ("F16", "F16"),
        ("F25", "F25"),
        ("F30", "F30"),
        ("F35", "F35"),
        ("F40", "F40"),
        ("F48", "F48"),
        ("F60", "F60"),
        ("N/A", "N/A")
    ]

    CONSTRUCAO_CORPO_ESFERA = [
        ("BI-PARTIDO", "Bi-partido"),
        ("TRI-PARTIDO", "Tri-partido"),
    ]

    DIB = [
        ("DBB", "DBB"),
        ("DIB-1", "DIB-1"),
        ("DIB-2", "DIB-2"),
        ("N/A", "N/A"),
    ]

    POSICAO_FALHA = [
        ("ABERTO", "Aberto"),
        ("FECHADA", "Fechada"),
        ("ULTIMA_POSICAO", "Última Posição"),
        ("N/A", "N/A"),
    ]

    FASE = [
        ("1", "1"),
        ("2", "2"),
        ("3", "3"),
        ("4", "4"),
    ]

    TENSAO = [(x, x) for x in ["120", "127", "220", "380", "440"]]

    FREQUENCIA = [(x, x) for x in ["55", "60"]]

    TIPO_CASTELO = [
        ("NORMAL", "Normal"),
        ("EXTENDIDO", "Extendido"),
    ]

    JUNCAO_CORPO_CASTELO = [
        ("APARAFUSADO", "Aparafusado"),
        ("SOLDADO", "Soldado"),
        ("ROSCADO", "Roscado"),
        ("ROSCADO E SOLDADO", "Roscado e Soldado"),
    ]

    JUNCAO_CORPO_CASTELO_RETENCAO = [
        ("APARAFUSADO", "Aparafusado"),
    ]

    # Retenção: tipo construtivo do obturador + configuração do corpo + orientação de
    # instalação. Dependência entre os 3 (validada em views.py):
    #   PISTAO  -> configuração Angular/Reto; orientação só Horizontal
    #   ESFERA  -> configuração Angular/Reto; orientação Horizontal/Vertical
    #   DISCO   -> configuração só Reto; orientação Horizontal/Vertical
    TIPO_RETENCAO = [
        ("PISTAO", "Pistão"),
        ("ESFERA", "Esfera"),
        ("DISCO", "Disco"),
    ]

    CONFIGURACAO_CORPO_RETENCAO = [
        ("ANGULAR", "Angular"),
        ("RETO", "Reto"),
    ]

    ORIENTACAO_INSTALACAO_RETENCAO = [
        ("HORIZONTAL", "Horizontal"),
        ("VERTICAL", "Vertical"),
    ]

    # API 594 (Seção 1): dois tipos construtivos — Tipo A (curto: wafer/lug/duplo-flange,
    # placa única ou dupla) e Tipo B (longo: bolted cover, flange ou solda de topo). Só
    # Retenção oferece a norma; só faz sentido quando norma = API 594.
    CATEGORIA_594 = [
        ("TIPO A", "Tipo A"),
        ("TIPO B", "Tipo B"),
    ]

    CATEGORIA_BORBOLETA = [
        ("CATEGORIA A", "Categoria A"),
        ("CATEGORIA B", "Categoria B"),
    ]

    FACE_A_FACE = [
        ("LUG", "Lug"),
        ("WAFER", "Wafer"),
        ("FLANGEADA PADRÃO CURTO", "Flangeada Padrão Curto"),
        ("FLANGEADA PADRÃO LONGO", "Flangeada Padrão Longo"),
        ("N/A", "N/A"),
    ]

    CONFIGURACAO_DISCO = [
        ("CONCÊNTRICA", "Concêntrica"),
        ("BI-EXCÊNTRICA", "Bi-Excêntrica"),
        ("TRI-EXCÊNTRICA", "Tri-Excêntrica"),
    ]

    # Esfera, Borboleta: sem N/A
    # IOGP — selecionável (mais opções podem ser adicionadas depois).
    IOGP = [
        ("IOGP AS-562", "IOGP AS-562"),
        ("N/A", "N/A"),
    ]

    USO_GERAL = [
        ("USO GERAL", "Uso Geral"),
        ("API 6FA", "API 6FA"),
        ("API 607", "API 607"),
        ("ISO 10497", "ISO 10497"),
    ]

    # Gaveta, Globo, Globo Controle: com N/A. Sem API 607: a norma (Secao 1) cobre
    # valvulas quarter-turn ou com sede nao-metalica; Gaveta/Globo/GC nao sao quarter-turn
    # e nao tem campo de sede/inserto nao-metalico no modelo (MATERIAIS_SEDE delas e' so
    # AISI/STELLITE/MONEL) -> nunca cai no escopo da norma.
    USO_GERAL_COM_NA = [
        ("USO GERAL", "Uso Geral"),
        ("API 6FA", "API 6FA"),
        ("API 607", "API 607"),
        ("ISO 10497", "ISO 10497"),
    ]

    CERTIFICACAO_SIL = [
        ("SIL 1", "SIL 1"),
        ("SIL 2", "SIL 2"),
        ("SIL 3", "SIL 3"),
        ("SIL 4", "SIL 4"),
        ("N/A", "N/A")
    ]

    NACE = [
        ("MR0103 ISO 17495", "MR0103 ISO 17495"),
        ("MR0175 ISO 15156", "MR0175 ISO 15156"),
        ("N/A", "N/A"),
    ]

    REVESTIMENTO = [
        ("DACROMETIZAÇÃO", "Dacrometização"),
        ("ZINCO NÍQUEL", "Zinco Níquel"),
        ("N/A", "N/A"),
    ]

    POSICIONADOR = [
        ("N/A", "N/A"),
        ("4-20 mA", "4-20 mA"),
        ("PROTOCOLO HART", "Protocolo Hart"),
        ("FIELDBUS", "Fieldbus"),
        ("PROFIBUS", "Profibus"),
    ]

    # Solenoide/Chave Fim de Curso/Sensor de Posição viraram Sim/Não (checkbox no form).
    CHAVE_FIM_CURSO = [("N/A", "N/A"), ("SIM", "Sim")]
    VALVULA_SOLENOIDE = [("N/A", "N/A"), ("SIM", "Sim")]
    VALVULA_LOCK_UP = [("N/A", "N/A"), ("2 VIAS", "2 Vias"), ("3 VIAS", "3 Vias")]
    SENSOR_POSICAO = [("N/A", "N/A"), ("SIM", "Sim")]
    VALVULA_ESCAPE_RAPIDO = [("N/A", "N/A"), ("2 VIAS", "2 Vias"), ("3 VIAS", "3 Vias")]

    IP = [("00", "00")] + [(str(n), str(n)) for n in range(10, 70)] + [('N/A', 'N/A')]

    # Características Elétricas (marcação Ex por subcategoria de instrumentação).
    # 5 partes independentes; juntas formam ex.: "Ex db IIC T6 Gb".
    CE_EX = [("Ex", "Ex")]
    CE_PROTECAO = [(x, x) for x in ["db", "db eb", "eb", "ec", "nA", "tb", "tc", "pxb", "pyb", "pzc", "i"]]
    CE_GRUPO = [(x, x) for x in ["I", "IIA", "IIB", "IIC", "IIIA", "IIIB", "IIIC"]]
    CE_TEMP = [(x, x) for x in ["T1", "T2", "T3", "T4", "T5", "T6"]]
    CE_EPL = [(x, x) for x in ["Ga", "Gb", "Gc"]]

    # Elétrica por subcategoria de instrumentação: tensão / corrente / potência
    TENSAO_ELET = [(x, x) for x in ["12 VDC", "12 VAC", "24 VDC", "24 VAC", "127 VAC", "120 VDC", "220 VAC"]]
    CORRENTE_ELET = [(f"{n} A", f"{n} A") for n in range(2, 51)]
    POTENCIA_ELET = [(f"{n} W", f"{n} W") for n in range(2, 51)]

    FILTRO = [
        ("SIM, COM MANÔMETROS", "Sim, com Manômetros"),
        ("SIM, SEM MANÔMETROS", "Sim, sem Manômetros"),
        ("SIM, COM MAN. ELEMENTO FILTRANTE 5 μ", "Sim, com Man. Elemento Filtrante 5 μ"),
        ("SIM, COM MAN. ELEMENTO FILTRANTE 5 μ CORPO ALUMÍNIO", "Sim, com Man. Elemento Filtrante 5 μ Corpo Alumínio"),
        ("SIM, COM MAN. ELEMENTO FILTRANTE 5 μ CORPO AÇO INOX", "Sim, com Man. Elemento Filtrante 5 μ Corpo Aço Inox"),
    ]

    TUBING = [
        ("INOX 316", "Inox 316"),
        ("INOX 304", "Inox 304"),
        ("COBRE", "Cobre"),
        ("COBRE REVESTIDO", "Cobre Revestido"),
    ]

    CARACTERISTICAS = [
        ("On - Off", "On - Off"),
        ("Linear", "Linear"),
        ("=%", "=%"),
        ("=% Modificado", "=% Modificado"),
        ("N/A", "N/A"),
    ]

    PLACA_IDENTIFICACAO = [
        ("AISI 316", "AISI 316"),
        ("AISI 304", "AISI 304"),
        ("Alumínio", "Alumínio"),
    ]

    FLANGE = [
        ("ASME B16.5", "ASME B16.5"),
        ("ASME B16.47", "ASME B16.47"),
        ("Norsok", "Norsok"),
    ]

    ANEXO_NBR_POR_TIPO = {
        "GAVETA": "Anexo A",
        "RETENCAO": "Anexo B",
        "ESFERA": "Anexo C",
    }

    # Materiais por tipo de válvula para formulário dinâmico
    MATERIAIS_POR_TIPO = {
        "ESFERA": {
            "CORPO_TAMPA": MATERIAIS_CORPO_TAMPA,
            "OBTURADOR": MATERIAIS_OBTURADOR_ESFERA,
            "SEDE": MATERIAIS_SEDE_ESFERA,
            "INSERTO_SEDE": INSERTO_SEDE,
            "HASTE": MATERIAIS_HASTE,
            "MOLAS": MATERIAIS_MOLAS,
            "JUNTA": VEDACAO_JUNTA_ESFERA,
            "MATERIAL_JUNTA": MATERIAIS_JUNTA,
            "GAXETA": MATERIAIS_GAXETA_ESFERA,
            "PARAFUSOS": MATERIAIS_PARAFUSOS,
            "PORCAS": MATERIAIS_PORCAS,
        },
        "GAVETA": {
            "CORPO_TAMPA": MATERIAIS_CORPO_TAMPA,
            "OBTURADOR": MATERIAIS_OBTURADOR,
            "SEDE": MATERIAIS_SEDE,
            "INSERTO_SEDE": [],  # Gaveta não tem inserto
            "HASTE": MATERIAIS_HASTE,
            "MOLAS": [],  # Gaveta não tem molas
            "JUNTA": VEDACAO_CORPO_TAMPA_GAVETA_GLOBO,
            "MATERIAL_JUNTA": MATERIAIS_JUNTA,
            "GAXETA": MATERIAIS_GAXETA_GAVETA,
            "PARAFUSOS": MATERIAIS_PARAFUSOS_COM_NA,
            "PORCAS": MATERIAIS_PORCAS_COM_NA,
        },
        "GLOBO": {
            "CORPO_TAMPA": MATERIAIS_CORPO_TAMPA,
            "OBTURADOR": MATERIAIS_OBTURADOR,
            "SEDE": MATERIAIS_SEDE,
            "INSERTO_SEDE": [],
            "HASTE": MATERIAIS_HASTE,
            "MOLAS": [],
            "JUNTA": VEDACAO_CORPO_TAMPA_GAVETA_GLOBO,
            "MATERIAL_JUNTA": MATERIAIS_JUNTA,
            "GAXETA": MATERIAIS_GAXETA_GLOBO,
            "PARAFUSOS": MATERIAIS_PARAFUSOS_COM_NA,
            "PORCAS": MATERIAIS_PORCAS_COM_NA,
        },
        "RETENCAO": {
            "CORPO_TAMPA": MATERIAIS_CORPO_TAMPA,
            "OBTURADOR": MATERIAIS_OBTURADOR,
            "SEDE": MATERIAIS_SEDE,
            "INSERTO_SEDE": INSERTO_SEDE,
            "HASTE": MATERIAIS_HASTE_RETENCAO,
            "MOLAS": MATERIAIS_MOLAS_RETENCAO,
            "JUNTA": VEDACAO_CORPO_TAMPA_RETENCAO,
            "MATERIAL_JUNTA": MATERIAIS_JUNTA,
            "GAXETA": [],  # Retenção não tem gaxeta
            "PARAFUSOS": MATERIAIS_PARAFUSOS_COM_NA,
            "PORCAS": MATERIAIS_PORCAS_COM_NA,
        },
        "BORBOLETA": {
            "CORPO_TAMPA": MATERIAIS_CORPO_BORBOLETA,
            "OBTURADOR": MATERIAIS_OBTURADOR_BORBOLETA,
            "SEDE": MATERIAIS_SEDE_BORBOLETA,
            "INSERTO_SEDE": [],
            "HASTE": MATERIAIS_HASTE_BORBOLETA,
            "MOLAS": [],
            "JUNTA": [],
            "GAXETA": MATERIAIS_GAXETA_BORBOLETA,
            "PARAFUSOS": [],
            "PORCAS": [],
        },
        "GLOBO_CONTROLE": {
            "CORPO_TAMPA": MATERIAIS_CORPO_TAMPA,
            "OBTURADOR": MATERIAIS_OBTURADOR,
            "SEDE": MATERIAIS_SEDE,
            "INSERTO_SEDE": [],
            "HASTE": MATERIAIS_HASTE,
            "MOLAS": [],
            "JUNTA": VEDACAO_CORPO_TAMPA_GAVETA_GLOBO,
            "MATERIAL_JUNTA": MATERIAIS_JUNTA,
            "GAXETA": MATERIAIS_GAXETA_GLOBO_CONTROLE,
            "PARAFUSOS": MATERIAIS_PARAFUSOS,
            "PORCAS": MATERIAIS_PORCAS,
        },
    }

    # Uso Geral por tipo (Esfera/Borboleta sem N/A, outros com N/A)
    USO_GERAL_POR_TIPO = {
        "ESFERA": USO_GERAL,
        "GAVETA": USO_GERAL_COM_NA,
        "GLOBO": USO_GERAL_COM_NA,
        "RETENCAO": [],  # Retenção não tem uso_geral
        "BORBOLETA": USO_GERAL,
        "GLOBO_CONTROLE": USO_GERAL_COM_NA,
    }
    
    # Classes por tipo
    CLASSES_POR_TIPO = {
        "ESFERA": CLASSES,
        "GAVETA": CLASSES,
        "GLOBO": CLASSES_RETENCAO_GLOBO,
        "RETENCAO": CLASSES_RETENCAO_GLOBO,
        "BORBOLETA": CLASSES_BORBOLETA,
        "GLOBO_CONTROLE": CLASSES_RETENCAO_GLOBO,
    }

    # Diâmetros por tipo
    DIAMETROS_POR_TIPO = {
        "ESFERA": DIAMETROS,
        "GAVETA": DIAMETROS,
        "GLOBO": DIAMETROS,
        "RETENCAO": DIAMETROS_RETENCAO,
        "BORBOLETA": DIAMETROS,
        "GLOBO_CONTROLE": DIAMETROS,
    }

    # Tipo de extremidade por tipo
    TIPO_EXTREMIDADE_POR_TIPO = {
        "ESFERA": TIPO_EXTREMIDADE,
        "GAVETA": TIPO_EXTREMIDADE,
        "GLOBO": TIPO_EXTREMIDADE,
        "RETENCAO": TIPO_EXTREMIDADE,
        "BORBOLETA": [],  # Borboleta não tem tipo de extremidade
        "GLOBO_CONTROLE": TIPO_EXTREMIDADE_GC,
    }

    # Tipo de acionamento por tipo
    TIPO_ACIONAMENTO_POR_TIPO = {
        "ESFERA": TIPO_ACIONAMENTO,
        "GAVETA": TIPO_ACIONAMENTO[1:],  # Sem ALAVANCA
        "GLOBO": TIPO_ACIONAMENTO[1:],  # Sem ALAVANCA
        "RETENCAO": [],  # Retenção não tem tipo de acionamento
        "BORBOLETA": TIPO_ACIONAMENTO,
        "GLOBO_CONTROLE": TIPO_ACIONAMENTO[1:],  # Sem ALAVANCA
    }

    # Tipo de passagem por tipo
    TIPO_PASSAGEM_POR_TIPO = {
        "ESFERA": TIPO_PASSAGEM,
        "GAVETA": TIPO_PASSAGEM,
        "GLOBO": TIPO_PASSAGEM,
        "RETENCAO": TIPO_PASSAGEM_RETENCAO,
        "BORBOLETA": [],  # Borboleta não tem tipo de passagem
        "GLOBO_CONTROLE": TIPO_PASSAGEM,
    }

    # Tipo de castelo por tipo
    TIPO_CASTELO_POR_TIPO = {
        "ESFERA": [],  # Esfera não tem tipo de castelo
        "GAVETA": TIPO_CASTELO,
        "GLOBO": TIPO_CASTELO,
        "RETENCAO": [],  # Retenção não tem tipo de castelo
        "BORBOLETA": [],  # Borboleta não tem tipo de castelo
        "GLOBO_CONTROLE": [],  # Globo Controle usa juncao_corpo_castelo, não tipo_castelo
    }

    # Junção corpo/castelo por tipo
    JUNCAO_CORPO_CASTELO_POR_TIPO = {
        "ESFERA": [],  # Esfera não tem junção corpo/castelo
        "GAVETA": JUNCAO_CORPO_CASTELO,
        "GLOBO": JUNCAO_CORPO_CASTELO,
        "RETENCAO": JUNCAO_CORPO_CASTELO_RETENCAO,
        "BORBOLETA": [],  # Borboleta não tem junção corpo/castelo
        "GLOBO_CONTROLE": JUNCAO_CORPO_CASTELO,
    }

    # Campos visíveis por tipo de válvula
    CAMPOS_POR_TIPO = {
        "ESFERA": [
            "fabricante", "pintura", "cor", "condicao_pintura",
            "norma", "iogp", "qsl", "nbr", "diametro", "classe", "tipo_extremidade", "tipo_ranhura",
            "tipo_montagem", "tipo_passagem", "tipo_acionamento", "marca_atuador", "flange_acoplamento", "construcao_corpo",
            "pintura_atuador", "cor_atuador", "condicao_pintura_atuador",
            "dib", "valvula_alivio", "dispositivo_antiestatico",
            "uso_geral", "baixa_emissao_fugitiva", "certificacao_sil", "nace", "revestimento",
            "posicionador", "ip_posicionador", "ex_posicionador", "protecao_posicionador", "grupo_posicionador", "temp_posicionador", "epl_posicionador", "tensao_posicionador", "corrente_posicionador", "potencia_posicionador",
            "chave_fim_curso", "ip_chave_fim_curso", "ex_chave_fim_curso", "protecao_chave_fim_curso", "grupo_chave_fim_curso", "temp_chave_fim_curso", "epl_chave_fim_curso", "tensao_chave_fim_curso", "corrente_chave_fim_curso", "potencia_chave_fim_curso",
            "valvula_solenoide", "ip_solenoide", "ex_solenoide", "protecao_solenoide", "grupo_solenoide", "temp_solenoide", "epl_solenoide", "tensao_solenoide", "corrente_solenoide", "potencia_solenoide",
            "valvula_lock_up", "sensor_posicao", "ip_sensor_posicao", "ex_sensor_posicao", "protecao_sensor_posicao", "grupo_sensor_posicao", "temp_sensor_posicao", "epl_sensor_posicao", "tensao_sensor_posicao", "corrente_sensor_posicao", "potencia_sensor_posicao", "valvula_escape_rapido",
            "caracteristicas", "dreno", "vent", "alivio_externo", "hot_disconnect", "indicador_posicao",
            "placa_identificacao", "flange", "anexo_nbr",
            "posicao_falha", "tensao", "fase", "frequencia",
        ],
        "GAVETA": [
            "fabricante", "pintura", "cor", "condicao_pintura",
            "norma", "iogp", "qsl", "nbr", "diametro", "classe", "tipo_extremidade", "tipo_ranhura",
            "tipo_passagem", "tipo_acionamento", "marca_atuador", "flange_acoplamento", "tipo_castelo", "juncao_corpo_castelo",
            "pintura_atuador", "cor_atuador", "condicao_pintura_atuador",
            "uso_geral", "baixa_emissao_fugitiva", "certificacao_sil", "nace", "revestimento",
            "posicionador", "ip_posicionador", "ex_posicionador", "protecao_posicionador", "grupo_posicionador", "temp_posicionador", "epl_posicionador", "tensao_posicionador", "corrente_posicionador", "potencia_posicionador",
            "chave_fim_curso", "ip_chave_fim_curso", "ex_chave_fim_curso", "protecao_chave_fim_curso", "grupo_chave_fim_curso", "temp_chave_fim_curso", "epl_chave_fim_curso", "tensao_chave_fim_curso", "corrente_chave_fim_curso", "potencia_chave_fim_curso",
            "valvula_solenoide", "ip_solenoide", "ex_solenoide", "protecao_solenoide", "grupo_solenoide", "temp_solenoide", "epl_solenoide", "tensao_solenoide", "corrente_solenoide", "potencia_solenoide",
            "valvula_lock_up", "sensor_posicao", "ip_sensor_posicao", "ex_sensor_posicao", "protecao_sensor_posicao", "grupo_sensor_posicao", "temp_sensor_posicao", "epl_sensor_posicao", "tensao_sensor_posicao", "corrente_sensor_posicao", "potencia_sensor_posicao", "valvula_escape_rapido",
            "caracteristicas", "dreno", "vent", "alivio_externo", "hot_disconnect", "indicador_posicao",
            "placa_identificacao", "flange", "anexo_nbr",
            "posicao_falha", "tensao", "fase", "frequencia",
        ],
        "GLOBO": [
            "fabricante", "pintura", "cor", "condicao_pintura",
            "norma", "iogp", "qsl", "nbr", "diametro", "classe", "tipo_extremidade", "tipo_ranhura",
            "tipo_passagem", "tipo_acionamento", "marca_atuador", "flange_acoplamento", "tipo_castelo", "juncao_corpo_castelo",
            "pintura_atuador", "cor_atuador", "condicao_pintura_atuador",
            "uso_geral", "baixa_emissao_fugitiva", "certificacao_sil", "nace", "revestimento",
            "posicionador", "ip_posicionador", "ex_posicionador", "protecao_posicionador", "grupo_posicionador", "temp_posicionador", "epl_posicionador", "tensao_posicionador", "corrente_posicionador", "potencia_posicionador",
            "chave_fim_curso", "ip_chave_fim_curso", "ex_chave_fim_curso", "protecao_chave_fim_curso", "grupo_chave_fim_curso", "temp_chave_fim_curso", "epl_chave_fim_curso", "tensao_chave_fim_curso", "corrente_chave_fim_curso", "potencia_chave_fim_curso",
            "valvula_solenoide", "ip_solenoide", "ex_solenoide", "protecao_solenoide", "grupo_solenoide", "temp_solenoide", "epl_solenoide", "tensao_solenoide", "corrente_solenoide", "potencia_solenoide",
            "valvula_lock_up", "sensor_posicao", "ip_sensor_posicao", "ex_sensor_posicao", "protecao_sensor_posicao", "grupo_sensor_posicao", "temp_sensor_posicao", "epl_sensor_posicao", "tensao_sensor_posicao", "corrente_sensor_posicao", "potencia_sensor_posicao", "valvula_escape_rapido",
            "caracteristicas", "dreno", "vent", "alivio_externo", "hot_disconnect", "indicador_posicao",
            "placa_identificacao", "flange",
            "posicao_falha", "tensao", "fase", "frequencia",
        ],
        "RETENCAO": [
            "fabricante", "pintura", "cor", "condicao_pintura",
            "norma", "iogp", "qsl", "nbr", "diametro", "classe", "tipo_extremidade", "tipo_ranhura",
            "tipo_passagem", "juncao_corpo_castelo", "nace", "revestimento",
            "tipo_retencao", "configuracao_corpo_retencao", "orientacao_instalacao", "categoria_594",
            "posicionador", "ip_posicionador", "ex_posicionador", "protecao_posicionador", "grupo_posicionador", "temp_posicionador", "epl_posicionador", "tensao_posicionador", "corrente_posicionador", "potencia_posicionador",
            "chave_fim_curso", "ip_chave_fim_curso", "ex_chave_fim_curso", "protecao_chave_fim_curso", "grupo_chave_fim_curso", "temp_chave_fim_curso", "epl_chave_fim_curso", "tensao_chave_fim_curso", "corrente_chave_fim_curso", "potencia_chave_fim_curso",
            "valvula_solenoide", "ip_solenoide", "ex_solenoide", "protecao_solenoide", "grupo_solenoide", "temp_solenoide", "epl_solenoide", "tensao_solenoide", "corrente_solenoide", "potencia_solenoide",
            "valvula_lock_up", "sensor_posicao", "ip_sensor_posicao", "ex_sensor_posicao", "protecao_sensor_posicao", "grupo_sensor_posicao", "temp_sensor_posicao", "epl_sensor_posicao", "tensao_sensor_posicao", "corrente_sensor_posicao", "potencia_sensor_posicao", "valvula_escape_rapido",
            "caracteristicas", "hot_disconnect", "indicador_posicao", "contra_peso",
            "placa_identificacao", "flange", "anexo_nbr",
            "posicao_falha", "tensao", "fase", "frequencia",
        ],
        "BORBOLETA": [
            "fabricante", "pintura", "cor", "condicao_pintura",
            "norma", "iogp", "qsl", "nbr", "diametro", "classe", "classe_pmt", "tipo_ranhura",
            "tipo_acionamento", "marca_atuador", "flange_acoplamento", "dispositivo_antiestatico",
            "pintura_atuador", "cor_atuador", "condicao_pintura_atuador",
            "categoria_borboleta", "face_a_face", "configuracao_disco",
            "uso_geral", "certificacao_sil", "nace", "revestimento",
            "posicionador", "ip_posicionador", "ex_posicionador", "protecao_posicionador", "grupo_posicionador", "temp_posicionador", "epl_posicionador", "tensao_posicionador", "corrente_posicionador", "potencia_posicionador",
            "chave_fim_curso", "ip_chave_fim_curso", "ex_chave_fim_curso", "protecao_chave_fim_curso", "grupo_chave_fim_curso", "temp_chave_fim_curso", "epl_chave_fim_curso", "tensao_chave_fim_curso", "corrente_chave_fim_curso", "potencia_chave_fim_curso",
            "valvula_solenoide", "ip_solenoide", "ex_solenoide", "protecao_solenoide", "grupo_solenoide", "temp_solenoide", "epl_solenoide", "tensao_solenoide", "corrente_solenoide", "potencia_solenoide",
            "valvula_lock_up", "sensor_posicao", "ip_sensor_posicao", "ex_sensor_posicao", "protecao_sensor_posicao", "grupo_sensor_posicao", "temp_sensor_posicao", "epl_sensor_posicao", "tensao_sensor_posicao", "corrente_sensor_posicao", "potencia_sensor_posicao", "valvula_escape_rapido",
            "caracteristicas", "hot_disconnect", "indicador_posicao",
            "placa_identificacao", "flange",
            "posicao_falha", "tensao", "fase", "frequencia",
        ],
        "GLOBO_CONTROLE": [
            "fabricante", "pintura", "cor", "condicao_pintura",
            "norma", "iogp", "qsl", "nbr", "diametro", "classe", "tipo_extremidade", "tipo_ranhura",
            "tipo_passagem", "tipo_acionamento", "marca_atuador", "flange_acoplamento", "juncao_corpo_castelo",
            "pintura_atuador", "cor_atuador", "condicao_pintura_atuador",
            "uso_geral", "baixa_emissao_fugitiva", "certificacao_sil", "nace", "revestimento",
            "posicionador", "ip_posicionador", "ex_posicionador", "protecao_posicionador", "grupo_posicionador", "temp_posicionador", "epl_posicionador", "tensao_posicionador", "corrente_posicionador", "potencia_posicionador", "filtro", "indicador_posicao", "tubing",
            "chave_fim_curso", "ip_chave_fim_curso", "ex_chave_fim_curso", "protecao_chave_fim_curso", "grupo_chave_fim_curso", "temp_chave_fim_curso", "epl_chave_fim_curso", "tensao_chave_fim_curso", "corrente_chave_fim_curso", "potencia_chave_fim_curso",
            "valvula_solenoide", "ip_solenoide", "ex_solenoide", "protecao_solenoide", "grupo_solenoide", "temp_solenoide", "epl_solenoide", "tensao_solenoide", "corrente_solenoide", "potencia_solenoide",
            "valvula_lock_up", "sensor_posicao", "ip_sensor_posicao", "ex_sensor_posicao", "protecao_sensor_posicao", "grupo_sensor_posicao", "temp_sensor_posicao", "epl_sensor_posicao", "tensao_sensor_posicao", "corrente_sensor_posicao", "potencia_sensor_posicao", "valvula_escape_rapido",
            "caracteristicas", "dreno", "hot_disconnect", "placa_identificacao", "flange",
            "posicao_falha", "tensao", "fase", "frequencia",
        ],
    }

    # Tipos de material obrigatórios por tipo de válvula
    TIPOS_MATERIAL_POR_TIPO = {
        "ESFERA": ["CORPO_TAMPA", "OBTURADOR", "SEDE", "INSERTO_SEDE", "HASTE", "MOLAS", "JUNTA", "MATERIAL_JUNTA", "GAXETA", "PARAFUSOS", "PORCAS"],
        "GAVETA": ["CORPO_TAMPA", "OBTURADOR", "SEDE", "HASTE", "JUNTA", "MATERIAL_JUNTA", "GAXETA", "PARAFUSOS", "PORCAS"],
        "GLOBO": ["CORPO_TAMPA", "OBTURADOR", "SEDE", "HASTE", "JUNTA", "MATERIAL_JUNTA", "GAXETA", "PARAFUSOS", "PORCAS"],
        "RETENCAO": ["CORPO_TAMPA", "OBTURADOR", "SEDE", "INSERTO_SEDE", "HASTE", "MOLAS", "JUNTA", "MATERIAL_JUNTA", "PARAFUSOS", "PORCAS"],
        "BORBOLETA": ["CORPO_TAMPA", "OBTURADOR", "SEDE", "HASTE", "GAXETA"],
        "GLOBO_CONTROLE": ["CORPO_TAMPA", "OBTURADOR", "SEDE", "HASTE", "JUNTA", "MATERIAL_JUNTA", "GAXETA", "PARAFUSOS", "PORCAS"],
    }

    # Vedações por tipo de válvula
    VEDACAO_POR_TIPO = {
        "ESFERA": VEDACAO_CORPO_TAMPA,
        "GAVETA": VEDACAO_CORPO_TAMPA_GAVETA_GLOBO,
        "GLOBO": VEDACAO_CORPO_TAMPA_GAVETA_GLOBO,
        "RETENCAO": VEDACAO_CORPO_TAMPA_RETENCAO,
        "BORBOLETA": [],
        "GLOBO_CONTROLE": VEDACAO_CORPO_TAMPA_GAVETA_GLOBO,
    }

    # Pintura absorve as normas: além de Padrão Fabricante / Sem Pintura, a própria
    # pintura já é a norma (N-442, N-1735, ...). Não há mais "Especial" nem select
    # separado de "Norma de Pintura". Cada norma define suas Condições (abaixo).
    PINTURA = [
        ("PADRÃO FABRICANTE", "Padrão Fabricante"),
        ("SEM PINTURA", "Sem pintura"),
        ("N-442", "N-442"),
        ("N-1735", "N-1735"),
        ("N-1374", "N-1374"),
        ("N-2912", "N-2912"),
    ]

    # Condições de exposição válidas para cada pintura/norma.
    CONDICAO_POR_NORMA_PINTURA = {
        "N-442": [(f"Condição {i}", f"Condição {i}") for i in range(1, 8)],
        "N-1735": [(f"Condição {i}", f"Condição {i}") for i in range(1, 9)],
        "N-1374": [
            ("Zona Submersa", "Zona Submersa"),
            ("Zona de Transição", "Zona de Transição"),
            ("Zona Atmosférica", "Zona Atmosférica"),
        ],
        "N-2912": [
            ("Tipo I", "Tipo I"),
            ("Tipo II", "Tipo II"),
            ("Tipo III", "Tipo III"),
        ],
    }

    # União (sem duplicatas) de todas as condições possíveis + valores forçados
    # (Padrão Fabricante / N/A), para choices do campo do modelo
    CONDICAO_PINTURA = list(dict.fromkeys(
        [("PADRÃO FABRICANTE", "Padrão Fabricante"), ("N/A", "N/A")]
        + [opt for opcoes in CONDICAO_POR_NORMA_PINTURA.values() for opt in opcoes]
    ))

    # Cor (pintura externa da válvula) — código Munsell/RAL conforme catálogo
    COR = [
        ("PADRÃO DO FABRICANTE", "PADRÃO DO FABRICANTE"),
        ("PRETO MUNSELL N 1 / RAL 9004", "PRETO MUNSELL N 1 / RAL 9004"),
        ("CINZA-ESCURO MUNSELL N 3.5", "CINZA-ESCURO MUNSELL N 3.5"),
        ("CINZA-CLARO MUNSELL N 6.5", "CINZA-CLARO MUNSELL N 6.5"),
        ("CINZA-GELO MUNSELL N 8 / RAL 7047", "CINZA-GELO MUNSELL N 8 / RAL 7047"),
        ("CINZA 0318 / RAL 9002", "CINZA 0318 / RAL 9002"),
        ("CINZA 0306 / 5GY8/1", "CINZA 0306 / 5GY8/1"),
        ("CINZA 0317 / RAL 7035", "CINZA 0317 / RAL 7035"),
        ("CINZA 2322 / RAL 7047", "CINZA 2322 / RAL 7047"),
        ("CINZA GELO 0304 / N-8,0", "CINZA GELO 0304 / N-8,0"),
        ("CINZA 0309 / 5BG7/0,4", "CINZA 0309 / 5BG7/0,4"),
        ("CINZA 0391 / 5B7/1", "CINZA 0391 / 5B7/1"),
        ("CINZA 2319 / RAL 7044", "CINZA 2319 / RAL 7044"),
        ("CINZA 0303 / 10Y7/1", "CINZA 0303 / 10Y7/1"),
        ("CINZA 0316 / RAL 7032", "CINZA 0316 / RAL 7032"),
        ("CINZA CLARO 0300 / N-6,5", "CINZA CLARO 0300 / N-6,5"),
        ("CINZA 0319 / RAL 7038", "CINZA 0319 / RAL 7038"),
        ("CINZA 0350 / RAL 7004", "CINZA 0350 / RAL 7004"),
        ("CINZA 0345 / 5GY6/1", "CINZA 0345 / 5GY6/1"),
        ("CINZA 0358 / RAL 7001", "CINZA 0358 / RAL 7001"),
        ("CINZA 1346 / RAL 7042", "CINZA 1346 / RAL 7042"),
        ("CINZA 0376 / N-5,5", "CINZA 0376 / N-5,5"),
        ("CINZA 0351 / RAL 7030", "CINZA 0351 / RAL 7030"),
        ("CINZA 2369 / RAL 7023", "CINZA 2369 / RAL 7023"),
        ("CINZA COSTADO 0357", "CINZA COSTADO 0357"),
        ("CINZA 0349 / 10B5/1", "CINZA 0349 / 10B5/1"),
        ("CINZA 0333 / RAL 7000", "CINZA 0333 / RAL 7000"),
        ("CINZA 0352 / RAL 7005", "CINZA 0352 / RAL 7005"),
        ("CINZA 0325 / RAL 7031", "CINZA 0325 / RAL 7031"),
        ("CINZA MÉDIO 0340 / N-5,0", "CINZA MÉDIO 0340 / N-5,0"),
        ("CINZA ESCURO 0380 / N-3,5", "CINZA ESCURO 0380 / N-3,5"),
        ("CINZA 1393 / RAL 7021", "CINZA 1393 / RAL 7021"),
        ("CINZA 0335 / RAL 7037", "CINZA 0335 / RAL 7037"),
        ("BRANCO MUNSELL N 9.5 / RAL 9003", "BRANCO MUNSELL N 9.5 / RAL 9003"),
        ("BRANCO-GELO MUNSELL N 8.5", "BRANCO-GELO MUNSELL N 8.5"),
        ("BRANCO 0100 / N-9,5", "BRANCO 0100 / N-9,5"),
        ("BRANCO 0101 / RAL 9010", "BRANCO 0101 / RAL 9010"),
        ("BRANCO 0111 / RAL 9001", "BRANCO 0111 / RAL 9001"),
        ("BRANCO 0119 / RAL 9018", "BRANCO 0119 / RAL 9018"),
        ("BRANCO 0123 / RAL 9003", "BRANCO 0123 / RAL 9003"),
        ("BRANCO 0133 / RAL 9016", "BRANCO 0133 / RAL 9016"),
        ("CARAMELO 0811 / 2,5YR4/8", "CARAMELO 0811 / 2,5YR4/8"),
        ("CASTANHO 0802 / 7,5YR5/6", "CASTANHO 0802 / 7,5YR5/6"),
        ("COR-DE-ALUMÍNIO RAL 9006", "COR-DE-ALUMÍNIO RAL 9006"),
        ("ALUMÍNIO LEAFING", "ALUMÍNIO LEAFING"),
        ("VINHO MUNSELL 5R 2/6 / RAL 3007", "VINHO MUNSELL 5R 2/6 / RAL 3007"),
        ("VERMELHO-SEGURANÇA MUNSELL 5R 4/14 / RAL 3001", "VERMELHO-SEGURANÇA MUNSELL 5R 4/14 / RAL 3001"),
        ("ÓXIDO DE FERRO MUNSELL 10R 3/6 / RAL 8012", "ÓXIDO DE FERRO MUNSELL 10R 3/6 / RAL 8012"),
        ("VERMELHO SEGURANÇA 0400 / 5R4/14", "VERMELHO SEGURANÇA 0400 / 5R4/14"),
        ("VERMELHO BOMBEIRO 0421", "VERMELHO BOMBEIRO 0421"),
        ("VERMELHO 0444 / RAL 3020", "VERMELHO 0444 / RAL 3020"),
        ("VERMELHO 0417 / SINAL", "VERMELHO 0417 / SINAL"),
        ("VERMELHO 0423 / RAL 3000", "VERMELHO 0423 / RAL 3000"),
        ("VERMELHO 0406 / 7,5R3/12", "VERMELHO 0406 / 7,5R3/12"),
        ("VERMELHO 0404 / 7,5R3/8", "VERMELHO 0404 / 7,5R3/8"),
        ("VERMELHO 1438 / 2,5YR4/8", "VERMELHO 1438 / 2,5YR4/8"),
        ("VERMELHO ÓXIDO 0412 / 10R3/6", "VERMELHO ÓXIDO 0412 / 10R3/6"),
        ("VERMELHO ÓXIDO 1405 / RAL 3009", "VERMELHO ÓXIDO 1405 / RAL 3009"),
        ("VERMELHO 0415 / RAL 3004", "VERMELHO 0415 / RAL 3004"),
        ("VERMELHO 0431 / 5R2/6", "VERMELHO 0431 / 5R2/6"),
        ("VERMELHO 1442 / RAL 3005", "VERMELHO 1442 / RAL 3005"),
        ("MARROM MUNSELL 2.5YR 2/4", "MARROM MUNSELL 2.5YR 2/4"),
        ("LARANJA-SEGURANÇA MUNSELL 2.5YR 6/14", "LARANJA-SEGURANÇA MUNSELL 2.5YR 6/14"),
        ("CREME MUNSELL 10YR 7/6", "CREME MUNSELL 10YR 7/6"),
        ("CREME-CLARO MUNSELL 2.5Y 9/4", "CREME-CLARO MUNSELL 2.5Y 9/4"),
        ("CREME 0633 / 2,5Y9/2", "CREME 0633 / 2,5Y9/2"),
        ("CREME CLARO 0631 / 2,5Y9/4", "CREME CLARO 0631 / 2,5Y9/4"),
        ("CREME 0636 / 2,5Y8/4", "CREME 0636 / 2,5Y8/4"),
        ("CREME 0639 / 2,5Y8/2", "CREME 0639 / 2,5Y8/2"),
        ("CREME CANALIZAÇÕES 0607 / 10YR7/6", "CREME CANALIZAÇÕES 0607 / 10YR7/6"),
        ("LARANJA 0206 / RAL 2003", "LARANJA 0206 / RAL 2003"),
        ("LARANJA 1201 / RAL 2008", "LARANJA 1201 / RAL 2008"),
        ("LARANJA SEGURANÇA 0200 / 2,5YR6/14", "LARANJA SEGURANÇA 0200 / 2,5YR6/14"),
        ("LARANJA 0211 / RAL 2004", "LARANJA 0211 / RAL 2004"),
        ("LARANJA 0247 / RAL 2011", "LARANJA 0247 / RAL 2011"),
        ("LARANJA 0209 / RAL 2002", "LARANJA 0209 / RAL 2002"),
        ("MARFIM 0646 / RAL 1015", "MARFIM 0646 / RAL 1015"),
        ("MARFIM 0668 / RAL 1014", "MARFIM 0668 / RAL 1014"),
        ("AMARELO 2677 / 7,5Y9/6", "AMARELO 2677 / 7,5Y9/6"),
        ("AMARELO SEGURANÇA 0600 / 5Y8/12", "AMARELO SEGURANÇA 0600 / 5Y8/12"),
        ("AMARELO PETROBRAS 0601 / 2,5Y8/12", "AMARELO PETROBRAS 0601 / 2,5Y8/12"),
        ("AMARELO 0697 / RAL 1021", "AMARELO 0697 / RAL 1021"),
        ("AMARELO 0666 / RAL 1023", "AMARELO 0666 / RAL 1023"),
        ("AMARELO 1650 / RAL 1012", "AMARELO 1650 / RAL 1012"),
        ("AMARELO 0628 / SINAL", "AMARELO 0628 / SINAL"),
        ("AMARELO 0681 / RAL 1003", "AMARELO 0681 / RAL 1003"),
        ("AMARELO 0609 / 10YR8/14", "AMARELO 0609 / 10YR8/14"),
        ("AMARELO 0676 / RAL 1004", "AMARELO 0676 / RAL 1004"),
        ("AMARELO 2693 / RAL 1032", "AMARELO 2693 / RAL 1032"),
        ("AMARELO 1631 / RAL 1028", "AMARELO 1631 / RAL 1028"),
        ("AMARELO 0651 / RAL 1007", "AMARELO 0651 / RAL 1007"),
        ("AMARELO 0608 / 7,5YR7/14", "AMARELO 0608 / 7,5YR7/14"),
        ("AMARELO 0613 / 10YR6/12", "AMARELO 0613 / 10YR6/12"),
        ("AMARELO CATERPILLAR 0677", "AMARELO CATERPILLAR 0677"),
        ("AREIA 0673 / RAL 1001", "AREIA 0673 / RAL 1001"),
        ("AREIA 1689 / RAL 1000", "AREIA 1689 / RAL 1000"),
        ("AREIA 2603 / RAL 1002", "AREIA 2603 / RAL 1002"),
        ("MARROM 0885 / 2,5Y4/6", "MARROM 0885 / 2,5Y4/6"),
        ("MARROM 0803 / 5YR4/4", "MARROM 0803 / 5YR4/4"),
        ("MARROM 0816 / 7,5YR3/6", "MARROM 0816 / 7,5YR3/6"),
        ("MARROM 0891 / RAL 8012", "MARROM 0891 / RAL 8012"),
        ("MARROM 0822 / RAL 8014", "MARROM 0822 / RAL 8014"),
        ("MARROM CANALIZAÇÕES 0800 / 2,5YR2/4", "MARROM CANALIZAÇÕES 0800 / 2,5YR2/4"),
        ("MARROM 0888 / RAL 8017", "MARROM 0888 / RAL 8017"),
        ("MARROM 0841 / RAL 8019", "MARROM 0841 / RAL 8019"),
        ("PÉROLA 0647 / RAL 1013", "PÉROLA 0647 / RAL 1013"),
        ("PRETO 0999 / N-1,0", "PRETO 0999 / N-1,0"),
        ("PÚRPURA SEGURANÇA 0180 / 10P4/10", "PÚRPURA SEGURANÇA 0180 / 10P4/10"),
        ("PÚRPURA 0188 / RAL 4001", "PÚRPURA 0188 / RAL 4001"),
        ("SÂNDALO 0641 / 7,5YR6/2", "SÂNDALO 0641 / 7,5YR6/2"),
        ("VERDE-SEGURANÇA MUNSELL 10GY 6/6", "VERDE-SEGURANÇA MUNSELL 10GY 6/6"),
        ("VERDE-PETROBRAS MUNSELL 2.5G 5/10 / RAL 6037", "VERDE-PETROBRAS MUNSELL 2.5G 5/10 / RAL 6037"),
        ("VERDE-PASTEL MUNSELL 5G 8/4 / RAL 6019", "VERDE-PASTEL MUNSELL 5G 8/4 / RAL 6019"),
        ("VERDE-EMBLEMA MUNSELL 2.5G 3/4", "VERDE-EMBLEMA MUNSELL 2.5G 3/4"),
        ("VERDE 0713 / 2,5G9/2", "VERDE 0713 / 2,5G9/2"),
        ("VERDE 2743 / 10GY8/4", "VERDE 2743 / 10GY8/4"),
        ("VERDE PASTEL 0700 / 5G8/4", "VERDE PASTEL 0700 / 5G8/4"),
        ("VERDE 0702 / 5GY8/4", "VERDE 0702 / 5GY8/4"),
        ("VERDE 2706 / 2,5G7/4", "VERDE 2706 / 2,5G7/4"),
        ("VERDE 0714 / 2,5G7/2", "VERDE 0714 / 2,5G7/2"),
        ("VERDE 0743 / RAL 6027", "VERDE 0743 / RAL 6027"),
        ("VERDE SEGURANÇA 0750 / 10GY6/6", "VERDE SEGURANÇA 0750 / 10GY6/6"),
        ("VERDE 0758 / RAL 6021", "VERDE 0758 / RAL 6021"),
        ("VERDE 0715 / 7,5G6/4", "VERDE 0715 / 7,5G6/4"),
        ("VERDE 0710 / 2,5G6/2", "VERDE 0710 / 2,5G6/2"),
        ("VERDE 0751 / 10GY5/4", "VERDE 0751 / 10GY5/4"),
        ("VERDE PETROBRAS 1737 / 2,5G5/10", "VERDE PETROBRAS 1737 / 2,5G5/10"),
        ("VERDE 0767 / RAL 6018", "VERDE 0767 / RAL 6018"),
        ("VERDE 0759 / RAL 6017", "VERDE 0759 / RAL 6017"),
        ("VERDE MÁQUINA 0757 / RAL 6011", "VERDE MÁQUINA 0757 / RAL 6011"),
        ("VERDE 0776 / RAL 6013", "VERDE 0776 / RAL 6013"),
        ("VERDE 0768 / 2,5G4/6", "VERDE 0768 / 2,5G4/6"),
        ("VERDE 0755 / 2,5G4/8", "VERDE 0755 / 2,5G4/8"),
        ("VERDE MÁQUINA 1778 / RAL 6010", "VERDE MÁQUINA 1778 / RAL 6010"),
        ("VERDE 0795 / SINAL", "VERDE 0795 / SINAL"),
        ("VERDE 0788 / 2,5G3/6", "VERDE 0788 / 2,5G3/6"),
        ("VERDE EMBLEMA 0780 / 2,5G3/4", "VERDE EMBLEMA 0780 / 2,5G3/4"),
        ("VERDE 2747 / RAL 6028", "VERDE 2747 / RAL 6028"),
        ("VERDE 1759 / RAL 6005", "VERDE 1759 / RAL 6005"),
        ("VERDE 1765 / RAL 6020", "VERDE 1765 / RAL 6020"),
        ("VERDE 2737 / RAL 6004", "VERDE 2737 / RAL 6004"),
        ("VERDE OTAN / NATO GREEN", "VERDE OTAN / NATO GREEN"),
        ("AZUL-SEGURANÇA MUNSELL 2.5PB 4/10", "AZUL-SEGURANÇA MUNSELL 2.5PB 4/10"),
        ("AZUL-PASTEL MUNSELL 2.5PB 8/4 / RAL EFFECT 610-4", "AZUL-PASTEL MUNSELL 2.5PB 8/4 / RAL EFFECT 610-4"),
        ("AZUL PASTEL 0510 / 2,5PB8/4", "AZUL PASTEL 0510 / 2,5PB8/4"),
        ("AZUL 0554 / 10B6/8", "AZUL 0554 / 10B6/8"),
        ("AZUL 0512 / 5PB6/8", "AZUL 0512 / 5PB6/8"),
        ("AZUL 1504 / RAL 5024", "AZUL 1504 / RAL 5024"),
        ("AZUL 0500 / 2,5PB5/6", "AZUL 0500 / 2,5PB5/6"),
        ("AZUL 0547 / 2,5PB5/8", "AZUL 0547 / 2,5PB5/8"),
        ("AZUL 0550 / RAL 5012", "AZUL 0550 / RAL 5012"),
        ("AZUL 0557 / RAL 5015", "AZUL 0557 / RAL 5015"),
        ("AZUL 0551 / SINAL", "AZUL 0551 / SINAL"),
        ("AZUL 0553 / RAL 5018", "AZUL 0553 / RAL 5018"),
        ("AZUL 2508 / 10B4/10", "AZUL 2508 / 10B4/10"),
        ("AZUL 2520 / RAL 5021", "AZUL 2520 / RAL 5021"),
        ("AZUL SEGURANÇA 0540 / 2,5PB4/10", "AZUL SEGURANÇA 0540 / 2,5PB4/10"),
        ("AZUL 0534 / RAL 5005", "AZUL 0534 / RAL 5005"),
        ("AZUL 0563 / RAL 5009", "AZUL 0563 / RAL 5009"),
        ("AZUL 2506 / RAL 5023", "AZUL 2506 / RAL 5023"),
        ("AZUL 0527 / RAL 5007", "AZUL 0527 / RAL 5007"),
        ("AZUL 0514 / RAL 5019", "AZUL 0514 / RAL 5019"),
        ("AZUL 0598 / RAL 5010", "AZUL 0598 / RAL 5010"),
        ("AZUL 0586 / 10B3/8", "AZUL 0586 / 10B3/8"),
        ("AZUL 0588 / 5PB3/8", "AZUL 0588 / 5PB3/8"),
        ("AZUL PETROBRAS 0587 / 7,5PB3/8", "AZUL PETROBRAS 0587 / 7,5PB3/8"),
        ("AZUL FRANÇA 1585", "AZUL FRANÇA 1585"),
        ("AZUL 0571 / RAL 5000", "AZUL 0571 / RAL 5000"),
        ("AZUL 2556 / 10B3/4", "AZUL 2556 / 10B3/4"),
        ("AZUL 2560 / 5PB2/8", "AZUL 2560 / 5PB2/8"),
        ("AZUL DEL REY 0558", "AZUL DEL REY 0558"),
        ("AZUL 0524 / 5B2/6", "AZUL 0524 / 5B2/6"),
        ("AZUL 2591 / 10B2/4", "AZUL 2591 / 10B2/4"),
        ("AZUL 0580 / 5PB2/4", "AZUL 0580 / 5PB2/4"),
        ("AZUL 2565 / RAL 5008", "AZUL 2565 / RAL 5008"),
        ("VIOLETA MUNSELL 10P 4/10 OU 2.5RP 4/10 OU 2.5P 3/8", "VIOLETA MUNSELL 10P 4/10 OU 2.5RP 4/10 OU 2.5P 3/8"),
        ("AZUL-MARINHO MUNSELL 5PB 2/4", "AZUL-MARINHO MUNSELL 5PB 2/4"),
        ("BORDÔ MUNSELL 7.5R 3/8", "BORDÔ MUNSELL 7.5R 3/8"),
        ("ROSA-SECO MUNSELL 2.5R 8/4", "ROSA-SECO MUNSELL 2.5R 8/4"),
        ("TURQUESA MUNSELL 7.5BG 6/8", "TURQUESA MUNSELL 7.5BG 6/8"),
        ("LILÁS MUNSELL 2.5P 6/18", "LILÁS MUNSELL 2.5P 6/18"),
        ("N/A", "N/A")
    ]

    # Fabricante (por enquanto só N/A — placeholder até cadastrar fabricantes reais)
    FABRICANTE = [
        ("DBV", "DBV"),
        ("FDV", "FDV"),
        ("YUANDA", "Yuanda"),
        ("WINWAY/JITAI", "Winway/Jitai"),
        ("NEWAY OIL EQUIPMENT", "Neway Oil Equipment"),
        ("ARFLU", "Arflu"),
        ("LJV", "LJV"),
        ("NEWAY", "Neway"),
        ("SHANXI", "Shanxi"),
        ("JUNPIN", "Junpin"),
        ("DEMBLA", "Dembla"),
        ("N/A", "N/A"),
    ]

    # === Campos do modelo ===

    id_valvula = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=40, unique=True, verbose_name="Código")
    tipo_valvula = models.CharField(max_length=20, choices=TIPO_VALVULA, verbose_name="Tipo de Válvula")
    funcao = models.CharField(max_length=20, choices=FUNCAO, default="BLOQUEIO", verbose_name="Função")
    fabricante = models.CharField(max_length=80, choices=FABRICANTE, blank=True, null=True, default="N/A", verbose_name="Fabricante")
    pintura = models.CharField(max_length=30, choices=PINTURA, blank=True, null=True, verbose_name="Pintura")
    cor = models.CharField(max_length=60, choices=COR, blank=True, null=True, verbose_name="Cor")
    # Aposentado: a norma agora vive no próprio campo "pintura". Coluna mantida só
    # para não perder dados antigos; não é mais preenchida/exibida.
    norma_pintura = models.CharField(max_length=20, blank=True, null=True, verbose_name="Norma de Pintura")
    condicao_pintura = models.CharField(max_length=40, choices=CONDICAO_PINTURA, blank=True, null=True, verbose_name="Condição de Pintura")
    projetos = models.ManyToManyField(
        "Projeto", related_name="valvulas", blank=True, verbose_name="Projetos",
    )
    norma = models.CharField(max_length=50, blank=True, verbose_name="Norma de Construção")
    iogp = models.CharField(max_length=20, choices=IOGP, blank=True, null=True, default="IOGP AS-562", verbose_name="IOGP")
    qsl = models.CharField(max_length=20, blank=True, verbose_name="QSL")
    nbr = models.BooleanField(default=False, verbose_name="NBR 15827")
    diametro = models.CharField(max_length=10, blank=True, verbose_name="Diâmetro")
    classe = models.CharField(max_length=20, blank=True, verbose_name="Classe")
    classe_pmt = models.CharField(max_length=50, blank=True, null=True, verbose_name="PMT")
    tipo_extremidade = models.CharField(max_length=60, blank=True, verbose_name="Tipo de Extremidade")
    tipo_ranhura = models.CharField(max_length=50, blank=True, verbose_name="Tipo de Ranhura")
    tipo_montagem = models.CharField(max_length=50, choices=TIPO_MONTAGEM_ESFERA, blank=True, null=True, verbose_name="Tipo de Montagem")
    tipo_acionamento = models.CharField(max_length=80, blank=True, verbose_name="Tipo de Acionamento")
    marca_atuador = models.CharField(max_length=30, choices=MARCA_ATUADOR, blank=True, null=True, verbose_name="Marca do Atuador")
    flange_acoplamento = models.CharField(max_length=10, choices=FLANGE_ACOPLAMENTO_ISO5211, blank=True, null=True, verbose_name="Flange de Acoplamento ISO 5211")
    pintura_atuador = models.CharField(max_length=30, choices=PINTURA, blank=True, null=True, verbose_name="Pintura do Atuador")
    cor_atuador = models.CharField(max_length=60, choices=COR, blank=True, null=True, verbose_name="Cor do Atuador")
    norma_pintura_atuador = models.CharField(max_length=20, blank=True, null=True, verbose_name="Norma de Pintura do Atuador")
    condicao_pintura_atuador = models.CharField(max_length=40, choices=CONDICAO_PINTURA, blank=True, null=True, verbose_name="Condição de Pintura do Atuador")
    construcao_corpo = models.CharField(max_length=50, choices=CONSTRUCAO_CORPO_ESFERA, blank=True, null=True, verbose_name="Construção do Corpo")
    dib = models.CharField(max_length=10, choices=DIB, blank=True, null=True, verbose_name="DIB")
    valvula_alivio = models.BooleanField(default=False, verbose_name="Válvula de Alívio / Dreno")
    dispositivo_antiestatico = models.BooleanField(default=False, verbose_name="Dispositivo Antiestático")
    tipo_passagem = models.CharField(max_length=20, choices=TIPO_PASSAGEM, blank=True, null=True, verbose_name="Tipo de Passagem")
    uso_geral = models.CharField(max_length=50, blank=True, null=True, verbose_name="Uso Geral / Testada a Fogo")
    baixa_emissao_fugitiva = models.BooleanField(default=False, verbose_name="Baixa Emissão Fugitiva")
    certificacao_sil = models.CharField(max_length=10, choices=CERTIFICACAO_SIL, blank=True, null=True, verbose_name="Certificação SIL")
    nace = models.CharField(max_length=30, choices=NACE, blank=True, null=True, verbose_name="NACE")
    revestimento = models.CharField(max_length=20, choices=REVESTIMENTO, blank=True, null=True, verbose_name="Revestimento")
    tipo_castelo = models.CharField(max_length=20, choices=TIPO_CASTELO, blank=True, null=True, verbose_name="Tipo de Castelo")
    juncao_corpo_castelo = models.CharField(max_length=30, choices=JUNCAO_CORPO_CASTELO, blank=True, null=True, verbose_name="Junção Corpo / Castelo")
    tipo_retencao = models.CharField(max_length=10, choices=TIPO_RETENCAO, blank=True, null=True, verbose_name="Tipo")
    configuracao_corpo_retencao = models.CharField(max_length=10, choices=CONFIGURACAO_CORPO_RETENCAO, blank=True, null=True, verbose_name="Configuração do Corpo")
    orientacao_instalacao = models.CharField(max_length=10, choices=ORIENTACAO_INSTALACAO_RETENCAO, blank=True, null=True, verbose_name="Orientação de Instalação")
    categoria_594 = models.CharField(max_length=10, choices=CATEGORIA_594, blank=True, null=True, verbose_name="Categoria (API 594)")
    categoria_borboleta = models.CharField(max_length=20, choices=CATEGORIA_BORBOLETA, blank=True, null=True, verbose_name="Categoria")
    face_a_face = models.CharField(max_length=50, choices=FACE_A_FACE, blank=True, null=True, verbose_name="Tipo de Conexão")
    configuracao_disco = models.CharField(max_length=20, choices=CONFIGURACAO_DISCO, blank=True, null=True, verbose_name="Configuração do Disco")

    # Campos exclusivos Globo Controle
    posicionador = models.CharField(max_length=50, choices=POSICIONADOR, blank=True, null=True, verbose_name="Posicionador")
    ip = models.CharField(max_length=5, choices=IP, blank=True, null=True, verbose_name="IP")
    # IP por subcategoria de instrumentação (Posicionador, Solenoid, Chave Fim de Curso, Sensor de Posição)
    ip_posicionador = models.CharField(max_length=5, choices=IP, blank=True, null=True, verbose_name="IP Posicionador")
    ip_solenoide = models.CharField(max_length=5, choices=IP, blank=True, null=True, verbose_name="IP Solenoid")
    ip_chave_fim_curso = models.CharField(max_length=5, choices=IP, blank=True, null=True, verbose_name="IP Chave Fim de Curso")
    ip_sensor_posicao = models.CharField(max_length=5, choices=IP, blank=True, null=True, verbose_name="IP Sensor de Posição")
    # Características Elétricas por subcategoria (5 partes cada): ex / proteção / grupo / temp / EPL
    ex_posicionador = models.CharField(max_length=10, choices=CE_EX, blank=True, null=True, verbose_name="Ex Posicionador")
    protecao_posicionador = models.CharField(max_length=10, choices=CE_PROTECAO, blank=True, null=True, verbose_name="Proteção Posicionador")
    grupo_posicionador = models.CharField(max_length=10, choices=CE_GRUPO, blank=True, null=True, verbose_name="Grupo Posicionador")
    temp_posicionador = models.CharField(max_length=10, choices=CE_TEMP, blank=True, null=True, verbose_name="Classe Temp. Posicionador")
    epl_posicionador = models.CharField(max_length=10, choices=CE_EPL, blank=True, null=True, verbose_name="EPL Posicionador")
    ex_solenoide = models.CharField(max_length=10, choices=CE_EX, blank=True, null=True, verbose_name="Ex Solenoid")
    protecao_solenoide = models.CharField(max_length=10, choices=CE_PROTECAO, blank=True, null=True, verbose_name="Proteção Solenoid")
    grupo_solenoide = models.CharField(max_length=10, choices=CE_GRUPO, blank=True, null=True, verbose_name="Grupo Solenoid")
    temp_solenoide = models.CharField(max_length=10, choices=CE_TEMP, blank=True, null=True, verbose_name="Classe Temp. Solenoid")
    epl_solenoide = models.CharField(max_length=10, choices=CE_EPL, blank=True, null=True, verbose_name="EPL Solenoid")
    ex_chave_fim_curso = models.CharField(max_length=10, choices=CE_EX, blank=True, null=True, verbose_name="Ex Chave Fim de Curso")
    protecao_chave_fim_curso = models.CharField(max_length=10, choices=CE_PROTECAO, blank=True, null=True, verbose_name="Proteção Chave Fim de Curso")
    grupo_chave_fim_curso = models.CharField(max_length=10, choices=CE_GRUPO, blank=True, null=True, verbose_name="Grupo Chave Fim de Curso")
    temp_chave_fim_curso = models.CharField(max_length=10, choices=CE_TEMP, blank=True, null=True, verbose_name="Classe Temp. Chave Fim de Curso")
    epl_chave_fim_curso = models.CharField(max_length=10, choices=CE_EPL, blank=True, null=True, verbose_name="EPL Chave Fim de Curso")
    ex_sensor_posicao = models.CharField(max_length=10, choices=CE_EX, blank=True, null=True, verbose_name="Ex Sensor de Posição")
    protecao_sensor_posicao = models.CharField(max_length=10, choices=CE_PROTECAO, blank=True, null=True, verbose_name="Proteção Sensor de Posição")
    grupo_sensor_posicao = models.CharField(max_length=10, choices=CE_GRUPO, blank=True, null=True, verbose_name="Grupo Sensor de Posição")
    temp_sensor_posicao = models.CharField(max_length=10, choices=CE_TEMP, blank=True, null=True, verbose_name="Classe Temp. Sensor de Posição")
    epl_sensor_posicao = models.CharField(max_length=10, choices=CE_EPL, blank=True, null=True, verbose_name="EPL Sensor de Posição")
    # Elétrica por subcategoria (tensão/corrente/potência)
    tensao_posicionador = models.CharField(max_length=10, choices=TENSAO_ELET, blank=True, null=True, verbose_name="Tensão Posicionador")
    corrente_posicionador = models.CharField(max_length=10, choices=CORRENTE_ELET, blank=True, null=True, verbose_name="Corrente Posicionador")
    potencia_posicionador = models.CharField(max_length=10, choices=POTENCIA_ELET, blank=True, null=True, verbose_name="Potência Posicionador")
    tensao_solenoide = models.CharField(max_length=10, choices=TENSAO_ELET, blank=True, null=True, verbose_name="Tensão Solenoid")
    corrente_solenoide = models.CharField(max_length=10, choices=CORRENTE_ELET, blank=True, null=True, verbose_name="Corrente Solenoid")
    potencia_solenoide = models.CharField(max_length=10, choices=POTENCIA_ELET, blank=True, null=True, verbose_name="Potência Solenoid")
    tensao_chave_fim_curso = models.CharField(max_length=10, choices=TENSAO_ELET, blank=True, null=True, verbose_name="Tensão Chave Fim de Curso")
    corrente_chave_fim_curso = models.CharField(max_length=10, choices=CORRENTE_ELET, blank=True, null=True, verbose_name="Corrente Chave Fim de Curso")
    potencia_chave_fim_curso = models.CharField(max_length=10, choices=POTENCIA_ELET, blank=True, null=True, verbose_name="Potência Chave Fim de Curso")
    tensao_sensor_posicao = models.CharField(max_length=10, choices=TENSAO_ELET, blank=True, null=True, verbose_name="Tensão Sensor de Posição")
    corrente_sensor_posicao = models.CharField(max_length=10, choices=CORRENTE_ELET, blank=True, null=True, verbose_name="Corrente Sensor de Posição")
    potencia_sensor_posicao = models.CharField(max_length=10, choices=POTENCIA_ELET, blank=True, null=True, verbose_name="Potência Sensor de Posição")
    filtro = models.CharField(max_length=80, choices=FILTRO, blank=True, null=True, verbose_name="Filtro")
    indicador_posicao = models.BooleanField(default=False, verbose_name="Indicador de Posição")
    tubing = models.CharField(max_length=20, choices=TUBING, blank=True, null=True, verbose_name="Tubing")
    chave_fim_curso = models.CharField(max_length=20, choices=CHAVE_FIM_CURSO, blank=True, null=True, verbose_name="Chave Fim de Curso")
    valvula_solenoide = models.CharField(max_length=20, choices=VALVULA_SOLENOIDE, blank=True, null=True, verbose_name="Válvula Solenoide")
    valvula_lock_up = models.CharField(max_length=20, choices=VALVULA_LOCK_UP, blank=True, null=True, verbose_name="Válvula Lock-Up")
    sensor_posicao = models.CharField(max_length=20, choices=SENSOR_POSICAO, blank=True, null=True, verbose_name="Sensor de Posição")
    valvula_escape_rapido = models.CharField(max_length=20, choices=VALVULA_ESCAPE_RAPIDO, blank=True, null=True, verbose_name="Válvula de Escape Rápido")
    caracteristicas = models.CharField(max_length=30, blank=True, null=True, verbose_name="Características")
    dreno = models.BooleanField(default=False, verbose_name="Dreno")
    vent = models.BooleanField(default=False, verbose_name="Vent")
    alivio_externo = models.BooleanField(default=False, verbose_name="Alívio Externo")
    hot_disconnect = models.BooleanField(default=False, verbose_name="Hot Disconnect")
    contra_peso = models.BooleanField(default=False, verbose_name="Contrapeso")
    placa_identificacao = models.CharField(max_length=20, blank=True, null=True, verbose_name="Placa de Identificação")
    flange = models.CharField(max_length=30, blank=True, null=True, verbose_name="Flange")
    anexo_nbr = models.CharField(max_length=20, blank=True, null=True, verbose_name="Anexo NBR")
    posicao_falha = models.CharField(max_length=20, choices=POSICAO_FALHA, blank=True, null=True, verbose_name="Posição em Caso de Falha")
    tensao = models.CharField(max_length=20, choices=TENSAO, blank=True, null=True, verbose_name="Tensão")
    fase = models.CharField(max_length=20, choices=FASE, blank=True, null=True, verbose_name="Fase")
    frequencia = models.CharField(max_length=20, choices=FREQUENCIA, blank=True, null=True, verbose_name="Frequência")
    observacao = models.TextField(max_length=1000, blank=True, default="", verbose_name="Observação")

    criado_por = models.ForeignKey(
        "Tb_Usuario", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="valvulas_criadas", verbose_name="Criado por",
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Válvula"
        verbose_name_plural = "Válvulas"
        ordering = ["-criado_em"]

    def __str__(self):
        return self.codigo

    def get_tipo_display_extended(self):
        return dict(self.TIPO_VALVULA).get(self.tipo_valvula, self.tipo_valvula)


class ValvulaMaterial(models.Model):
    TIPO_MATERIAL = [
        ("CORPO_TAMPA", "Corpo / Tampa"),
        ("OBTURADOR", "Obturador"),
        ("SEDE", "Sede / Porta Sede"),
        ("INSERTO_SEDE", "Inserto da Sede"),
        ("HASTE", "Haste"),
        ("MOLAS", "Molas"),
        ("JUNTA", "Categoria Junta"),
        ("MATERIAL_JUNTA", "Materiais da Junta"),
        ("GAXETA", "Gaxeta"),
        ("PARAFUSOS", "Parafusos"),
        ("PORCAS", "Porcas"),
    ]

    id = models.AutoField(primary_key=True)
    valvula = models.ForeignKey(Valvula, on_delete=models.CASCADE, related_name="materiais")
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    tipo_material = models.CharField(max_length=20, choices=TIPO_MATERIAL, verbose_name="Tipo de Material")

    def clean(self):
        # Regra de negócio: Para válvulas do tipo GAVETA com NBR 15827 habilitado,
        # a gaxeta deve ser GRAFITE FLEXÍVEL + FIO DE INCONEL C/ INIBIDOR (molibdato de bário e/ou fios de zinco)
        if self.tipo_material == 'GAXETA':
            if self.valvula.tipo_valvula == 'GAVETA' and self.valvula.nbr:
                specific_material = "GRAFITE FLEXÍVEL + FIO DE INCONEL C/ INIBIDOR (molibdato de bário e/ou fios de zinco)"
                if self.material.nome != specific_material:
                    from django.core.exceptions import ValidationError
                    raise ValidationError({
                        'material': f"Para válvulas do tipo GAVETA com NBR 15827 habilitado, a gaxeta deve ser: {specific_material}"
                    })

    class Meta:
        verbose_name = "Material da Válvula"
        verbose_name_plural = "Materiais da Válvula"
        unique_together = ["valvula", "tipo_material"]

    def __str__(self):
        tipo = dict(self.TIPO_MATERIAL).get(self.tipo_material, self.tipo_material)
        return f"{self.valvula.codigo} - {tipo}: {self.material.nome}"


class Vedacao(models.Model):
    id_vedacao = models.AutoField(primary_key=True)
    valvula = models.ForeignKey(Valvula, on_delete=models.CASCADE, related_name="vedacoes")
    vedacao_corpo_tampa = models.CharField(max_length=100, verbose_name="Vedação Sede / Tampa")
    vedacao_junta = models.CharField(max_length=100, blank=True, default="", verbose_name="Vedação da Junta")

    class Meta:
        verbose_name = "Vedação"
        verbose_name_plural = "Vedações"

    def __str__(self):
        return f"Vedação {self.valvula.codigo}: {self.vedacao_corpo_tampa}"


class ComponentesInternos(models.Model):
    id = models.AutoField(primary_key=True)
    valvula = models.ForeignKey(Valvula, on_delete=models.CASCADE, related_name="componentes")
    inserto_rede = models.CharField(max_length=100, blank=True, default="", verbose_name="Inserto da Sede")

    class Meta:
        verbose_name = "Componente Interno"
        verbose_name_plural = "Componentes Internos"

    def __str__(self):
        return f"Componentes {self.valvula.codigo}: {self.inserto_rede}"


class AnexoValvula(models.Model):
    """Arquivo anexo (PDF/imagem) de uma válvula. Conteúdo vive no Supabase Storage;
    aqui guardamos apenas a chave do objeto e os metadados."""
    id = models.AutoField(primary_key=True)
    valvula = models.ForeignKey(Valvula, on_delete=models.CASCADE, related_name="anexos")
    storage_key = models.CharField(max_length=500, unique=True, verbose_name="Chave no Storage")
    nome_original = models.CharField(max_length=255, verbose_name="Nome do Arquivo")
    content_type = models.CharField(max_length=100, blank=True, default="", verbose_name="Tipo MIME")
    tamanho = models.PositiveIntegerField(default=0, verbose_name="Tamanho (bytes)")
    enviado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Anexo da Válvula"
        verbose_name_plural = "Anexos da Válvula"
        ordering = ["-enviado_em"]

    def __str__(self):
        return f"Anexo {self.valvula.codigo}: {self.nome_original}"


class StorageBlob(models.Model):
    """Conteúdo binário de anexos armazenado no banco (fallback quando Supabase não configurado)."""
    key = models.TextField(unique=True, verbose_name="Chave do objeto")
    data = models.BinaryField(verbose_name="Conteúdo")

    class Meta:
        verbose_name = "Blob de Storage"
        verbose_name_plural = "Blobs de Storage"

    def __str__(self):
        return self.key


class TentativaDuplicata(models.Model):
    """Registra tentativas de criação de válvula que bateram em duplicata (HTTP 409).
    Usado nas estatísticas para medir quantas criações idênticas foram barradas."""
    id = models.AutoField(primary_key=True)
    tipo_valvula = models.CharField(max_length=20, choices=Valvula.TIPO_VALVULA, verbose_name="Tipo de Válvula")
    valvula_existente = models.ForeignKey(
        Valvula, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="tentativas_duplicata", verbose_name="Válvula Existente",
    )
    usuario = models.ForeignKey(
        Tb_Usuario, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="tentativas_duplicata", verbose_name="Usuário",
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Tentativa de Duplicata"
        verbose_name_plural = "Tentativas de Duplicata"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Duplicata {self.tipo_valvula} em {self.criado_em:%d/%m/%Y %H:%M}"
   
# .
