import pandas as pd
import spacy
from spacy.language import Language
from spacy.util import filter_spans
from spacy.tokens import Span
from spacy.matcher import Matcher
import re

# ==============================================================================
# 1. DEFINIÇÃO DE PADRÕES REGEX (O "Faxineiro" + Serviços Públicos)
# ==============================================================================
REGEX_PATTERNS = {
    # --- IDENTIFICADORES PESSOAIS FORTE ---
    "CPF_CNPJ": r'\b\d{3,}\.\d{3,}[\d\.-]*\b',
    "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "TELEFONE": r'\(?\d{2}\)?\s?(?:9\d{4}|\d{4})[-.\s]?\d{4}',
    "PROCESSO_SEI": r'\b\d{4,6}-\d{6,10}/\d{4}-\d{2}\b',
    
    # --- VEÍCULOS ---
    "VEICULO_PLACA": r'\b[A-Z]{3}[-\s]?\d[A-Z0-9]\d{2}\b',
    "VEICULO_RENAVAM": r'(?i)renavam[\s\.:]*\d+',
    
    # --- SERVIÇOS PÚBLICOS (DF) ---
    # Captura genérica de "Inscrição/Matrícula" com filtro posterior
    "DADO_INSCRICAO_GERAL": r'(?i)(?:inscrição|matricula|matrícula)[\s\.:nºo-]*\d+(?:[\.-]\d+)*',
    
    # Específicos que não usam a palavra "Inscrição"
    "DADO_ENERGIA": r'(?i)(?:unidade\s+consumidora|instalação|código\s+cliente)[\s\.:nºo-]*\d+',
    "DADO_IPTU_TLP": r'(?i)(?:iptu|tlp)[\s\.:nºo-]*\d+',
    "DADO_HIDROMETRO": r'(?i)hidr[ôo]metro[\s\.:nºo-]*\w+',
    
    # --- DADOS BANCÁRIOS ---
    "DADO_BANCARIO": r'(?i)(?:agência|conta\s+corrente|pix)[\s\.:nºo-]*[\d-]+'
}

# ==============================================================================
# 2. FUNÇÃO DE FILTRO (Evita Falsos Positivos)
# ==============================================================================
def eh_falso_positivo(span):
    """Retorna True se o span for um ano, lei, ou número irrelevante."""
    texto = span.text.lower()
    
    # Extrair números para análise
    numeros = re.findall(r'\d+', texto)
    if not numeros: return True
    numero_str = "".join(numeros)
    
    # REGRA A: É um ano? (Ex: "Matrícula em 2024")
    if len(numero_str) == 4:
        valor = int(numero_str)
        if 1900 <= valor <= 2035: return True

    # REGRA B: É curto demais? (Ex: "Inscrição 1")
    if len(numero_str) < 3: return True

    # REGRA C: Contexto Legislativo (Olha a palavra anterior)
    if span.start > 0:
        palavra_anterior = span.doc[span.start - 1].text.lower()
        if palavra_anterior in ["lei", "decreto", "portaria", "artigo", "art", "item", "número", "nº"]:
            # "Número Inscrição" é válido, mas "Lei Inscrição" não existe.
            # Vamos filtrar apenas termos legislativos fortes
            if palavra_anterior in ["lei", "decreto", "portaria"]:
                return True

    return False

# ==============================================================================
# 3. COMPONENTE SPACY CUSTOMIZADO (Ponte Regex -> AI)
# ==============================================================================
@Language.component("regex_detector")
def regex_detector(doc):
    matches = []
    for label, pattern in REGEX_PATTERNS.items():
        for match in re.finditer(pattern, doc.text, flags=re.IGNORECASE):
            start, end = match.span()
            span = doc.char_span(start, end, label=label)
            
            if span is not None:
                # Aplica filtro apenas na categoria perigosa
                if label == "DADO_INSCRICAO_GERAL":
                    if eh_falso_positivo(span):
                        continue 
                
                matches.append(span)
    
    # Adiciona à lista de entidades (mesclando com o que já existe)
    try:
        doc.ents = list(doc.ents) + matches
        doc.ents = filter_spans(doc.ents) # Remove sobreposições
    except Exception as e:
        pass # Ignora erros de span inválido raros
        
    return doc

