import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="ROADWATCH | Accident Analytics",
    page_icon="🚦",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(145deg, #07111f 0%, #0d1728 55%, #121a2d 100%);
    color: #f4f7fb;
}
[data-testid="stMetric"] {
    background: rgba(255,255,255,.06);
    border: 1px solid rgba(255,255,255,.10);
    padding: 16px;
    border-radius: 14px;
}
h1, h2, h3 {color: #f7fafc;}
</style>
""", unsafe_allow_html=True)

st.title("🚦 ROADWATCH")
st.caption("DISTRIBUTED ROAD ACCIDENT HOTSPOT ANALYSIS • HADOOP MAPREDUCE")

# ---------------------------------------------------------
# LOAD HADOOP OUTPUTS
# ---------------------------------------------------------
hotspot_path = Path("outputs/hotspots.csv")
analytics_path = Path("outputs/analytics/roadwatch_analytics.csv")

if not hotspot_path.exists():
    st.error("Hotspot output not found: outputs/hotspots.csv")
    st.stop()

if not analytics_path.exists():
    st.error("Analytics output not found: outputs/analytics/roadwatch_analytics.csv")
    st.stop()

df = pd.read_csv(hotspot_path)
analytics = pd.read_csv(analytics_path)

required = {"latitude", "longitude", "accident_count"}
if not required.issubset(df.columns):
    st.error("hotspots.csv must contain latitude, longitude and accident_count.")
    st.stop()

for col in required:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=list(required))
df = df[
    df.latitude.between(-90, 90)
    & df.longitude.between(-180, 180)
    & (df.accident_count > 0)
]

analytics["year"] = pd.to_numeric(analytics["year"], errors="coerce")
analytics["value"] = pd.to_numeric(analytics["value"], errors="coerce")
analytics = analytics.dropna(
    subset=["metric", "geography_type", "geography", "year", "value"]
)
analytics["year"] = analytics["year"].astype(int)

if df.empty or analytics.empty:
    st.error("One or more Hadoop output files contain no valid records.")
    st.stop()

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def metric_data(metric, geo_type=None, geography=None):
    result = analytics[analytics["metric"] == metric].copy()

    if geo_type is not None:
        result = result[result["geography_type"] == geo_type]

    if geography is not None:
        result = result[result["geography"] == geography]

    return result


def show_bar(data, x, y, title, color="#ff8c42", horizontal=False):
    if data.empty:
        st.info("No records available for this selection.")
        return

    if horizontal:
        fig = px.bar(
            data,
            x=x,
            y=y,
            orientation="h",
            color=x,
            color_continuous_scale=["#ffb703", "#fb5607", "#d00000"],
            labels={x: x.replace("_", " ").title(),
                    y: y.replace("_", " ").title()}
        )
    else:
        fig = px.bar(
            data,
            x=x,
            y=y,
            color_discrete_sequence=[color],
            labels={x: x.replace("_", " ").title(),
                    y: y.replace("_", " ").title()}
        )

    fig.update_layout(
        title=title,
        template="plotly_dark",
        height=430,
        margin=dict(l=10, r=10, t=55, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)


def show_line(data, x, y, title, color="#00c2a8"):
    if data.empty:
        st.info("No records available for this selection.")
        return

    fig = px.line(
        data.sort_values(x),
        x=x,
        y=y,
        markers=True,
        color_discrete_sequence=[color],
        labels={x: x.replace("_", " ").title(),
                y: y.replace("_", " ").title()}
    )
    fig.update_layout(
        title=title,
        template="plotly_dark",
        height=420,
        margin=dict(l=10, r=10, t=55, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------
# MAIN TABS
# ---------------------------------------------------------
tab_hotspot, tab_tn, tab_india = st.tabs([
    "🗺️ Hotspot Map",
    "📍 Tamil Nadu Analysis",
    "🇮🇳 India Analysis"
])

# =========================================================
# TAB 1: EXISTING HOTSPOT MAP
# =========================================================
with tab_hotspot:
    st.subheader("Geographic hotspot map")

    max_count = int(max(1, df.accident_count.max()))

    top_n = st.sidebar.slider(
        "Hotspot cells to show",
        min_value=1,
        max_value=max(1, min(50, len(df))),
        value=max(1, min(20, len(df)))
    )

    min_count = st.sidebar.slider(
        "Minimum accident count per grid cell",
        min_value=1,
        max_value=max_count,
        value=1
    )

    filtered = df[df.accident_count >= min_count].copy()

    if filtered.empty:
        st.warning("No cells meet this threshold. Lower the minimum.")
    else:
        total_records = int(filtered.accident_count.sum())
        hotspot = filtered.sort_values(
            "accident_count", ascending=False
        ).head(top_n)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Reported accidents shown", f"{total_records:,}")
        c2.metric("Grid cells", f"{len(filtered):,}")
        c3.metric(
            "Highest cell count",
            f"{int(filtered.accident_count.max()):,}"
        )
        c4.metric("Cells displayed", f"{len(hotspot):,}")

        center = [
            float(filtered.latitude.mean()),
            float(filtered.longitude.mean())
        ]

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
                popup=(
                    f"<b>Grid cell</b><br>"
                    f"Latitude: {r.latitude:.2f}<br>"
                    f"Longitude: {r.longitude:.2f}<br>"
                    f"Reported accidents: {int(r.accident_count):,}"
                )
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

        show = hotspot.sort_values(
            "accident_count", ascending=False
        ).copy()

        show["location_grid"] = show.apply(
            lambda r: f"{r.latitude:.2f}, {r.longitude:.2f}",
            axis=1
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


# =========================================================
# TAB 2: TAMIL NADU ANALYSIS
# =========================================================
with tab_tn:
    st.header("Tamil Nadu Road Accident Analysis")
    st.caption(
        "District-level statistics (2021–2023) and historical state trends (1993–2025)."
    )

    st.subheader("District-wise accident comparison")

    district_acc = metric_data("accidents", "district")
    district_fatal = metric_data("fatalities", "district")

    if not district_acc.empty:
        years = sorted(district_acc["year"].unique())
        selected_year = st.selectbox(
            "Select year for district comparison",
            years,
            index=len(years) - 1,
            key="tn_district_year"
        )

        col1, col2 = st.columns(2)

        with col1:
            selected = district_acc[
                district_acc["year"] == selected_year
            ].nlargest(15, "value").sort_values("value")

            show_bar(
                selected,
                "value",
                "geography",
                f"Top districts by reported accidents — {selected_year}",
                horizontal=True
            )

        with col2:
            selected = district_fatal[
                district_fatal["year"] == selected_year
            ].nlargest(15, "value").sort_values("value")

            show_bar(
                selected,
                "value",
                "geography",
                f"Top districts by reported fatalities — {selected_year}",
                color="#ff4d6d",
                horizontal=True
            )

        st.markdown("#### District statistics")
        combined = district_acc[
            district_acc["year"] == selected_year
        ][["geography", "value"]].rename(
            columns={"value": "Accidents"}
        )

        fatal_year = district_fatal[
            district_fatal["year"] == selected_year
        ][["geography", "value"]].rename(
            columns={"value": "Fatalities"}
        )

        combined = combined.merge(fatal_year, on="geography", how="outer")
        combined = combined.fillna(0).sort_values(
            "Accidents", ascending=False
        )

        st.dataframe(combined, hide_index=True, use_container_width=True)
    else:
        st.info("District-wise accident data is unavailable.")

    st.markdown("---")
    st.subheader("Tamil Nadu historical accident trends")

    historical_metrics = [
        ("accidents", "Total accidents"),
        ("fatalities", "Persons killed"),
        ("injuries", "Persons injured")
    ]

    historical = []
    for metric, label in historical_metrics:
        part = metric_data(metric, "region", "Tamil Nadu")
        if not part.empty:
            part = part[["year", "value"]].copy()
            part["category"] = label
            historical.append(part)

    if historical:
        trend = pd.concat(historical, ignore_index=True)

        fig = px.line(
            trend.sort_values("year"),
            x="year",
            y="value",
            color="category",
            markers=True,
            labels={
                "year": "Year",
                "value": "Reported count",
                "category": "Metric"
            },
            color_discrete_sequence=["#ff8c42", "#ff4d6d", "#00c2a8"]
        )

        fig.update_layout(
            template="plotly_dark",
            height=480,
            hovermode="x unified",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "Historical series are based on the available Tamil Nadu annual dataset. "
            "The year marked 2024(P) is represented as 2024."
        )
    else:
        st.info("Historical Tamil Nadu trend data is unavailable.")

    st.markdown("---")
    st.subheader("Accident severity over time")

    severity_names = {
        "fatal_accidents": "Fatal accidents",
        "grievous_accidents": "Grievous accidents",
        "minor_accidents": "Minor accidents",
        "non_injury_accidents": "Non-injury accidents"
    }

    severity_parts = []
    for metric, label in severity_names.items():
        part = metric_data(metric, "region", "Tamil Nadu")
        if not part.empty:
            part = part[["year", "value"]].copy()
            part["Accident category"] = label
            severity_parts.append(part)

    if severity_parts:
        severity = pd.concat(severity_parts, ignore_index=True)

        fig = px.line(
            severity.sort_values("year"),
            x="year",
            y="value",
            color="Accident category",
            markers=True,
            labels={"year": "Year", "value": "Number of accidents"}
        )
        fig.update_layout(
            template="plotly_dark",
            height=450,
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Accident severity data is unavailable.")


# =========================================================
# TAB 3: INDIA ANALYSIS
# =========================================================
with tab_india:
    st.header("India Road Accident Analysis")
    st.caption(
        "State-wise, city-wise and national accident statistics from the available datasets."
    )

    st.subheader("State-wise comparison")

    state_acc = metric_data("accidents", "state")
    state_fatal = metric_data("fatalities", "state")

    if not state_acc.empty:
        state_years = sorted(state_acc["year"].unique())
        state_year = st.selectbox(
            "Select year for state comparison",
            state_years,
            index=len(state_years) - 1,
            key="india_state_year"
        )

        col1, col2 = st.columns(2)

        with col1:
            selected = state_acc[
                state_acc["year"] == state_year
            ].nlargest(15, "value").sort_values("value")

            show_bar(
                selected,
                "value",
                "geography",
                f"Top states by accidents — {state_year}",
                horizontal=True
            )

        with col2:
            selected = state_fatal[
                state_fatal["year"] == state_year
            ].nlargest(15, "value").sort_values("value")

            show_bar(
                selected,
                "value",
                "geography",
                f"Top states by fatalities — {state_year}",
                color="#ff4d6d",
                horizontal=True
            )
    else:
        st.info("State-wise statistics are unavailable.")

    st.markdown("---")
    st.subheader("National annual trend")

    national_metrics = [
        ("accidents", "Total accidents"),
        ("fatalities", "Persons killed"),
        ("injuries", "Persons injured")
    ]

    national_parts = []
    for metric, label in national_metrics:
        part = metric_data(metric, "region", "India")
        if not part.empty:
            part = part[["year", "value"]].copy()
            part["category"] = label
            national_parts.append(part)

    if national_parts:
        national = pd.concat(national_parts, ignore_index=True)

        fig = px.line(
            national.sort_values("year"),
            x="year",
            y="value",
            color="category",
            markers=True,
            labels={
                "year": "Year",
                "value": "Reported count",
                "category": "Metric"
            },
            color_discrete_sequence=["#ff8c42", "#ff4d6d", "#00c2a8"]
        )
        fig.update_layout(
            template="plotly_dark",
            height=450,
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(
            "National annual totals are not available under the expected "
            "'India' region label in the analytics output."
        )

    st.markdown("---")
    st.subheader("City-wise comparison")

    city_acc = metric_data("accidents", "city")
    city_fatal = metric_data("fatalities", "city")
    city_injuries = metric_data("injuries", "city")

    if not city_acc.empty:
        city_years = sorted(city_acc["year"].unique())
        city_year = st.selectbox(
            "Select year for city comparison",
            city_years,
            index=len(city_years) - 1,
            key="india_city_year"
        )

        city_table = city_acc[
            city_acc["year"] == city_year
        ][["geography", "value"]].rename(
            columns={"value": "Accidents"}
        )

        for source, label in [
            (city_fatal, "Fatalities"),
            (city_injuries, "Injuries")
        ]:
            values = source[source["year"] == city_year][
                ["geography", "value"]
            ].rename(columns={"value": label})

            if not values.empty:
                city_table = city_table.merge(
                    values, on="geography", how="left"
                )

        city_table = city_table.fillna(0).sort_values(
            "Accidents", ascending=False
        )

        show_bar(
            city_table.head(15).sort_values("Accidents"),
            "Accidents",
            "geography",
            f"Top cities by reported accidents — {city_year}",
            horizontal=True
        )

        st.dataframe(
            city_table,
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("City-wise statistics are unavailable.")


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.markdown("---")
st.caption(
    "HDFS stores the datasets • Hadoop MapReduce processes and aggregates records "
    "• Streamlit, Plotly and Folium visualize the results."
)
