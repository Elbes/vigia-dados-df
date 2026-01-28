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

    tipos = set()
    sensiveis = set()
    origens = set()
    evidencias = []
    confianca = 0.0

    doc = nlp(texto)

    for ent in doc.ents:
        texto_ent = normalizar(ent.text)

        if ent.label_ == "PER":
            if texto_ent not in LOCAIS_IGNORADOS and texto_ent not in ORGAOS_IGNORADOS:
                tipos.add("nome_pessoa")
                origens.add("spacy")
                confianca = max(confianca, 0.75)
                evidencias.append(f"Nome detectado: {ent.text}")

        if ent.label_ in ["CPF", "CNPJ", "EMAIL", "TELEFONE"]:
            tipos.add(ent.label_.lower())
            origens.add("regex_validado")
            confianca = max(confianca, 0.95)
            evidencias.append(f"Dado pessoal validado: {ent.label_}")

        if ent.label_ in MAPA_SENSIVEL:
            sensiveis.add(MAPA_SENSIVEL[ent.label_])
            origens.add("spacy+heuristica")
            confianca = max(confianca, 0.85)
            evidencias.append(f"Dado sensível: {ent.text}")

    if matcher(doc):
        sensiveis.add("saude")
        origens.add("contexto")
        confianca = max(confianca, 0.9)
        evidencias.append("Contexto sensível declarado")

    return {
        "contem_dados_pessoais": bool(tipos),
        "contem_dados_sensiveis": bool(sensiveis),
        "origem_decisao": sorted(origens),
        "tipos_detectados": sorted(tipos),
        "categorias_sensiveis": sorted(sensiveis),
        "confianca": round(confianca, 2),
        "evidencias": evidencias
    }
