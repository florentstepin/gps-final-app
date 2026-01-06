"""
Application IA-BrainStormer GPS (Version V5 - Save & Load)
Système complet + Gestion de l'Historique + Sauvegarde/Chargement de Projet
"""
import streamlit as st
import json
import re
from openai import OpenAI
from datetime import datetime

# ==========================================
# 0. OUTILS DE NETTOYAGE
# ==========================================

def clean_json_response(raw_content):
    try: return json.loads(raw_content)
    except: pass
    try:
        match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        if match: return json.loads(match.group())
    except: pass
    try:
        clean_str = re.sub(r'```json\s*|\s*```', '', raw_content)
        return json.loads(clean_str)
    except: return None

# ==========================================
# 1. PROMPTS SYSTÈME
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
{ "angles": [ {"id": 1, "titre": "Titre court", "cible_precise": "...", "opportunite": "..."} ] }"""

SYSTEM_PROMPT_PHASE_P = """Tu es Expert Stratège. Utilise la Matrice de Conviction.
On te donne 3 options numérotées 1, 2 et 3.
FORMAT JSON STRICT :
{
  "evaluations": [
    { "id_option": 1, "score_douleur": 0, "score_unicite": 0, "score_alignement": 0, "score_total_pondere": 0 },
    { "id_option": 2, ... }, { "id_option": 3, ... }
  ],
  "recommandation": { "id_gagnant": 1, "raison": "Explication courte" }
}"""

SYSTEM_PROMPT_PHASE_S = """Backcasting de J+7 à J+1.
FORMAT JSON STRICT :
{ "resultat_j7": "...", "etapes_journalieres": [ {"jour": "J+7", "action_principale": "...", "detail_execution": "..."} ] }"""

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
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content
            json_data = clean_json_response(raw)
            return json_data if json_data else {"error": True, "raw": raw}
        except Exception as e:
            return {"error": True, "message": str(e)}

    def crash_test_dur(self, idee): return self.call_gpt(SYSTEM_PROMPT_CRASH_TEST, f"Idée: {idee}")
    def phase_g_generation(self, idee): return self.call_gpt(SYSTEM_PROMPT_PHASE_G, f"Idée validée: {idee}")
    def phase_p_priorisation(self, angles):
        txt = ""
        for index, a in enumerate(angles):
            txt += f"OPTION {index + 1} : {a['titre']} ({a['cible_precise']})\n"
        return self.call_gpt(SYSTEM_PROMPT_PHASE_P, f"Classe ces 3 options :\n{txt}")
    def phase_s_sequencage(self, angle): return self.call_gpt(SYSTEM_PROMPT_PHASE_S, f"Plan pour: {angle.get('titre')}")

# ==========================================
# 3. UI & GESTION D'ÉTAT (SAVE/LOAD)
# ==========================================

st.set_page_config(page_title="IA-BrainStormer GPS", page_icon="🧭", layout="wide")

# CSS
st.markdown("""
<style>
    .main-title {font-size: 3rem; text-align: center; color: #667eea;}
    .verdict-vert {background-color: #d4edda; padding: 1rem; border-radius: 5px; border-left: 5px solid #28a745;}
    .verdict-rouge {background-color: #f8d7da; padding: 1rem; border-radius: 5px; border-left: 5px solid #dc3545;}
    .stButton>button {width: 100%;}
    .history-item {padding: 10px; border-bottom: 1px solid #eee; font-size: 0.9em;}
</style>
""", unsafe_allow_html=True)

# --- GESTION DE SESSION ---
if 'step' not in st.session_state: st.session_state.step = 'crash_test'
if 'history' not in st.session_state: st.session_state.history = [] # Liste des projets de la session

def reset_app():
    # On garde la clé API et l'historique
    keys_keep = ['openai_api_key_input', 'history']
    st.session_state.step = 'crash_test'
    for k in list(st.session_state.keys()):
        if k not in keys_keep: del st.session_state[k]

def load_project(uploaded_file):
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            # On restaure tout l'état
            for key, value in data.items():
                st.session_state[key] = value
            st.success("Projet chargé avec succès !")
            st.rerun()
        except Exception as e:
            st.error(f"Erreur de chargement : {e}")

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Config & Mémoire")
    api_key = st.text_input("Clé API OpenAI", type="password", key="openai_api_key_input")
    model_choice = st.selectbox("Modèle", ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"])
    
    st.markdown("---")
    st.subheader("💾 Sauvegarde / Chargement")
    
    # CHARGEMENT DE FICHIER
    uploaded_file = st.file_uploader("📂 Charger un projet (.json)", type="json")
    if uploaded_file:
        if st.button("Restaurer ce projet"):
            load_project(uploaded_file)

    st.markdown("---")
    # HISTORIQUE DE SESSION
    with st.expander("🕒 Historique de session"):
        if not st.session_state.history:
            st.write("Aucun projet terminé dans cette session.")
        else:
            for i, item in enumerate(reversed(st.session_state.history)):
                st.markdown(f"**{item['time']}** : {item['titre']}")

    st.markdown("---")
    st.button("🔄 Nouveau Projet (Reset)", on_click=reset_app)

if not api_key:
    st.warning("⬅️ Clé API requise.")
    st.stop()

gps = GPSSystem(api_key, model_choice)

# --- CORPS DE L'APP ---
st.markdown("<h1 class='main-title'>🧭 IA-BrainStormer GPS</h1>", unsafe_allow_html=True)

# PHASE 0
if st.session_state.step == 'crash_test':
    st.subheader("Phase 0 : Crash Test")
    idee = st.text_area("Votre idée :", height=100, key="input_idee")
    if st.button("🚀 Crash Test"):
        with st.spinner("Analyse..."):
            st.session_state.crash_test_result = gps.crash_test_dur(idee)
            st.session_state.idee_initiale = idee
            st.rerun()

    if 'crash_test_result' in st.session_state:
        res = st.session_state.crash_test_result
        if res.get('error'): st.error("Erreur IA.")
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

# PHASE G
elif st.session_state.step == 'generation':
    st.subheader("Phase G : Génération")
    if 'phase_g_result' not in st.session_state:
        with st.spinner("Génération..."):
            st.session_state.phase_g_result = gps.phase_g_generation(st.session_state.idee_validee)
            st.rerun()
    else:
        res = st.session_state.phase_g_result
        if res.get('error'): 
            st.error("Erreur format."); 
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

# PHASE P
elif st.session_state.step == 'priorisation':
    st.subheader("Phase P : Priorisation")
    if 'phase_p_result' not in st.session_state:
        with st.spinner("Priorisation..."):
            st.session_state.phase_p_result = gps.phase_p_priorisation(st.session_state.angles_selectionnes)
            st.rerun()
    else:
        res = st.session_state.phase_p_result
        if res.get('error') or 'evaluations' not in res:
            st.error("Erreur format IA.")
            if st.button("Relancer"): del st.session_state.phase_p_result; st.rerun()
        else:
            data_clean = []
            mes_3_angles = st.session_state.angles_selectionnes
            for e in res['evaluations']:
                idx = e.get('id_option', 1) - 1
                titre_reel = mes_3_angles[idx]['titre'] if 0 <= idx < len(mes_3_angles) else "Inconnu"
                total = e.get('score_total_pondere', 0)
                data_clean.append({"Option": f"Option {e.get('id_option')}", "Titre": titre_reel, "Total": total})
            
            st.table(data_clean)
            
            reco = res.get('recommandation', {})
            id_gagnant = reco.get('id_gagnant', 1)
            idx_gagnant = id_gagnant - 1
            titre_gagnant = mes_3_angles[idx_gagnant]['titre'] if 0 <= idx_gagnant < len(mes_3_angles) else "Err"

            st.success(f"🏆 Recommandation : Option {id_gagnant} - {titre_gagnant}")
            st.info(reco.get('raison'))

            options_indices = range(len(mes_3_angles))
            default_idx = idx_gagnant if (0 <= idx_gagnant < len(mes_3_angles)) else 0
            choix_idx = st.selectbox("Choix final :", options_indices, format_func=lambda i: f"Op {i+1}: {mes_3_angles[i]['titre']}", index=default_idx)
            
            if st.button("Générer le Plan -> Phase S"):
                st.session_state.angle_choisi = mes_3_angles[choix_idx]
                st.session_state.step = 'sequencage'
                st.rerun()

# PHASE S
elif st.session_state.step == 'sequencage':
    st.subheader("Phase S : Plan")
    if 'phase_s_result' not in st.session_state:
        with st.spinner("Backcasting..."):
            res = gps.phase_s_sequencage(st.session_state.angle_choisi)
            st.session_state.phase_s_result = res
            
            # SAUVEGARDE HISTORIQUE SESSION
            titre_projet = st.session_state.angle_choisi.get('titre', 'Projet Sans Titre')
            timestamp = datetime.now().strftime("%H:%M")
            st.session_state.history.append({"time": timestamp, "titre": titre_projet})
            
            st.rerun()
    else:
        plan = st.session_state.phase_s_result
        if plan.get('error'): st.error("Erreur plan.")
        else:
            st.info(f"Objectif : {plan.get('resultat_j7')}")
            for j in plan.get('etapes_journalieres', []):
                st.write(f"**{j.get('jour')}** : {j.get('action_principale')}")
            
            # PREPARATION SAUVEGARDE COMPLETE
            # On exclut la clé API et l'objet de connexion de la sauvegarde JSON
            state_to_save = {k: v for k, v in st.session_state.items() if k not in ['openai_api_key_input', 'history']}
            json_str = json.dumps(state_to_save, indent=2, ensure_ascii=False)
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("💾 SAUVEGARDER LE PROJET (JSON)", json_str, "projet_gps_save.json", type="primary")
            with col2:
                st.button("Nouveau Projet", on_click=reset_app)
