import spacy
import re
from spacy.language import Language
from spacy.matcher import Matcher
from spacy.util import filter_spans

from validacoes import validar_cpf, validar_data_nascimento


# =====================================================
# REGEX COMPLEMENTAR (Dados pessoais explícitos)
# =====================================================
REGEX_PATTERNS = {

    # ==================== IDENTIFICAÇÃO PESSOAL ====================

    # CPF (validado posteriormente com dígito verificador)
    "CPF": r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b',
    "CPF_CONTEXTUAL": r'(?i)\bcpf[\s\.:nº]*\d{3}\.\d{3}\.\d{3}-\d{2}\b',

    # CNPJ
    "CNPJ": r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b',

    # ==================== DOCUMENTOS PESSOAIS ====================

    "DOC_RG": r'(?i)\b(?:rg|registro\s+geral|identidade)[\s\.:nº-]*\d[\d\.-]{5,12}\b',
    "DOC_CNH": r'(?i)\b(?:cnh|carteira\s+nacional|habilitação)[\s\.:nºo-]*\d{9,11}\b',
    "DOC_PASSAPORTE": r'(?i)\b(?:passaporte)[\s\.:nº]*[A-Z]{2}\d{6,7}\b',
    "DOC_TITULO_ELEITOR": r'(?i)\b(?:título\s+de\s+eleitor|titulo\s+eleitor)[\s\.:nºo-]*\d{10,12}\b',
    "DOC_PIS": r'(?i)\b(?:pis|pasep|nis)[\s\.:nº]*\d{3}\.\d{5}\.\d{2}-\d\b',
    "DOC_CTPS": r'(?i)\b(?:ctps|carteira\s+de\s+trabalho)[\s\.:nº]*\d+[\d\.-/]*\b',
    "DOC_CERTIDAO": r'(?i)\b(?:certidão|certidao)[\s\w\.:nºo-]{0,30}?(?:nascimento|casamento|óbito|obito|negativa|antecedentes)[\s\.:nº]*\d{6,32}\b',

    # Boletins e ocorrências
    "DOC_OCORRENCIA_MILITAR": r'(?i)\b(?:ocorrência|ocorrencia|bo|boletim|atendimento|chamado|cbmdf|pmdf|pc-?df|policial)[\s\w\.:nºo-]{0,50}?\b\d{15,20}\b',
    "DOC_BO": r'(?i)\b(?:bo|boletim\s+de\s+ocorrência|boletim\s+de\s+ocorrencia)[\s\.:nº]*\d{6,12}\b',

    # NIRE
    "DOC_NIRE": r'(?i)\b(?:nire|registro\s+de\s+empresa)[\s\.:nº]*\d{11}\b',

    # ==================== DATA PESSOAL ====================

    # Data de nascimento (validada posteriormente)
    "DATA_NASCIMENTO": r'(?i)(?:nascimento|nascido|nascida|data\s+de\s+nascimento|dn|d\.n\.)[\s\.:]*\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}',

    # ==================== CONTATO ====================

    "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "EMAIL_PARCIAL": r'(?i)(?:email|e-mail|correio)[\s\.:]*[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+',

    # Telefones
    "TELEFONE_COMPLETO": r'(?:\+55\s?)?\(?\d{2}\)?[\s.-](?:9\d{4}|\d{4})[\s.-]\d{4}\b',
    "TELEFONE_CONTEXTUAL": r'(?i)(?:tel|telefone|fone|celular|whats|whatsapp|contato|falar)[\s\.:nº]+\d{4,5}[\s.-]\d{4}\b',

    # ==================== SAÚDE (Sensível) ====================

    "SENSIVEL_CID": r'(?i)\bCID(?:\s*[-]?\s*(?:10|11))?[\s\.:]*[A-Z]\d{2}(?:\.\d)?\b',

    # ==================== PROCESSOS ====================

    "PROCESSO_SEI": r'\b\d{4,6}-\d{6,10}/(?:20[1-3]\d)-(?:0[1-9]|[1-9]\d)\b',
    "PROCESSO_CONTEXTUAL": r'(?i)(?:processo|sei|protocolo)[\s\.:nº]*\d{4,6}-\d{6,10}/\d{4}-\d{2}',

    # ==================== VEÍCULOS ====================

    "VEICULO_PLACA": r'\b[A-Z]{3}[-\s]?\d[A-Z0-9]\d{2}\b',
    "VEICULO_RENAVAM": r'(?i)renavam[\s\.:]*\d+',
    "VEICULO_CHASSI": r'(?i)\b(?:chassi|chassis)[\s\.:nº]*[A-HJ-NPR-Z0-9]{17}\b',

    # ==================== FINANCEIRO ====================

    "CONTA_BANCARIA": r'(?i)\bconta[\s\.:]*\d{4,12}-\d\b',
    "AGENCIA_BANCARIA": r'(?i)\b(?:agência|agencia|ag)[\s\.:nº]*\d{4}\b',
    "PIX_CPF": r'(?i)\bpix[\s\.:]*\d{3}\.\d{3}\.\d{3}-\d{2}\b',
}

# ==============================================================================
# LISTAS DE EXCEÇÃO (O QUE IGNORAR)
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
    "inss", "receita federal", "polícia federal", "policia federal","seec",
    "secretaria", "ministério", "ministerio", "diretoria", "gerência", "gerencia",
    "coordenação", "presidência", "agência", "instituto", "fundação", "departamento",
    "defensoria pública", "ministério público", "conselho tutelar"
}

# ==============================================================================
# LISTAS DE ALVOS (O QUE PROCURAR)
# ==============================================================================

# [As listas DOENCAS, RACA_ETNIA, RELIGIOES, ORIENTACAO_SEXUAL permanecem iguais]
# Mantendo do config_dados_FINAL.py

LISTA_CONSELHOS = [
    "OAB", "CRA", "CAU", "CRBIO", "CRBM", "CRC", "CRE", "CRECI", "COREN", 
    "CONRE", "CREF", "CREFITO", "CRM", "CRMV", "CRN", "CRO", "CRF", "CRP", 
    "CRESS", "CONFE", "CONFEA", "CREA", "CRQ", "CRT", "CORE", "CONRERP", 
    "CRP", "CRTR", "CRFA", "CRMV", "Cofeci", "Cofen", "Cofito", "Confea", 
    "Conferp", "Confere", "Conselho Federal de Medicina", 
    "Ordem dos Advogados do Brasil"
]

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

    # Ano isolado
    if len(numero_str) == 4:
        ano = int(numero_str)
        if 1900 <= ano <= 2035:
            return True

    return False


# =====================================================
# COMPONENTE REGEX → spaCy (Determinístico + Validado)
# =====================================================
@Language.component("regex_detector")
def regex_detector(doc):
    spans = []

    for label, pattern in REGEX_PATTERNS.items():
        for match in re.finditer(pattern, doc.text, flags=re.IGNORECASE):
            span = doc.char_span(match.start(), match.end(), label=label)
            if not span:
                continue

            # Anti falso positivo geral
            if eh_falso_positivo(span, label):
                continue

            # Validação forte por tipo
            if label in {"CPF", "CPF_CONTEXTUAL", "PIX_CPF"}:
                if not validar_cpf(span.text):
                    continue

            if label == "DATA_NASCIMENTO":
                if not validar_data_nascimento(span.text):
                    continue

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
