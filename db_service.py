import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os

class DBService:
    def __init__(self):
        # Evitar inicializar múltiples veces si se usa reload
        if not firebase_admin._apps:
            cred_path = "serviceAccountKey.json"
            if not os.path.exists(cred_path):
                raise FileNotFoundError(f"No se encontró {cred_path}")
            
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()

    def guardar_diagnostico(self, data: dict) -> str:
        """
        Guarda el diagnóstico en la colección 'diagnosticos' y retorna el ID.
        Agrega timestamp del servidor y estado inicial.
        """
        try:
            # Agregar timestamp y estado por defecto
            data_to_save = data.copy()
            data_to_save["timestamp"] = firestore.SERVER_TIMESTAMP
            data_to_save["estado"] = "pendiente" 
            
            # Guardar en Firestore
            update_time, doc_ref = self.db.collection("diagnosticos").add(data_to_save)
            
            print(f"Diagnóstico guardado en Firestore con ID: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            print(f"Error al guardar en Firestore: {e}")
            return None

    def actualizar_documento(self, doc_id: str, data: dict) -> bool:
        """
        Actualiza campos arbitrarios de un documento.
        """
        try:
            doc_ref = self.db.collection("diagnosticos").document(doc_id)
            doc_ref.update(data)
            return True
        except Exception as e:
            print(f"Error al actualizar documento: {e}")
            return False

    def obtener_historial(self) -> list:
        """
        Obtiene los últimos diagnósticos ordenados por fecha descendente.
        """
        try:
            docs = self.db.collection("diagnosticos").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(20).stream()
            historial = []
            for doc in docs:
                data = doc.to_dict()
                data["firestore_id"] = doc.id
                # Convertir timestamp a string para JSON serialization
                if "timestamp" in data and data["timestamp"]:
                   data["timestamp"] = data["timestamp"].isoformat()
                historial.append(data)
            return historial
        except Exception as e:
            print(f"Error al obtener historial: {e}")
            return []
