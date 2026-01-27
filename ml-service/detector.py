from spacy_pipeline import (
    carregar_spacy,
    obter_matcher,
    normalizar,
    LOCAIS_IGNORADOS,
    ORGAOS_IGNORADOS
)

MAPA_SENSIVEL = {
    "SENSIVEL_SAUDE": "saude",
    "SENSIVEL_RELIGIAO": "religiao",
    "SENSIVEL_RACA": "raca",
}

def analisar_texto(texto: str) -> dict:
    nlp = carregar_spacy()
    matcher = obter_matcher()

    tipos_detectados = set()
    categorias_sensiveis = set()
    origens = set()
    confianca = 0.0
    evidencias = []

    doc = nlp(texto)

    for ent in doc.ents:
        texto_ent = normalizar(ent.text)

        # 🔹 Nome de pessoa (com exceções)
        if ent.label_ == "PER":
            if texto_ent not in LOCAIS_IGNORADOS and texto_ent not in ORGAOS_IGNORADOS:
                tipos_detectados.add("nome_pessoa")
                origens.add("spacy")
                confianca = max(confianca, 0.75)
                evidencias.append(f"Nome detectado: {ent.text}")

        # 🔹 Dados pessoais fortes
        if ent.label_ in ["CPF_CNPJ", "EMAIL", "TELEFONE"]:
            tipos_detectados.add(ent.label_.lower())
            origens.add("regex")
            confianca = max(confianca, 0.95)
            evidencias.append(f"Dado pessoal: {ent.label_}")

        # 🔹 Dados sensíveis explícitos
        if ent.label_ in MAPA_SENSIVEL:
            categorias_sensiveis.add(MAPA_SENSIVEL[ent.label_])
            origens.add("spacy+heuristica")
            confianca = max(confianca, 0.85)
            evidencias.append(f"Dado sensível: {ent.text}")

    # 🔹 Contexto sensível implícito
    if matcher(doc):
        categorias_sensiveis.add("saude")
        origens.add("spacy+contexto")
        confianca = max(confianca, 0.9)
        evidencias.append("Contexto sensível detectado")

    return {
        "contem_dados_pessoais": bool(tipos_detectados),
        "contem_dados_sensiveis": bool(categorias_sensiveis),
        "origem_decisao": sorted(origens),
        "tipos_detectados": sorted(tipos_detectados),
        "categorias_sensiveis": sorted(categorias_sensiveis),
        "confianca": round(confianca, 2),
        "evidencias": evidencias
    }
