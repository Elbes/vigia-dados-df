"""
evaluate.py
Avaliação offline da heurística de detecção de dados pessoais.

NÃO é usado em produção.
Usado apenas para:
- validação técnica
- auditoria
- demonstração para banca
"""

from detector import analisar_texto

# =====================================================
# CONJUNTO DE TESTES CONTROLADO (SINTÉTICO)
# =====================================================
# (Texto, Esperado: True = contém dado pessoal)
AMOSTRAS = [
    ("Meu CPF é 123.456.789-09", True),
    ("Lei nº 1234/2023", False),
    ("Sou portador de HIV", True),
    ("Processo SEI 00001-000123/2024-11", False),
    ("João Silva solicitou informação", True),
    ("Secretaria de Saúde do DF", False),
    ("Telefone para contato: (61) 99999-9999", True),
    ("Requerimento conforme Decreto nº 45.000", False),
]

# =====================================================
# MATRIZ DE CONFUSÃO
# =====================================================
tp = fp = fn = tn = 0

for texto, esperado in AMOSTRAS:
    resultado = analisar_texto(texto)["contem_dados_pessoais"]

    if resultado and esperado:
        tp += 1
    elif resultado and not esperado:
        fp += 1
    elif not resultado and esperado:
        fn += 1
    else:
        tn += 1

# =====================================================
# MÉTRICAS
# =====================================================
precisao = tp / (tp + fp) if (tp + fp) else 0
recall = tp / (tp + fn) if (tp + fn) else 0
f1 = 2 * precisao * recall / (precisao + recall) if (precisao + recall) else 0

# =====================================================
# RESULTADO
# =====================================================
print("📊 Avaliação do VigiaDados DF")
print("-" * 40)
print(f"Verdadeiros Positivos (TP): {tp}")
print(f"Falsos Positivos (FP): {fp}")
print(f"Falsos Negativos (FN): {fn}")
print(f"Verdadeiros Negativos (TN): {tn}")
print("-" * 40)
print(f"Precisão: {precisao:.2f}")
print(f"Recall:   {recall:.2f}")
print(f"F1-score: {f1:.2f}")
