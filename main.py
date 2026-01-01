from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.ai_service import GeminiService
from schemas import DiagnosticoResponse
import uvicorn

app = FastAPI(
    title="Construtec API",
    description="API para análisis de problemas de mantenimiento del hogar con IA",
    version="1.0.0"
)

# Configurar CORS (permitir todo para desarrollo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from services.db_service import DBService

# Instanciar servicios
try:
    ai_service = GeminiService()
except ValueError as e:
    print(f"ADVERTENCIA: {e}. Asegurate de configurar el .env correctamente.")
    ai_service = None

try:
    db_service = DBService()
    print("INFO: Conexión con Firebase establecida.")
except Exception as e:
    print(f"ADVERTENCIA: Error conectando con Firebase: {e}")
    db_service = None

@app.get("/")
def read_root():
    return {"message": "Construtec API online. Usá /docs para ver la documentación."}

@app.get("/diagnosticos")
def get_diagnosticos():
    if not db_service:
        raise HTTPException(status_code=503, detail="Servicio de base de datos no disponible")
    return db_service.obtener_historial()

from pydantic import BaseModel

from typing import Optional

class JobUpdate(BaseModel):
    estado: str
    garantia: Optional[str] = None

@app.put("/diagnosticos/{doc_id}/estado")
def update_estado(doc_id: str, update: JobUpdate):
    if not db_service:
        raise HTTPException(status_code=503, detail="Servicio de base de datos no disponible")
    
    # Filtrar valores nulos para no borrarlos en Firestore
    data_to_update = {k: v for k, v in update.dict().items() if v is not None}
    
    success = db_service.actualizar_documento(doc_id, data_to_update)
    if not success:
        raise HTTPException(status_code=404, detail="Documento no encontrado o error al actualizar")
    
    return {"message": "Documento actualizado correctamente", "datos": data_to_update}

@app.post("/analizar-problema", response_model=DiagnosticoResponse)
async def analyze_problem(file: UploadFile = File(...)):
    """
    Recibe una imagen (foto del problema), la analiza con Gemini 1.5 Flash 
    y devuelve un diagnóstico estructurado con presupuesto estimado.
    """
    if not ai_service:
         raise HTTPException(status_code=500, detail="Servicio de IA no configurado (falta API KEY).")

    print(f"DEBUG: Recibido Content-Type: {file.content_type}")
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail=f"El archivo debe ser una imagen. Recibido: {file.content_type}")

    try:
        contents = await file.read()
        result = await ai_service.analyze_image(contents, mime_type=file.content_type)
        
        # Guardar en Firestore si el servicio está disponible
        if db_service:
            doc_id = db_service.guardar_diagnostico(result)
            if doc_id:
                result["firestore_id"] = doc_id

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno al analizar la imagen: {str(e)}")

# Para correrlo localmente: uvicorn main:app --reload
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
