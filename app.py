"""
Application IA-BrainStormer GPS (Version V3 - Indestructible)
Système complet : Crash Test DUR + Génération + Priorisation + Séquençage
Mode BYOK (Bring Your Own Key) - Parsing JSON Renforcé
"""
import streamlit as st
import json
import re
from openai import OpenAI

# ==========================================
# 0. OUTILS DE NETTOYAGE (LE SECRET)
# ==========================================

def clean_json_response(raw_content):
    """
    Nettoie la réponse de l'IA pour extraire le JSON pur,
    même si l'IA ajoute du texte autour ou des balises markdown.
    """
    try:
        # 1. Essai direct
        return json.loads(raw_content)
    except:
        pass

    try:
        # 2. Chercher le contenu entre accolades {}
        match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        if match:
            json_str = match.group()
            return json.loads(json_str)
    except:
        pass
        
    try:
        # 3. Enlever les balises markdown ```json ... ```
        clean_str = re.sub(r'```json\s*|\s*```', '', raw_content)
        return json.loads(clean_str)
    except:
        return None

# ==========================================
# 1. LES PROMPTS SYSTÈME
# ==========================================

SYSTEM_PROMPT_CRASH_TEST = """Tu es un Auditeur Stratégique ("Devil's Advocate").
Analyse l'idée selon D.U.R. (Douloureux, Urgent, Reconnu).

FORMAT JSON STRICT :
{
  "score_D": 0, "score_U": 0, "score_R": 0, "total": 0,
  "verdict": "VERT ou ROUGE",
  "analyse_critique": "Phrase courte",
  "conseil_architecte": "Action concrète"
}"""

SYSTEM_PROMPT_PHASE_G = """Génère 10 angles stratégiques uniques.
FORMAT JSON STRICT :
{ 
  "angles": [ 
     {"id": 1, "titre": "Titre court", "cible_precise": "...", "opportunite": "..."} 
  ] 
}"""

SYSTEM_PROMPT_PHASE_P = """Tu es Expert Stratège. Utilise la Matrice de Conviction.
Pondération : Douleur (Coef 4), Unicité (Coef 3), Alignement (Coef 3).

FORMAT JSON STRICT OBLIGATOIRE :
{
  "evaluations": [
    {
      "id": 1,
      "titre": "Rappel titre",
      "score_douleur": 0,
      "score_unicite": 0,
      "score_alignement": 0,
      "score_total_pondere": 0
    }
  ],
  "recommandation": {
    "id_gagnant": 1,
    "raison": "Explication courte"
  }
}"""

SYSTEM_PROMPT_PHASE_S = """Backcasting de J+7 à J+1.
FORMAT JSON STRICT :
{ 
  "resultat_j7": "...", 
  "etapes_journalieres": [ 
     {"jour": "J+7", "action_principale": "...", "detail_execution": "..."} 
  ] 
}"""

# ==========================================
# 2. MÉCANIQUE API
# ==========================================

class GPSSystem:
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def call_gpt(self, system_prompt: str, user_message: str) -> dict:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            raw_content = response.choices[0].message.content
            
            # Utilisation du nettoyeur
            json_data = clean_json_response(raw_content)
            
            if json_data:
                return json_data
            else:
                return {"error": True, "raw": raw_content, "message": "JSON illisible"}
                
        except Exception as e:
            return {"error": True, "message": str(e)}

    # Méthodes spécifiques
    def crash_test_dur(self, idee):
        return self.call_gpt(SYSTEM_PROMPT_CRASH_TEST, f"Idée: {idee}")
    
    def phase_g_generation(self, idee):
        return self.call_gpt(SYSTEM_PROMPT_PHASE_G, f"Idée validée: {idee}")

    def phase_p_priorisation(self, angles):
        txt = "\n".join([f"ID {a['id']}: {a['titre']} ({a['cible_precise']})" for a in angles])
        return self.call_gpt(SYSTEM_PROMPT_PHASE_P, f"Classe ces options:\n{txt}")

    def phase_s_sequencage(self, angle):
        return self.call_gpt(SYSTEM_PROMPT_PHASE_S, f"Plan pour: {angle.get('titre')}")

# ==========================================
# 3. INTERFACE (UI)
# ==========================================

def reset_app():
    keys = ['step', 'openai_api_key_input']
    st.session_state.step = 'crash_test'
    for k in list(st.session_state.keys()):
        if k not in keys: del st.session_state[k]

st.set_page_config(page_title="IA-BrainStormer GPS", page_icon="🧭", layout="wide")

st.markdown("""
<style>
    .main-title {font-size: 3rem; text-align: center; color: #667eea;}
    .verdict-vert {background-color: #d4edda; padding: 1rem; border-radius: 5px; border-left: 5px solid #28a745;}
    .verdict-rouge {background-color: #f8d7da; padding: 1rem; border-radius: 5px; border-left: 5px solid #dc3545;}
    .stButton>button {width: 100%;}
</style>
""", unsafe_allow_html=True)

if 'step' not in st.session_state: st.session_state.step = 'crash_test'

