import pandas as pd
import streamlit as st
import plotly.express as px
import os

# ===================== CONFIG =====================
st.set_page_config(page_title="Population Dashboard", layout="wide")

@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path): return pd.DataFrame()
    df = pd.read_csv(file_path)
    df["year"] = pd.to_numeric(df["year"], errors='coerce').fillna(0).astype(int)
    df["population"] = pd.to_numeric(df["population"], errors="coerce").fillna(0)
    return df

def format_pop(val):
    if val <= 0: return "0"
    if val >= 1_000_000_000: return f"{val/1_000_000_000:.2f} Mrd."
    if val >= 1_000_000: return f"{val/1_000_000:.1f} Mio."
    return f"{val:,.0f}".replace(",", ".")

data = load_data("population_continent.csv")

st.markdown("<h1 style='text-align:center;'>🌍 Global Population Dashboard</h1>", unsafe_allow_html=True)

# ===================== FILTER =====================
c1, c2, c3 = st.columns(3)
with c1:
    region_options = ["World"] + sorted(data["continent"].unique().tolist())
    sel_reg = st.selectbox("🌍 Gebiet auswählen", region_options, index=0)

filtered_data = data.copy() if sel_reg == "World" else data[data["continent"] == sel_reg]

with c2:
    countries = ["Keine Auswahl"] + sorted(filtered_data["country"].unique())
    # Geändert von multiselect zu selectbox für automatisches Zuklappen
    sel_country = st.selectbox("Land auswählen", countries, index=0)

with c3:
    sel_year = st.slider("Jahr", int(data.year.min()), int(data.year.max()), int(data.year.max()))

# ===================== KPI SEKTION =====================
kpi_l, kpi_r = st.columns(2)

def get_stats(df_scope, year):
    curr = df_scope[df_scope["year"] == year]["population"].sum()
    prev = df_scope[df_scope["year"] == year - 1]["population"].sum()
    delta = ((curr - prev) / prev * 100) if prev > 0 else 0
    return curr, delta

with kpi_l:
    pop_reg, growth_reg = get_stats(filtered_data, sel_year)
    label_reg = "Welt" if sel_reg == "World" else sel_reg
    st.metric(label=f"Bevölkerung {label_reg}", value=format_pop(pop_reg), delta=f"{growth_reg:+.2f}% Wachstumsrate")

with kpi_r:
    if sel_country != "Keine Auswahl":
        c_data = data[data["country"] == sel_country]
        pop_c, growth_c = get_stats(c_data, sel_year)
        st.metric(label=f"{sel_country}", value=format_pop(pop_c), delta=f"{growth_c:+.2f}% Wachstumsrate")
    else:
        st.metric(label="Ausgewähltes Land", value="Keine Auswahl")

st.markdown("---")

# ===================== WELTKARTE =====================
st.subheader(f"{sel_reg}")
map_data = filtered_data[filtered_data["year"] == sel_year].copy()

# Filter auf Land, falls eines gewählt wurde
if sel_country != "Keine Auswahl":
    map_data = map_data[map_data["country"] == sel_country]

map_data["Zahl"] = map_data["population"].apply(format_pop)

scope_map = {"Africa": "africa", "Asia": "asia", "Europe": "europe"}
current_scope = scope_map.get(sel_reg, "world")
current_proj = "natural earth" if sel_reg == "World" else "mercator"

fig_map = px.choropleth(
    map_data, locations="iso3", color="population", hover_name="country",
    custom_data=["Zahl"], color_continuous_scale="Viridis", 
    scope=current_scope,
    projection=current_proj
)

# --- SKALA ---
max_val = map_data["population"].max() if not map_data.empty else 0
if max_val >= 1_000_000_000:
    tick_vals = [i * 200_000_000 for i in range(int(max_val/200_000_000) + 2)]
    tick_text = [f"{v/1_000_000_000:.1f} Mrd." for v in tick_vals]
elif max_val >= 1_000_000:
    tick_vals = [i * 50_000_000 for i in range(int(max_val/50_000_000) + 2)]
    tick_text = [f"{v/1_000_000:.0f} Mio." for v in tick_vals]
else:
    tick_vals, tick_text = None, None

fig_map.update_layout(coloraxis_colorbar=dict(
    title="Bevölkerung", tickvals=tick_vals, ticktext=tick_text
))

# --- ZOOMS ---
if sel_reg == "Amerika":
    fig_map.update_geos(lataxis_range=[-56, 75], lonaxis_range=[-175, -30])
elif sel_reg == "Asia":
    fig_map.update_geos(lataxis_range=[-15, 65], lonaxis_range=[25, 160])
elif sel_reg == "Oceania":
    fig_map.update_geos(lataxis_range=[-55, 10], lonaxis_range=[100, 185])

fig_map.update_traces(hovertemplate="<b>%{hovertext}</b><br>Bevölkerung<br>%{customdata[0]}<extra></extra>")
fig_map.update_layout(
    margin={"r":0,"t":0,"l":0,"b":0}, height=650,
    geo=dict(showcountries=True, countrycolor="DarkGrey", showocean=True, oceancolor="AliceBlue")
)
st.plotly_chart(fig_map, use_container_width=True)

# ===================== DIAGRAMME =====================
u1, u2 = st.columns(2)
chart_year_data = filtered_data[(filtered_data["year"] == sel_year) & (filtered_data["population"] > 0)]

with u1:
    top10 = chart_year_data.nlargest(10, "population").sort_values("population", ascending=True)
    top10["pop_text"] = top10["population"].apply(format_pop)
    st.plotly_chart(px.bar(top10, x="population", y="country", orientation="h", 
                           title=f"Größte Population ({sel_reg})", text="pop_text", 
                           color="population", color_continuous_scale="Reds"), use_container_width=True)

with u2:
    bottom10 = chart_year_data.nsmallest(10, "population").sort_values("population", ascending=True)
    bottom10["pop_text"] = bottom10["population"].apply(format_pop)
    st.plotly_chart(px.bar(bottom10, x="population", y="country", orientation="h", 
                           title=f"Kleinste Population ({sel_reg})", text="pop_text", 
                           color="population", color_continuous_scale="Blues_r"), use_container_width=True)