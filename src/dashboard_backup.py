import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Road Accident Hotspots", page_icon="🚦", layout="wide")
st.markdown('''
<style>
.stApp {background: linear-gradient(145deg, #07111f 0%, #0d1728 55%, #121a2d 100%); color: #f4f7fb;}
[data-testid="stMetric"] {background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.10); padding: 16px; border-radius: 14px;}
h1, h2, h3 {color: #f7fafc;}
</style>
''', unsafe_allow_html=True)

st.title("🚦 ROADWATCH")
st.caption("DISTRIBUTED ROAD ACCIDENT HOTSPOT ANALYSIS • HADOOP MAPREDUCE")

path = Path("outputs/hotspots.csv")
if not path.exists():
    st.error("Hotspot output not found. Run the local preview or Hadoop job first. See README.md.")
    st.stop()

df = pd.read_csv(path)
required = {"latitude", "longitude", "accident_count"}
if not required.issubset(df.columns):
    st.error("hotspots.csv must contain latitude, longitude, accident_count.")
    st.stop()
for c in required:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df = df.dropna(subset=list(required))
df = df[(df.latitude.between(-90,90)) & (df.longitude.between(-180,180)) & (df.accident_count > 0)]
if df.empty:
    st.warning("No valid hotspot cells found. Check the dataset's GPS columns.")
    st.stop()

max_count = int(max(1, df.accident_count.max()))
top_n = st.sidebar.slider(
    "Hotspot cells to show",
    min_value=1,
    max_value=max(1, min(50, len(df))),
    value=max(1, min(20, len(df)))
)
min_count = st.sidebar.slider("Minimum accident count per grid cell", 1, max_count, 1)
filtered = df[df.accident_count >= min_count].copy()
if filtered.empty:
    st.warning("No cells meet this threshold. Lower the minimum.")
    st.stop()

total_records = int(filtered.accident_count.sum())
hotspot = filtered.sort_values("accident_count", ascending=False).head(top_n)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Reported accidents shown", f"{total_records:,}")
c2.metric("Grid cells", f"{len(filtered):,}")
c3.metric("Highest cell count", f"{int(filtered.accident_count.max()):,}")
c4.metric("Cells displayed", f"{len(hotspot):,}")


st.subheader("Geographic hotspot map")

center = [float(filtered.latitude.mean()), float(filtered.longitude.mean())]

m = folium.Map(
    location=center,
    zoom_start=7,
    tiles="OpenStreetMap",
    control_scale=True
)

HeatMap(
    filtered[["latitude", "longitude", "accident_count"]].values.tolist(),
    radius=25,
    blur=20,
    min_opacity=0.4,
    name="Accident density"
).add_to(m)

cluster = MarkerCluster(name="Hotspot cells").add_to(m)

for _, r in hotspot.iterrows():
    folium.CircleMarker(
        location=[r.latitude, r.longitude],
        radius=max(5, min(18, 4 + float(r.accident_count) ** 0.5)),
        color="#ff4d6d",
        weight=2,
        fill=True,
        fill_color="#ff8c42",
        fill_opacity=0.8,
        tooltip=f"{int(r.accident_count):,} reported accidents",
        popup=f"<b>Grid cell</b><br>Latitude: {r.latitude:.2f}<br>Longitude: {r.longitude:.2f}<br>Reported accidents: {int(r.accident_count):,}"
    ).add_to(cluster)

folium.LayerControl().add_to(m)

st_folium(
    m,
    height=750,
    use_container_width=True,
    returned_objects=[]
)

st.caption(
    "Heat intensity reflects reported accident counts per 0.01° grid cell. "
    "Locations represent district/city-level coordinates, not individual crash sites."
)

st.markdown("---")

st.subheader("Top hotspot cells")

show = hotspot.sort_values("accident_count", ascending=False).copy()
show["location_grid"] = show.apply(
    lambda r: f"{r.latitude:.2f}, {r.longitude:.2f}", axis=1
)

st.dataframe(
    show[["location_grid", "accident_count"]].rename(
        columns={
            "location_grid": "Latitude, Longitude",
            "accident_count": "Reported accidents"
        }
    ),
    hide_index=True,
    use_container_width=True
)

st.markdown("---")

st.subheader("Hotspot concentration")

fig = px.bar(
    show.sort_values("accident_count"),
    x="accident_count",
    y="location_grid",
    orientation="h",
    labels={
        "accident_count": "Reported accidents",
        "location_grid": "Grid cell"
    },
    color="accident_count",
    color_continuous_scale=["#ffb703", "#fb5607", "#d00000"]
)

fig.update_layout(
    template="plotly_dark",
    height=500,
    margin=dict(l=5, r=5, t=10, b=5),
    coloraxis_showscale=False
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("HDFS stores input • Hadoop MapReduce aggregates grid cells • Streamlit/Folium visualizes reducer output.")
