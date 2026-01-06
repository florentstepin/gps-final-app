"""
Application IA-BrainStormer GPS (Version Monolithe Finale)
Système complet : Crash Test DUR + Génération + Priorisation + Séquençage
Mode BYOK (Bring Your Own Key)
"""
import streamlit as st
import json
from openai import OpenAI

# ==========================================
# 1. LES PROMPTS SYSTÈME (LE CERVEAU)
# ==========================================

SYSTEM_PROMPT_CRASH_TEST = """Tu agis en tant qu'Auditeur Stratégique impitoyable ("Devil's Advocate"). 
Analyse l'idée selon la matrice D.U.R. (Douloureux, Urgent, Reconnu). Note chaque pilier sur 10.

RÈGLE DE DÉCISION :
- Si Score Total < 20/30 OU si une seule note est < 5/10 : Le projet est "ROUGE".
- Sinon : Le projet est "VERT".

FORMAT DE RÉPONSE ATTENDU (JSON) :
{
  "score_D": 0, "score_U": 0, "score_R": 0, "total": 0,
  "verdict": "VERT ou ROUGE",
  "analyse_critique": "Phrase courte",
  "conseil_architecte": "Action concrète"
}"""

SYSTEM_PROMPT_PHASE_G = """Tu es l'Explorateur de Perspectives. Génère 10 angles radicalement différents.
FORMAT JSON : { "angles": [ {"id": 1, "titre": "...", "cible_precise": "...", "opportunite": "..."} ] }"""

SYSTEM_PROMPT_PHASE_P = """Tu es l'Expert en Stratégie. Utilise la Matrice de Conviction.
Pondération : Douleur (Coef 4), Unicité (Coef 3), Alignement (Coef 3).
NE CHOISIS PAS LA FACILITÉ.
FORMAT JSON : { "evaluations": [...], "recommandation": {"id_gagnant": 1, "raison": "..."} }"""

SYSTEM_PROMPT_PHASE_S = """Tu es Chef de Projet Sprint. Utilise le BACKCASTING.
Pars de J+7 (Résultat Final) et remonte jusqu'à J+1.
FORMAT JSON : { "resultat_j7": "...", "etapes_journalieres": [ {"jour": "J+7", "action_principale": "...", "detail_execution": "..."} ] }"""

# ==========================================
# 2. LES CLASSES UTILITAIRES (LA MÉCANIQUE)
# ==========================================

class OpenAIHelper:
    def __init__(self, api_key: str, default_model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.default_model = default_model
    
    def call_gpt(self, system_prompt: str, user_message: str, model: str = None, response_format: dict = None) -> dict:
        if model is None: model = self.default_model
        try:
            messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]
            call_params = {"model": model, "messages": messages, "temperature": 0.7}
            if response_format: call_params["response_format"] = response_format
            
            response = self.client.chat.completions.create(**call_params)
            content = response.choices[0].message.content
            try: return json.loads(content)
            except json.JSONDecodeError: return {"raw_response": content}
        except Exception as e:
            return {"error": True, "message": f"Erreur API : {str(e)}"}

class GPSSystem:
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.openai_helper = OpenAIHelper(api_key, default_model=model)
    
    def crash_test_dur(self, idee: str) -> dict:
        return self.openai_helper.call_gpt(
            SYSTEM_PROMPT_CRASH_TEST, 
            f"Analyse cette idée : {idee}", 
            response_format={"type": "json_object"}
        )
    
    def phase_g_generation(self, idee: str) -> dict:
        return self.openai_helper.call_gpt(
            SYSTEM_PROMPT_PHASE_G, 
            f"Génère 10 angles pour : {idee}", 
            response_format={"type": "json_object"}
        )

    def phase_p_priorisation(self, angles: list) -> dict:
        angles_text = "\n".join([f"ID {a['id']}: {a['titre']} ({a['cible_precise']})" for a in angles])
        return self.openai_helper.call_gpt(
            SYSTEM_PROMPT_PHASE_P, 
            f"Classe ces options :\n{angles_text}", 
            response_format={"type": "json_object"}
        )

    def phase_s_sequencage(self, angle: dict) -> dict:
        return self.openai_helper.call_gpt(
            SYSTEM_PROMPT_PHASE_S, 
            f"Plan Backcasting pour : {angle['titre']}", 
            response_format={"type": "json_object"}
        )

# ==========================================
# 3. L'INTERFACE UTILISATEUR (L'APP)
# ==========================================

# Fonction Reset (Callback)
def reset_app():
    keys_to_keep = ['step', 'openai_api_key_input']
    st.session_state.step = 'crash_test'
    for key in list(st.session_state.keys()):
        if key not in keys_to_keep: del st.session_state[key]

# Config Page
st.set_page_config(page_title="IA-BrainStormer GPS", page_icon="🧭", layout="wide")

# CSS
st.markdown("""
<style>
    .main-title {font-size: 3rem; text-align: center; color: #667eea;}
    .verdict-vert {background-color: #d4edda; padding: 1rem; border-radius: 5px; border-left: 5px solid #28a745;}
    .verdict-rouge {background-color: #f8d7da; padding: 1rem; border-radius: 5px; border-left: 5px solid #dc3545;}
    .stButton>button {width: 100%;}
</style>
""", unsafe_allow_html=True)

