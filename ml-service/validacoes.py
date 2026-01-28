import re
from datetime import datetime

def validar_cpf(cpf_str: str) -> bool:
    numeros = re.sub(r'\D', '', cpf_str)

    if len(numeros) != 11:
        return False
    if numeros == numeros[0] * 11:
        return False

    soma = sum(int(numeros[i]) * (10 - i) for i in range(9))
    dig1 = (soma * 10 % 11) % 10

    soma = sum(int(numeros[i]) * (11 - i) for i in range(10))
    dig2 = (soma * 10 % 11) % 10

    return numeros[-2:] == f"{dig1}{dig2}"

def validar_data_nascimento(data_str: str) -> bool:
    match = re.search(r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})', data_str)
    if not match:
        return False

    dia, mes, ano = map(int, match.groups())
    if ano < 100:
        ano = 1900 + ano if ano > 24 else 2000 + ano

    if not (1904 <= ano <= 2019):
        return False

    try:
        datetime(ano, mes, dia)
        return True
    except ValueError:
        return False