# SIDEBAR
with st.sidebar:
    st.title("⚙️ Config")
    api_key = st.text_input("Clé API OpenAI", type="password", key="openai_api_key_input")
    model_choice = st.selectbox("Modèle", ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"])
    st.progress({'crash_test':0, 'generation':33, 'priorisation':66, 'sequencage':100}[st.session_state.step])
    st.button("🔄 Reset", on_click=reset_app)

if not api_key:
    st.warning("⬅️ Entrez votre clé API à gauche.")
    st.stop()

gps = GPSSystem(api_key, model_choice)

st.markdown("<h1 class='main-title'>🧭 IA-BrainStormer GPS</h1>", unsafe_allow_html=True)

# --- PHASE 0 ---
if st.session_state.step == 'crash_test':
    st.subheader("Phase 0 : Crash Test")
    idee = st.text_area("Votre idée :", height=100)
    if st.button("🚀 Crash Test"):
        with st.spinner("Analyse..."):
            st.session_state.crash_test_result = gps.crash_test_dur(idee)
            st.session_state.idee_initiale = idee
            st.rerun()

    if 'crash_test_result' in st.session_state:
        res = st.session_state.crash_test_result
        if res.get('error'):
            st.error("Erreur IA. Réessayez.")
            st.write(res)
        else:
            c1,c2,c3 = st.columns(3)
            c1.metric("Douleur", f"{res.get('score_D',0)}/10")
            c2.metric("Urgence", f"{res.get('score_U',0)}/10")
            c3.metric("Reconnu", f"{res.get('score_R',0)}/10")
            
            if res.get('verdict') == 'VERT': st.markdown(f"<div class='verdict-vert'>✅ {res.get('analyse_critique')}</div>", unsafe_allow_html=True)
            else: st.markdown(f"<div class='verdict-rouge'>🛑 {res.get('analyse_critique')}</div>", unsafe_allow_html=True)
            
            validee = st.text_area("Reformulation :", value=st.session_state.get('idee_initiale'))
            if st.button("Valider -> Phase G"):
                st.session_state.idee_validee = validee
                st.session_state.step = 'generation'
                st.rerun()

# --- PHASE G ---
elif st.session_state.step == 'generation':
    st.subheader("Phase G : Génération")
    if 'phase_g_result' not in st.session_state:
        with st.spinner("Génération..."):
            st.session_state.phase_g_result = gps.phase_g_generation(st.session_state.idee_validee)
            st.rerun()
    else:
        res = st.session_state.phase_g_result
        if res.get('error'):
            st.error("Erreur format.")
            if st.button("Réessayer"): del st.session_state.phase_g_result; st.rerun()
        else:
            sel = []
            for a in res.get('angles', []):
                with st.expander(f"📐 {a.get('titre')}"):
                    st.write(a.get('opportunite'))
                    if st.checkbox("Sélectionner", key=f"c_{a['id']}"): sel.append(a)
            
            if len(sel) == 3:
                if st.button("Valider -> Phase P"):
                    st.session_state.angles_selectionnes = sel
                    st.session_state.step = 'priorisation'
                    st.rerun()
            else: st.warning(f"Sélectionnez 3 angles ({len(sel)}/3)")

# --- PHASE P (Celle qui posait problème) ---
elif st.session_state.step == 'priorisation':
    st.subheader("Phase P : Priorisation")
    if 'phase_p_result' not in st.session_state:
        with st.spinner("Priorisation..."):
            st.session_state.phase_p_result = gps.phase_p_priorisation(st.session_state.angles_selectionnes)
            st.rerun()
    else:
        res = st.session_state.phase_p_result
        
        # --- BLINDAGE DE L'AFFICHAGE ---
        if res.get('error') or 'evaluations' not in res:
            st.error("L'IA a renvoyé un format inattendu.")
            st.code(res.get('raw', str(res))) # Affiche le brut pour debug si besoin
            if st.button("Relancer le calcul"): 
                del st.session_state.phase_p_result
                st.rerun()
        else:
            # Construction du tableau manuelle pour éviter les cases vides
            data_clean = []
            for e in res['evaluations']:
                # Calcul de secours si l'IA a oublié le total
                s_pain = e.get('score_douleur', 0)
                s_uniq = e.get('score_unicite', 0)
                s_align = e.get('score_alignement', 0)
                total = e.get('score_total_pondere', (s_pain*4 + s_uniq*3 + s_align*3))
                
                data_clean.append({
                    "Angle": e.get('titre', 'Angle inconnu'),
                    "Douleur (x4)": s_pain,
                    "Unicité (x3)": s_uniq,
                    "Passion (x3)": s_align,
                    "SCORE TOTAL": total
                })
            
            st.table(data_clean)
            
            # Affichage de la recommandation
            reco = res.get('recommandation', {})
            if reco:
                st.success(f"🏆 Recommandation : Angle #{reco.get('id_gagnant', '?')}")
                st.info(f"Pourquoi : {reco.get('raison', 'Aucune justification fournie')}")
            else:
                st.warning("Pas de recommandation explicite de l'IA.")

            # Sélecteur
            opts = {e.get('id'): e.get('titre') for e in res['evaluations']}
            choix = st.selectbox("Votre choix final :", list(opts.keys()), format_func=lambda x: opts.get(x))
            
            if st.button("Générer le Plan -> Phase S"):
                st.session_state.angle_choisi = next((a for a in st.session_state.angles_selectionnes if a["id"] == choix), None)
                st.session_state.step = 'sequencage'
                st.rerun()

# --- PHASE S ---
elif st.session_state.step == 'sequencage':
    st.subheader("Phase S : Plan")
    if 'phase_s_result' not in st.session_state:
        with st.spinner("Backcasting..."):
            st.session_state.phase_s_result = gps.phase_s_sequencage(st.session_state.angle_choisi)
            st.rerun()
    else:
        plan = st.session_state.phase_s_result
        if plan.get('error'):
            st.error("Erreur plan.")
        else:
            st.info(f"Objectif : {plan.get('resultat_j7')}")
            for j in plan.get('etapes_journalieres', []):
                st.write(f"**{j.get('jour')}** : {j.get('action_principale')}")
            
            st.download_button("JSON", json.dumps(plan), "plan.json")
            st.button("Nouveau Projet", on_click=reset_app)