if 'step' not in st.session_state: st.session_state.step = 'crash_test'

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configuration")
    st.info("🔒 Mode Sécurisé (BYOK)")
    
    # Champ Clé API
    api_key = st.text_input("Clé API OpenAI", type="password", key="openai_api_key_input")
    model_choice = st.selectbox("Modèle", ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"])
    
    st.progress(0 if st.session_state.step == 'crash_test' else 33 if st.session_state.step == 'generation' else 66 if st.session_state.step == 'priorisation' else 100)
    st.button("🔄 Nouveau Projet", on_click=reset_app)

# --- VÉRIFICATION CLÉ ---
if not api_key:
    st.markdown("<h1 class='main-title'>🧭 IA-BrainStormer GPS</h1>", unsafe_allow_html=True)
    st.warning("⬅️ Veuillez entrer votre clé API OpenAI dans la barre latérale gauche pour activer le système.")
    with st.expander("Comment obtenir une clé ?"):
        st.write("1. Allez sur platform.openai.com/api-keys\n2. Créez une clé ('sk-...')\n3. Collez-la ici. Elle n'est pas stockée.")
    st.stop()

gps = GPSSystem(api_key, model_choice)

# --- CORPS DE L'APP ---
st.markdown("<h1 class='main-title'>🧭 IA-BrainStormer GPS</h1>", unsafe_allow_html=True)

# PHASE 0
if st.session_state.step == 'crash_test':
    st.subheader("Phase 0 : Crash Test D.U.R.")
    idee = st.text_area("Votre idée :", height=150, placeholder="Décrivez votre projet...")
    if st.button("🚀 Lancer le Crash Test"):
        if not idee: st.error("Décrivez votre idée.")
        else:
            with st.spinner("Analyse en cours..."):
                res = gps.crash_test_dur(idee)
                st.session_state.crash_test_result = res
                st.session_state.idee_initiale = idee
                st.rerun()

    if 'crash_test_result' in st.session_state:
        res = st.session_state.crash_test_result
        c1, c2, c3 = st.columns(3)
        c1.metric("Douleur", f"{res.get('score_D')}/10"); c2.metric("Urgence", f"{res.get('score_U')}/10"); c3.metric("Reconnu", f"{res.get('score_R')}/10")
        
        if res.get('verdict') == 'VERT': st.markdown(f"<div class='verdict-vert'>✅ {res.get('analyse_critique')}</div>", unsafe_allow_html=True)
        else: st.markdown(f"<div class='verdict-rouge'>🛑 {res.get('analyse_critique')} <br>💡 {res.get('conseil_architecte')}</div>", unsafe_allow_html=True)
        
        validee = st.text_area("Reformulez avant la suite :", value=st.session_state.get('idee_validee', st.session_state.idee_initiale))
        if st.button("Valider et Passer à la Phase G"):
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
        selection = []
        for a in st.session_state.phase_g_result.get('angles', []):
            with st.expander(f"📐 {a['titre']}"):
                st.write(a['opportunite'])
                if st.checkbox("Sélectionner", key=f"chk_{a['id']}"): selection.append(a)
        
        if len(selection) == 3:
            if st.button("Passer à la Phase P"):
                st.session_state.angles_selectionnes = selection
                st.session_state.step = 'priorisation'
                st.rerun()
        else: st.warning(f"Sélectionnez exactement 3 angles ({len(selection)}/3)")

# PHASE P
elif st.session_state.step == 'priorisation':
    st.subheader("Phase P : Priorisation")
    if 'phase_p_result' not in st.session_state:
        with st.spinner("Calcul des scores..."):
            st.session_state.phase_p_result = gps.phase_p_priorisation(st.session_state.angles_selectionnes)
            st.rerun()
    else:
        evals = st.session_state.phase_p_result.get('evaluations', [])
        st.table([{ "Angle": e['titre'], "Score Total": e['score_total_pondere']} for e in evals])
        st.success(f"Recommandation : Angle #{st.session_state.phase_p_result['recommandation']['id_gagnant']}")
        
        options = {e['id']: e['titre'] for e in evals}
        choix = st.selectbox("Votre choix final :", list(options.keys()), format_func=lambda x: options[x])
        if st.button("Générer le Plan (Phase S)"):
            st.session_state.angle_choisi = next(a for a in st.session_state.angles_selectionnes if a["id"] == choix)
            st.session_state.step = 'sequencage'
            st.rerun()

# PHASE S
elif st.session_state.step == 'sequencage':
    st.subheader("Phase S : Plan d'Action")
    if 'phase_s_result' not in st.session_state:
        with st.spinner("Backcasting..."):
            st.session_state.phase_s_result = gps.phase_s_sequencage(st.session_state.angle_choisi)
            st.rerun()
    else:
        plan = st.session_state.phase_s_result
        st.info(f"Objectif J+7 : {plan.get('resultat_j7')}")
        for j in plan.get('etapes_journalieres', []):
            st.write(f"**{j['jour']}** : {j['action_principale']}")
        
        st.download_button("💾 Télécharger JSON", data=json.dumps(plan, indent=2), file_name="plan.json")
