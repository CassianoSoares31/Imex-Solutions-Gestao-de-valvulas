import json

from django import forms
from django.forms import inlineformset_factory
from .models import Valvula, ValvulaMaterial, Vedacao, ComponentesInternos, Material

# Campos de instrumentação por subcategoria: Caract. Elétricas (ex/protecao/grupo/temp/epl)
# + Alimentação (tensao/corrente/potencia). 4 subcategorias × 8 = 32 campos.
_INSTR_SUBS = ["posicionador", "solenoide", "chave_fim_curso", "sensor_posicao"]
_INSTR_ELET_FIELDS = [
    f"{p}_{s}" for s in _INSTR_SUBS
    for p in ("ex", "protecao", "grupo", "temp", "epl", "tensao", "corrente", "potencia")
]


class ValvulaForm(forms.ModelForm):
    class Meta:
        model = Valvula
        fields = [
            "tipo_valvula", "funcao", "fabricante", "pintura", "cor", "condicao_pintura", "norma", "iogp", "qsl", "nbr", "diametro", "classe", "classe_pmt",
            "tipo_extremidade", "tipo_ranhura", "tipo_montagem",
            "tipo_passagem", "tipo_acionamento", "marca_atuador", "flange_acoplamento", "construcao_corpo",
            "pintura_atuador", "cor_atuador", "condicao_pintura_atuador",
            "dib", "valvula_alivio", "dispositivo_antiestatico",
            "uso_geral", "baixa_emissao_fugitiva", "certificacao_sil",
            "nace", "revestimento", "tipo_castelo", "juncao_corpo_castelo",
            "tipo_retencao", "configuracao_corpo_retencao", "orientacao_instalacao", "categoria_594",
            "categoria_borboleta", "face_a_face", "configuracao_disco",
            "posicionador", "ip", "ip_posicionador", "ip_solenoide", "ip_chave_fim_curso", "ip_sensor_posicao",
            "filtro", "indicador_posicao", "tubing",
            "chave_fim_curso", "valvula_solenoide", "valvula_lock_up", "sensor_posicao", "valvula_escape_rapido",
            "caracteristicas", "dreno", "vent", "alivio_externo", "hot_disconnect", "contra_peso", "placa_identificacao", "flange", "anexo_nbr",
            "posicao_falha", "tensao", "fase", "frequencia",
            "observacao",
        ] + _INSTR_ELET_FIELDS
        widgets = {
            "tipo_valvula": forms.Select(attrs={"class": "form-select", "id": "id_tipo_valvula"}),
            "funcao": forms.Select(attrs={"class": "form-select", "id": "id_funcao"}),
            "fabricante": forms.Select(attrs={"class": "form-select"}),
            "pintura": forms.Select(attrs={"class": "form-select"}),
            "cor": forms.Select(attrs={"class": "form-select"}),
            "condicao_pintura": forms.Select(attrs={"class": "form-select"}),
            "norma": forms.Select(attrs={"class": "form-select"}),
            "iogp": forms.Select(attrs={"class": "form-select"}),
            "qsl": forms.Select(attrs={"class": "form-select"}),
            "nbr": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "diametro": forms.Select(attrs={"class": "form-select"}),
            "classe": forms.Select(attrs={"class": "form-select"}),
            "classe_pmt": forms.TextInput(attrs={"class": "form-control", "placeholder": "Informe a PMT"}),
            "tipo_extremidade": forms.Select(attrs={"class": "form-select"}),
            "tipo_ranhura": forms.Select(attrs={"class": "form-select"}),
            "tipo_montagem": forms.Select(attrs={"class": "form-select"}),
            "tipo_passagem": forms.Select(attrs={"class": "form-select"}),
            "tipo_acionamento": forms.Select(attrs={"class": "form-select"}),
            "marca_atuador": forms.Select(attrs={"class": "form-select"}),
            "flange_acoplamento": forms.Select(attrs={"class": "form-select"}),
            "construcao_corpo": forms.Select(attrs={"class": "form-select"}),
            "dib": forms.Select(attrs={"class": "form-select"}),
            "pintura_atuador": forms.Select(attrs={"class": "form-select"}),
            "cor_atuador": forms.Select(attrs={"class": "form-select"}),
            "condicao_pintura_atuador": forms.Select(attrs={"class": "form-select"}),
            "valvula_alivio": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "dispositivo_antiestatico": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "uso_geral": forms.Select(attrs={"class": "form-select"}),
            "baixa_emissao_fugitiva": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "certificacao_sil": forms.Select(attrs={"class": "form-select"}),
            "nace": forms.Select(attrs={"class": "form-select"}),
            "revestimento": forms.Select(attrs={"class": "form-select"}),
            "tipo_castelo": forms.Select(attrs={"class": "form-select"}),
            "juncao_corpo_castelo": forms.Select(attrs={"class": "form-select"}),
            "tipo_retencao": forms.Select(attrs={"class": "form-select"}),
            "configuracao_corpo_retencao": forms.Select(attrs={"class": "form-select"}),
            "orientacao_instalacao": forms.Select(attrs={"class": "form-select"}),
            "categoria_594": forms.Select(attrs={"class": "form-select"}),
            "categoria_borboleta": forms.Select(attrs={"class": "form-select"}),
            "face_a_face": forms.Select(attrs={"class": "form-select"}),
            "configuracao_disco": forms.Select(attrs={"class": "form-select"}),
            "posicionador": forms.Select(attrs={"class": "form-select"}),
            "ip": forms.Select(attrs={"class": "form-select"}),
            "ip_posicionador": forms.Select(attrs={"class": "form-select"}),
            "ip_solenoide": forms.Select(attrs={"class": "form-select"}),
            "ip_chave_fim_curso": forms.Select(attrs={"class": "form-select"}),
            "ip_sensor_posicao": forms.Select(attrs={"class": "form-select"}),
            "filtro": forms.Select(attrs={"class": "form-select"}),
            "indicador_posicao": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "tubing": forms.Select(attrs={"class": "form-select"}),
            "chave_fim_curso": forms.Select(attrs={"class": "form-select"}),
            "valvula_solenoide": forms.Select(attrs={"class": "form-select"}),
            "valvula_lock_up": forms.Select(attrs={"class": "form-select"}),
            "sensor_posicao": forms.Select(attrs={"class": "form-select"}),
            "valvula_escape_rapido": forms.Select(attrs={"class": "form-select"}),
            "dreno": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "vent": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "alivio_externo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "hot_disconnect": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "contra_peso": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "posicao_falha": forms.Select(attrs={"class": "form-select"}),
            "tensao": forms.Select(attrs={"class": "form-select"}),
            "fase": forms.Select(attrs={"class": "form-select"}),
            "frequencia": forms.Select(attrs={"class": "form-select"}),
            "observacao": forms.Textarea(attrs={"class": "form-control", "rows": 3, "maxlength": 1000, "placeholder": "Observações (máx. 1000 caracteres)"}),
        }

    def __init__(self, *args, **kwargs):
        tipo_valvula = kwargs.pop("tipo_valvula", None)
        super().__init__(*args, **kwargs)
        campos_bool = ["nbr", "valvula_alivio", "dispositivo_antiestatico",
                       "baixa_emissao_fugitiva", "indicador_posicao", "dreno", "vent", "alivio_externo",
                       "hot_disconnect", "contra_peso"]
        if tipo_valvula:
            campos_visiveis = Valvula.CAMPOS_POR_TIPO.get(tipo_valvula, [])
            for campo in self.fields:
                if campo == "tipo_valvula":
                    continue
                if campo in campos_bool:
                    self.fields[campo].required = False
                elif campo not in campos_visiveis:
                    self.fields[campo].required = False


