import spacy
import re
from spacy.language import Language
from spacy.matcher import Matcher
from spacy.util import filter_spans


# =====================================================
# REGEX COMPLEMENTAR (Dados pessoais explícitos)
# =====================================================
REGEX_PATTERNS = {

     # Identificadores Pessoais
    "CPF_CNPJ": r'\b\d{3,}\.\d{3,}[\d\.-]*\b',
    "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "TELEFONE": r'\(?\d{2}\)?\s?(?:9\d{4}|\d{4})[-.\s]?\d{4}',
    "PROCESSO_SEI": r'\b\d{4,6}-\d{6,10}/\d{4}-\d{2}\b',
    "ENDERECO": r"\b(Rua|Avenida|Av\.|Quadra|Lote)\b",
    
    # Veículos
    "VEICULO_PLACA": r'\b[A-Z]{3}[-\s]?\d[A-Z0-9]\d{2}\b',
    "VEICULO_RENAVAM": r'(?i)renavam[\s\.:]*\d+',
    
    # Serviços Públicos (DF)
    "DADO_INSCRICAO_GERAL": r'(?i)(?:inscrição|matricula|matrícula)[\s\.:nºo-]\d+(?:[\.-]\d+)',
    "DADO_ENERGIA": r'(?i)(?:unidade\s+consumidora|instalação|código\s+cliente)[\s\.:nºo-]*\d+',
    "DADO_IPTU_TLP": r'(?i)(?:iptu|tlp)[\s\.:nºo-]*\d+',
    "DADO_HIDROMETRO": r'(?i)hidr[ôo]metro[\s\.:nºo-]*\w+',
    "DADO_BANCARIO": r'(?i)(?:agência|conta\s+corrente|pix)[\s\.:nºo-]*[\d-]+',
}



# ==============================================================================
# LISTAS DE EXCEÇÃO (WHITE LISTS)
# Termos que o modelo deve IGNORAR, mesmo que pareçam nomes ou entidades.
# ==============================================================================
LOCAIS_IGNORADOS = {
    "plano piloto", "gama", "taguatinga", "brazlândia", "brazlandia",
    "sobradinho", "planaltina", "paranoá", "paranoa", "núcleo bandeirante",
    "ceilândia", "ceilandia", "guará", "guara", "cruzeiro", "samambaia", 
    "santa maria", "são sebastião", "recanto das emas", "lago sul", "lago norte",
    "riacho fundo", "candangolândia", "águas claras", "aguas claras", "sudoeste", 
    "octogonal", "varjão", "park way", "scia", "estrutural", "jardim botânico", 
    "itapoã", "sia", "vicente pires", "fercal", "sol nascente", "arniqueira", 
    "asa sul", "asa norte", "setor", "sqs", "sqn", "shis", "shin", "distrito federal", 
    "brasília", "brasilia", "df", "norte", "sul", "leste", "oeste"
}

ORGAOS_IGNORADOS = {
    "gdf", "cldf", "tcdf", "pcdf", "pmdf", "cbmdf", "detran", "detran-df", "der",
    "caesb", "neoenergia", "ceb", "novacap", "terracap", "codhab", "brb", "procon",
    "ses", "ses-df", "see", "see-df", "sef", "sefaz", "ssp", "ssp-df", "sedest",
    "agefis", "df legal", "slu", "adasa", "emater", "zoo", "metro", "metrô",
    "cgdf", "controladoria geral", "ouvidoria", "participa df", "participa-df",
    "tjdft", "mpdft", "stf", "stj", "tst", "tse", "mpu", "agu", "cgu", "tcu",
    "inss", "receita federal", "polícia federal", "policia federal",
    "secretaria", "ministério", "ministerio", "diretoria", "gerência", "gerencia",
    "coordenação", "presidência", "agência", "instituto", "fundação", "departamento",
    "defensoria pública", "ministério público", "conselho tutelar"
}

CONTEXTO_LEGAL = {
    "lei", "decreto", "portaria", "processo", "sei",
    "art", "artigo", "nº", "numero", "número"
}


# =====================================================
# NORMALIZAÇÃO (anti ruído)
# =====================================================
def normalizar(texto: str) -> str:
    return texto.lower().strip()


# =====================================================
# VALIDAÇÃO ANTI FALSO POSITIVO (AUDITÁVEL)
# =====================================================
def eh_falso_positivo(span, tipo: str) -> bool:
    texto = span.text.lower()
    numeros = re.findall(r"\d+", texto)
    numero_str = "".join(numeros)

    # Contexto jurídico-administrativo
    if span.start > 0:
        palavra_anterior = span.doc[span.start - 1].text.lower()
        if palavra_anterior in CONTEXTO_LEGAL:
            return True

    # Ano isolado
    if len(numero_str) == 4:
        ano = int(numero_str)
        if 1900 <= ano <= 2035:
            return True

    # Validação por tipo
    if tipo == "CPF_CNPJ" and len(numero_str) not in (11, 14):
        return True

    if tipo == "TELEFONE" and len(numero_str) not in (10, 11):
        return True

    return False


# =====================================================
# COMPONENTE REGEX → spaCy (Determinístico)
# =====================================================
@Language.component("regex_detector")
def regex_detector(doc):
    spans = []

    for label, pattern in REGEX_PATTERNS.items():
        for match in re.finditer(pattern, doc.text, flags=re.IGNORECASE):
            span = doc.char_span(match.start(), match.end(), label=label)
            if span and not eh_falso_positivo(span, label):
                spans.append(span)

    doc.ents = filter_spans(list(doc.ents) + spans)
    return doc


# =====================================================
# SINGLETONS
# =====================================================
_nlp = None
_matcher = None


# =====================================================
# PIPELINE spaCy
# =====================================================
def carregar_spacy():
    global _nlp, _matcher

    if _nlp:
        return _nlp

    nlp = spacy.load("pt_core_news_lg")

    if "regex_detector" not in nlp.pipe_names:
        nlp.add_pipe("regex_detector", before="ner")

    ruler = nlp.add_pipe("entity_ruler", before="ner")
    ruler.add_patterns([
        {"label": "SENSIVEL_SAUDE", "pattern": [{"LOWER": {"IN": [
            "câncer", "hiv", "aids", "autismo", "depressão", "tumor"
        ]}}]},
        {"label": "SENSIVEL_RELIGIAO", "pattern": [{"LOWER": {"IN": [
            "católico", "evangélico", "umbanda", "candomblé"
        ]}}]},
        {"label": "SENSIVEL_RACA", "pattern": [{"LOWER": {"IN": [
            "negro", "pardo", "indígena", "quilombola"
        ]}}]},
    ])

    matcher = Matcher(nlp.vocab)
    matcher.add("CONTEXTO_SENSIVEL", [[
        {"LOWER": {"IN": ["sou", "tenho", "fui", "estou", "portador"]}},
        {"OP": "*"},
        {"ENT_TYPE": "SENSIVEL_SAUDE"}
    ]])

    _nlp = nlp
    _matcher = matcher
    return _nlp


def obter_matcher():
    return _matcher
