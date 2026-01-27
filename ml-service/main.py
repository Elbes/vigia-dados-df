from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from detector import analisar_texto

app = FastAPI(title="VigiaDados DF – ML Service")

class TextoEntrada(BaseModel):
    texto: str

@app.post("/analisar")
def analisar(dados: TextoEntrada):
    try:
        resultado = analisar_texto(dados.texto)
        return resultado
    except Exception as e:
        print("ERRO NO PROCESSAMENTO:", e)
        raise HTTPException(status_code=500, detail="Erro interno ao analisar texto")

@app.get("/health")
def health():
    return {"status": "ok"}