class ValvulaMaterialForm(forms.ModelForm):
    class Meta:
        model = ValvulaMaterial
        fields = ["tipo_material", "material"]

    def __init__(self, *args, **kwargs):
        tipo_valvula = kwargs.pop("tipo_valvula", None)
        super().__init__(*args, **kwargs)
        if tipo_valvula:
            tipos = Valvula.TIPOS_MATERIAL_POR_TIPO.get(tipo_valvula, [])
            self.fields["tipo_material"].choices = [("", "---------")] + tipos


class VedacaoForm(forms.ModelForm):
    class Meta:
        model = Vedacao
        fields = ["vedacao_corpo_tampa", "vedacao_junta"]

    def __init__(self, *args, **kwargs):
        tipo_valvula = kwargs.pop("tipo_valvula", None)
        super().__init__(*args, **kwargs)
        if tipo_valvula:
            opcoes = Valvula.VEDACAO_POR_TIPO.get(tipo_valvula, [])
            self.fields["vedacao_corpo_tampa"].choices = [("", "---------")] + opcoes
            self.fields["vedacao_junta"].choices = [("", "---------")] + opcoes


class ComponentesInternosForm(forms.ModelForm):
    class Meta:
        model = ComponentesInternos
        fields = ["inserto_rede"]

    def __init__(self, *args, **kwargs):
        tipo_valvula = kwargs.pop("tipo_valvula", None)
        super().__init__(*args, **kwargs)
        if tipo_valvula:
            opcoes = Valvula.MATERIAIS_POR_TIPO.get(tipo_valvula, {}).get("INSERTO_SEDE", [])
            self.fields["inserto_rede"].choices = [("", "---------")] + opcoes


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ["nome"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nome do material"}),
        }


class PesquisaForm(forms.Form):
    codigo = forms.CharField(
        max_length=40, required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Buscar por código...", "autofocus": True}),
    )
    tipo_valvula = forms.ChoiceField(
        choices=[], required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipo_valvula"].choices = [("", "Todos")] + Valvula.TIPO_VALVULA


ValvulaMaterialFormSet = inlineformset_factory(
    Valvula, ValvulaMaterial, form=ValvulaMaterialForm, extra=1, can_delete=True
)
VedacaoFormSet = inlineformset_factory(
    Valvula, Vedacao, form=VedacaoForm, extra=1, can_delete=True
)
ComponentesInternosFormSet = inlineformset_factory(
    Valvula, ComponentesInternos, form=ComponentesInternosForm, extra=1, can_delete=True
)
# .
