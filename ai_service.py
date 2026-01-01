import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
from schemas import DiagnosticoResponse
import base64

load_dotenv()

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY no encontrada en variables de entorno.")
        
        self.client = genai.Client(api_key=api_key)
        
        self.system_prompt = """
        Actuás como un Perito Experto en Mantenimiento (Argentina).
        Analizá la imagen y devolvé un JSON con:
        {
          "diagnostico_corto": "string",
          "diagnostico_detallado": "string",
          "nivel_urgencia": "BAJA" | "MEDIA" | "ALTA",
          "color_urgencia": "hex code",
          "solucion_tecnica_pasos": ["paso 1", "paso 2"],
          "materiales_sugeridos": ["material 1", "material 2"],
          "precio_mano_obra_min_ars": integer,
          "precio_mano_obra_min_ars": integer,
          "precio_mano_obra_max_ars": integer,
          "consejo_anti_verso": "string",
          "mini_contrato_sugerido": "Redactá un párrafo formal breve que sirva de acuerdo. Ej: 'Se acuerda la reparación de [problema] mediante [solución] con los materiales listados. El objetivo es detener la filtración de forma definitiva.'",
          "oficio_requerido": "PLOMERO" | "GASISTA" | "ELECTRICISTA" | "ZINGUERO"
        }
        Reglas: Precios en ARS (Zona Norte GBA), idioma Rioplatense, sé crudo y realista.
        """

    async def analyze_image(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
        """
        Envía la imagen a Gemini y retorna el análisis estructurado.
        """
        try:
            # En el nuevo SDK podemos pasar los bytes directamente si usamos types.Part
            # O podemos usar el contenido directamente en la lista.
            # Para mayor seguridad, codificamos a Part.
            
            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            )
            
            # Configuración manual para evitar problemas con types.GenerateContentConfig en versiones mixtas
            config = {
                "system_instruction": self.system_prompt,
                "response_mime_type": "application/json",
                "response_schema": DiagnosticoResponse
            }
            
            response = self.client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=[image_part],
                config=config
            )
            
            # El nuevo SDK suele devolver un objeto parseado si se usó response_schema pydantic
            # pero depende de la versión. Si devuelve objeto, lo convertimos a dict.
            # Si devuelve texto JSON, lo parseamos.
            if response.parsed:
               return response.parsed.model_dump()
            else:
               return json.loads(response.text)
            
        except Exception as e:
            print(f"Error al analizar imagen con Gemini: {e}")
            raise e
