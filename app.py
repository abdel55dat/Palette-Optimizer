import streamlit as st
import plotly.express as px
from src.generate_data import generate_commandes, generate_palettes
from src.optimizer import optimiser_chargement, resume_chargement, detail_chargement

st.set_page_config(page_title="Optimiseur de Chargement Ceva", layout="wide")
st.title("Optimiseur de Chargement — XXXXXX Logistics")

#SIDEBAR
st.sidebar.title("Paramètres de simulation")
st.sidebar.markdown("Ajuste le nombre de commandes à planifier et génère un plan de chargement.")
n_orders = st.sidebar.slider("Nombre de commandes", min_value=10, max_value=100, value=20, step=5)
seed = st.sidebar.number_input("Graine aléatoire (reproductibilité)", value=42)
st.sidebar.markdown("---")
st.sidebar.info("Les données sont simulées à partir de contraintes réelles observées en entrepôt logistique.")

#DONNÉES
df_cmd = generate_commandes(n_orders=n_orders, seed=int(seed))
df_pal = generate_palettes(df_cmd)
camions = optimiser_chargement(df_pal)
df_resume = resume_chargement(camions)
df_detail = detail_chargement(camions)

#KPIs
st.subheader("📊 Vue globale")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Commandes à livrer", len(df_cmd["ORDER_ID"].unique()))
col2.metric("Palettes totales", len(df_pal))
col3.metric("Camions nécessaires", len(camions))
col4.metric("Remplissage moyen", f"{df_resume['TAUX_REMPLISSAGE_%'].mean():.1f}%")

st.markdown("---")

#GRAPHIQUE REMPLISSAGE
st.subheader("Taux de remplissage par camion")
fig1 = px.bar(
    df_resume, x="TRUCK_ID", y="TAUX_REMPLISSAGE_%",
    color="TAUX_REMPLISSAGE_%", color_continuous_scale="RdYlGn",
    range_color=[0, 100],
    text="TAUX_REMPLISSAGE_%",
    labels={"TAUX_REMPLISSAGE_%": "Remplissage (%)", "TRUCK_ID": "Camion"},
)
fig1.update_traces(texttemplate="%{text}%", textposition="outside")
fig1.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Max 33 palettes")
fig1.update_layout(coloraxis_showscale=False)
st.plotly_chart(fig1, use_container_width=True)

st.markdown("---")

#TABLEAU RÉSUMÉ PAR CAMION
st.subheader("Plan de chargement par camion")
st.dataframe(
    df_resume.rename(columns={
        "TRUCK_ID": "Camion",
        "PALETTES_AU_SOL": "Palettes au sol",
        "TAUX_REMPLISSAGE_%": "Remplissage (%)",
        "NB_COMMANDES": "Nb commandes",
        "CLIENTS": "Clients",
        "DESTINATIONS": "Destinations",
    }),
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")

#DÉTAIL D'UN CAMION
st.subheader("🔍 Détail d'un camion")
camion_choisi = st.selectbox("Choisir un camion", df_resume["TRUCK_ID"].tolist())
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