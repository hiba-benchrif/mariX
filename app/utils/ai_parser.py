import google.generativeai as genai
import os
import json

def extract_data_from_document(filepath, dossier_type):
    """
    Analyse un document avec Gemini 1.5 Flash et retourne un dictionnaire JSON.
    dossier_type: 'import' ou 'export'
    """
    api_key = os.environ.get('GEMINI_API_KEY')
    
    if not api_key or api_key == 'votre_cle_api_gemini':
        # Fallback de simulation si la clé n'est pas configurée
        return {
            "numero_dossier": f"SIM-{dossier_type.upper()}-001", 
            "client": "Client Simulé par IA",
            "compagnie": "Compagnie Maritime Test"
        }

    try:
        genai.configure(api_key=api_key)
        # Utilisation du dernier modèle disponible
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # Uploader le fichier temporaire vers l'API Gemini
        uploaded_file = genai.upload_file(path=filepath)
        
        # Définir le prompt en fonction du type
        if dossier_type == 'import':
            fields = "numero_dossier, commercial, exploitant, type_conteneur, fournisseur, client, mbl, incoterm, agent, compagnie, pol, pod, etd, eta, achat, vente, pays"
        else:
            fields = "numero_dossier, numero_booking, commercial, client, compagnie, date_booking, date_chargement, date_sequence, etd, pod, eta, nombre_conteneurs, facturation (mettre true ou false), situation"
            
        prompt = f"""
        Tu es un assistant logistique expert en documents maritimes (BL, Booking, etc). 
        Analyse ce document et extrais les informations pour un dossier {dossier_type.upper()}.
        
        Liste stricte des clés attendues : {fields}.
        
        Contraintes :
        1. Retourne UNIQUEMENT un objet JSON valide (pas de markdown, pas de texte explicatif, pas de blocs ```json).
        2. Si une information est introuvable, mets une chaîne vide "".
        3. Pour les dates, utilise obligatoirement le format YYYY-MM-DD.
        4. Pour achat et vente (si import), retourne un nombre ou une chaîne vide.
        """
        
        response = model.generate_content([prompt, uploaded_file])
        
        # Nettoyage de la réponse au cas où Gemini ajoute des marqueurs markdown
        text_response = response.text.strip()
        if text_response.startswith('```json'):
            text_response = text_response[7:]
        if text_response.startswith('```'):
            text_response = text_response[3:]
        if text_response.endswith('```'):
            text_response = text_response[:-3]
            
        data = json.loads(text_response.strip())
        return data
        
    except Exception as e:
        print(f"Erreur d'extraction IA : {e}")
        return {}
