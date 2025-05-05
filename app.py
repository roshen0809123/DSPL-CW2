import streamlit as st
import pandas as pd
import plotly.express as px
import re
import base64

st.set_page_config(page_title="Aid Effectiveness Dashboard", layout="wide", initial_sidebar_state="expanded")

def set_background(image_file):
    with open(image_file, "rb") as img:
        encoded = base64.b64encode(img.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        .block-container {{
            background-color: rgba(0, 0, 0, 0.65);
            padding: 2rem;
            border-radius: 10px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_background("money.jpg")

@st.cache_data
def load_data():
    return pd.read_csv("aid effectiveness (1).csv")

data = load_data()

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Overview", "Aid Effectiveness"])

# overview page
if page == "Overview":
    st.title("Sri Lanka Aid Effectiveness Dashboard")

    st.markdown("""
    Welcome to the **Aid Effectiveness Dashboard!**

    Aid effectiveness is the impact that aid has in reducing poverty and inequality, increasing growth, building capacity, and accelerating achievement of the Millennium Development Goals set by the international community. Indicators here cover aid received as well as progress in reducing poverty and improving education, health, and other measures of human welfare.
    """)

    st.subheader("Dataset")
    st.dataframe(data)

    st.subheader("Column Information")
    st.markdown("""
    - **Year**: The year the data was recorded.  
    - **Indicator Name**: The descriptive name of the indicator.  
    - **Indicator Code**: A short code representing each indicator. 
    - **Value**: The numeric value of the indicator for the given year.
    """)

    st.subheader("Dataset Summary")
    st.write(f"**Total Rows**: {len(data):,}")
    st.write(f"**Time Range**: {int(data['Year'].min())} - {int(data['Year'].max())}")
    st.write(f"**Unique Indicators**: {data['Indicator Name'].nunique()}")

# aid effectiveness page
elif page == "Aid Effectiveness":
    st.title("Aid Effectiveness")

    st.sidebar.header("Filter Options")
    indicators = sorted(data["Indicator Name"].dropna().unique())
    selected_indicator = st.sidebar.selectbox("Select Indicators for Bar and Line Chart", indicators)

    years = data["Year"].dropna().unique()
    min_year, max_year = int(years.min()), int(years.max())
    year_range = st.sidebar.slider("Select Year Range for Bar and Line Chart", min_year, max_year, (min_year, max_year))

    filtered_data = data[
        (data["Indicator Name"] == selected_indicator) &
        (data["Year"] >= year_range[0]) &
        (data["Year"] <= year_range[1])
    ]

    # line chart
    st.markdown("## Line Chart")
    fig_line = px.line(
        filtered_data, x="Year", y="Value",
        title=f"{selected_indicator} Over Time",
        markers=True, template="plotly_dark"
    )
    fig_line.update_layout(title_x=0.2, font=dict(size=16), xaxis_title="Year", yaxis_title="Value")
    st.plotly_chart(fig_line, use_container_width=True)

    # bar chart
    st.markdown("## Bar Chart")
    fig_col = px.bar(
        filtered_data.sort_values("Year"),
        x="Year", y="Value",
        title=f"{selected_indicator} - Column Chart",
        template="plotly_dark", height=600
    )
    fig_col.update_layout(title_x=0.2, font=dict(size=16), xaxis_title="Year", yaxis_title="Value (USD or Units)")
    fig_col.update_traces(texttemplate='%{y:.2s}', textposition='outside')
    st.plotly_chart(fig_col, use_container_width=True)

    # pie chart
    st.markdown("## Pie Chart: Net Bilateral Aid Flows from DAC Donors (by Year)")

    dac_data = data[data["Indicator Name"].str.contains("Net bilateral aid flows from DAC donors", case=False, na=False)]
    pie_years = sorted(dac_data["Year"].dropna().unique())
    selected_pie_year = st.sidebar.selectbox("Select Year for Pie Chart", pie_years, index=len(pie_years) - 1)

    def extract_country(name):
        match = re.search(r'DAC donors,\s*(.*?)\s*\(', name)
        return match.group(1).strip() if match else "Unknown"

    dac_data["Donor Country"] = dac_data["Indicator Name"].apply(extract_country)

    valid_countries = [
        "Australia", "Austria", "Belgium", "Canada", "European Union institutions", "Switzerland",
        "Czechia", "Germany", "Denmark", "Spain", "Finland", "France", "United Kingdom",
        "Greece", "Hungary", "Ireland", "Iceland", "Italy", "Japan", "Korea, Rep.",
        "Luxembourg", "Netherlands", "Norway", "New Zealand", "Poland", "Portugal",
        "Slovenia", "Sweden", "United States"
    ]

    filtered_dac = dac_data[
        (dac_data["Donor Country"].isin(valid_countries)) &
        (dac_data["Year"] == selected_pie_year)
    ]

    grouped = filtered_dac.groupby("Donor Country")["Value"].sum().reset_index()
    grouped["Share"] = grouped["Value"] / grouped["Value"].sum() * 100

    top_donors = grouped[grouped["Share"] >= 1]
    others = grouped[grouped["Share"] < 1]
    others_sum = others["Value"].sum()

    if not others.empty:
        others_row = pd.DataFrame([{"Donor Country": "Others (<1%)", "Value": others_sum}])
        pie_data = pd.concat([top_donors[["Donor Country", "Value"]], others_row], ignore_index=True)
    else:
        pie_data = grouped[["Donor Country", "Value"]]

    fig_pie = px.pie(
        pie_data, names="Donor Country", values="Value",
        title=f"DAC Donor Aid by Country – {selected_pie_year} (Grouped <1%)",
        template="plotly_dark", height=700
    )
    fig_pie.update_traces(textinfo='label+percent', textfont_size=16, marker=dict(line=dict(color='#000000', width=1)))
    fig_pie.update_layout(title_x=0.2, font=dict(size=16), legend_title="Country", showlegend=True)
    st.plotly_chart(fig_pie, use_container_width=True)

    # area chart
    st.markdown("## Area Chart")

    multi_indicators = st.sidebar.multiselect(
        "Select Indicators for Area Chart", options=indicators, default=indicators[:2]
    )

    area_data = data[
        (data["Indicator Name"].isin(multi_indicators)) &
        (data["Year"] >= year_range[0]) & (data["Year"] <= year_range[1])
    ]

    if not area_data.empty and multi_indicators:
        pivot_df = area_data.pivot_table(
            index="Year", columns="Indicator Name", values="Value", aggfunc="sum"
        ).fillna(0).reset_index().sort_values("Year")

        fig_area = px.area(
            pivot_df, x="Year", y=multi_indicators,
            title="Stacked Area Chart of Selected Indicators",
            template="plotly_dark", height=600
        )
        fig_area.update_layout(title_x=0.2, font=dict(size=16), xaxis_title="Year", yaxis_title="Value")
        st.plotly_chart(fig_area, use_container_width=True)
    else:
        st.info("Please select at least one indicator for the area chart.")