# ==============================================================================
# 4. CONFIGURAÇÃO GERAL DO PIPELINE
# ==============================================================================
def carregar_modelo():
    print("Carregando modelo spaCy (pt_core_news_lg)...")
    try:
        nlp = spacy.load("pt_core_news_lg")
    except:
        print("Modelo não encontrado. Rode: python -m spacy download pt_core_news_lg")
        return None

    # A. Adiciona Componente Regex (Antes da NER padrão)
    if "regex_detector" not in nlp.pipe_names:
        nlp.add_pipe("regex_detector", before="ner")
    
    # B. Adiciona Entity Ruler (Para OAB, Matrículas e Sensíveis baseados em tokens)
    ruler = nlp.add_pipe("entity_ruler", before="ner")
    patterns = [
        # CONSELHOS (OAB/CREA/CRM)
        {"label": "DOC_PROFISSIONAL", "pattern": [
            {"LOWER": {"IN": ["oab", "crea", "crm", "crc", "coren", "cau"]}}, 
            {"IS_PUNCT": True, "OP": "*"}, 
            {"LOWER": {"REGEX": "^[a-z]{2}$"}, "OP": "?"}, # UF
            {"IS_PUNCT": True, "OP": "*"}, 
            {"TEXT": {"REGEX": "^\\d+$"}}
        ]},
        # SIAPE (Outra forma)
        {"label": "MATRICULA_SIAPE", "pattern": [{"LOWER": "siape"}, {"IS_PUNCT": True, "OP": "*"}, {"TEXT": {"REGEX": "^\\d+"}}]},
        
        # SENSÍVEIS (Saúde/Religião/Raça)
        {"label": "SENSIVEL_SAUDE", "pattern": [{"LOWER": {"IN": ["hiv", "aids", "câncer", "esquizofrenia", "autismo", "tumor", "depressão"]}}]},
        {"label": "SENSIVEL_SAUDE", "pattern": [{"LOWER": "cid"}, {"TEXT": {"REGEX": "^[A-Z]\\d+"}}]},
        {"label": "SENSIVEL_RELIGIAO", "pattern": [{"LOWER": {"IN": ["umbanda", "candomblé", "evangélico", "católico", "espírita", "judeu"]}}]},
        {"label": "SENSIVEL_RACA", "pattern": [{"LOWER": {"IN": ["negro", "pardo", "indígena", "quilombola"]}}]}
    ]
    ruler.add_patterns(patterns)
    
    # C. Matcher para Contexto (Declaração de doenças)
    matcher = Matcher(nlp.vocab)
    matcher.add("ALERTA_SENSIVEL_CONTEXTO", [[
        {"LOWER": {"IN": ["eu", "meu", "minha", "sou", "tenho", "portador"]}},
        {"OP": "*"}, # Até n palavras
        {"ENT_TYPE": "SENSIVEL_SAUDE"}
    ]])
    
    return nlp, matcher

# ==============================================================================
# 5. EXECUÇÃO NO ARQUIVO
# ==============================================================================
def processar_arquivo(caminho_entrada, caminho_saida):
    nlp, matcher = carregar_modelo()
    if not nlp: return
    
    print(f"Lendo arquivo: {caminho_entrada}")
    try:
        df = pd.read_csv(caminho_entrada)
    except:
        df = pd.read_excel(caminho_entrada) # Tenta outro separador
        
    print("Processando linhas... (Isso usa IA, pode levar alguns segundos)")

    # Função aplicada linha a linha
    def analisar(texto):
        if not isinstance(texto, str):
            return False, False, "Nenhum"
        
        doc = nlp(texto)
        
        # 1. Coletar Entidades
        categorias = []
        tem_sensivel = False
        
        for ent in doc.ents:
            # Filtra apenas o que interessa (Pessoas + Nossas Categorias)
            if ent.label_ in ["PER", "LOC", "ORG", "MISC"]: # Padrões do spaCy
                if ent.label_ == "PER": # Só queremos nomes de pessoas
                    categorias.append("NOME_PESSOA")
            else:
                # Nossas categorias customizadas (CPF, CAESB, SAUDE, etc)
                categorias.append(ent.label_)
                if "SENSIVEL" in ent.label_:
                    tem_sensivel = True
        
        # 2. Verificar Contexto (Matcher)
        if matcher(doc):
            categorias.append("CONTEXTO_SENSIVEL_DECLARADO")
            tem_sensivel = True
            
        categorias = list(set(categorias)) # Remove duplicatas
        tem_dado_pessoal = len(categorias) > 0
        lista_categorias = ", ".join(categorias) if categorias else "Nenhum"
        
        return tem_dado_pessoal, tem_sensivel, lista_categorias

    # Aplica e cria as colunas
    resultados = df['Texto Mascarado'].apply(analisar)
    
    # Desempacota os resultados em colunas do DataFrame
    df['TEM_DADO_PESSOAL'] = [res[0] for res in resultados]
    df['TEM_SENSIVEL'] = [res[1] for res in resultados]
    df['CATEGORIAS_ENCONTRADAS'] = [res[2] for res in resultados]

    # Salva
    df.to_excel(caminho_saida, index=False)
    print(f"Concluído! Arquivo salvo em: {caminho_saida}")
    
    # Exibe resumo
    print("\n--- RESUMO DOS DADOS ENCONTRADOS ---")
    print(df['CATEGORIAS_ENCONTRADAS'].value_counts().head(10))
    print(f"\nTotal com Dados Pessoais: {df['TEM_DADO_PESSOAL'].sum()}")
    print(f"Total com Dados Sensíveis: {df['TEM_SENSIVEL'].sum()}")

# RODA O PROCESSO (Ajuste o nome do arquivo aqui)
processar_arquivo("data\AMOSTRA_e-SIC.xlsx", "data\RESULTADO_FINAL_HACKATHON.xlsx")