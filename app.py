import streamlit as st
import plotly.express as px
from src.generate_data import generate_commandes, generate_palettes
from src.optimizer import optimiser_chargement, resume_chargement, detail_chargement

st.set_page_config(page_title="Optimiseur de Chargement", layout="wide")
st.title("Optimiseur de Chargement — Logistique & Transport")

#SIDEBAR
st.sidebar.title("⚙️ Paramètres de simulation")
st.sidebar.markdown("Simule un plan de chargement à partir de commandes générées aléatoirement.")
n_orders = st.sidebar.slider("Nombre de commandes", min_value=10, max_value=100, value=20, step=5)
seed = st.sidebar.number_input("Graine aléatoire", value=42)
st.sidebar.markdown("---")
st.sidebar.info("Les données sont simulées à partir de contraintes réelles observées en entrepôt logistique.")

#DONNÉES
df_cmd = generate_commandes(n_orders=n_orders, seed=int(seed))
df_pal = generate_palettes(df_cmd)
camions = optimiser_chargement(df_pal)
df_resume = resume_chargement(camions)
df_detail = detail_chargement(camions)

nb_fp = len(df_pal[df_pal["PALLET_TYPE"] == "FP"])
nb_ltl = len(df_pal[df_pal["PALLET_TYPE"] == "LTL"])
nb_stacked = df_resume["PALETTES_STACKEES"].sum()

#KPIs
st.subheader("Vue globale")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Commandes", len(df_cmd["ORDER_ID"].unique()))
col2.metric("Palettes FP", nb_fp)
col3.metric("Lignes LTL", nb_ltl)
col4.metric("Camions nécessaires", len(camions))
col5.metric("Palettes stackées", int(nb_stacked))

st.markdown("---")

#GRAPHIQUE REMPLISSAGE
st.subheader("Taux de remplissage par camion")
fig1 = px.bar(
    df_resume,
    x="TRUCK_ID",
    y="TAUX_REMPLISSAGE_%",
    color="CLIENT",
    text="TAUX_REMPLISSAGE_%",
    hover_data=["CLIENT", "DESTINATION", "NB_COMMANDES", "PALETTES_STACKEES"],
    labels={"TAUX_REMPLISSAGE_%": "Remplissage (%)", "TRUCK_ID": "Camion", "CLIENT": "Client"},
)
fig1.update_traces(texttemplate="%{text}%", textposition="outside")
fig1.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Max 33 palettes")
st.plotly_chart(fig1, use_container_width=True)

st.markdown("---")

#TABLEAU RÉSUMÉ
st.subheader("🗺️ Plan de chargement par camion")
st.dataframe(
    df_resume.rename(columns={
        "TRUCK_ID": "Camion",
        "CLIENT": "Client",
        "DESTINATION": "Destination",
        "PALETTES_AU_SOL": "Palettes au sol",
        "PALETTES_STACKEES": "Dont stackées",
        "TAUX_REMPLISSAGE_%": "Remplissage (%)",
        "NB_COMMANDES": "Nb commandes",
    }),
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")

#DÉTAIL D'UN CAMION
st.subheader("🔍 Détail d'un camion")
options = df_resume.apply(
    lambda r: f"{r['TRUCK_ID']} — {r['CLIENT']} — {r['DESTINATION']} ({r['PALETTES_AU_SOL']} palettes)",
    axis=1
).tolist()
camion_choisi = st.selectbox("Choisir un camion", options)
truck_id = int(camion_choisi.split(" ")[1])
df_camion = df_detail[df_detail["TRUCK_ID"] == truck_id].copy()
df_camion["STACKED"] = df_camion["STACKED"].map({True: "✅ Oui", False: "❌ Non"})
st.dataframe(
    df_camion.rename(columns={
        "SLOT": "Slot",
        "PALLET_BOTTOM": "Palette basse",
        "PALLET_TOP": "Palette haute",
        "HAUTEUR_TOTALE_CM": "Hauteur totale (cm)",
        "STACKED": "Stackée ?",
    }).drop(columns=["TRUCK_ID"]),
    use_container_width=True,
    hide_index=True,
)