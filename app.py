import streamlit as st
import pandas as pd
import plotly.express as px

# Load dataset
df = pd.read_csv("aid effectiveness (1).csv")

# Display raw data
st.subheader("Raw Dataset Preview")
st.dataframe(df)

# Clean column names
df.columns = [col.strip().replace(" ", "_") for col in df.columns]

# Identify the time column (assumed to be "Year")
year_col = "Year" if "Year" in df.columns else df.columns[0]
df[year_col] = pd.to_numeric(df[year_col], errors='coerce')
df = df.dropna(subset=[year_col])
df[year_col] = df[year_col].astype(int)

# Select numeric columns for indicators
num_cols = df.select_dtypes(include='number').columns.tolist()
if year_col in num_cols:
    num_cols.remove(year_col)

# Sidebar filters
st.sidebar.header("Filters")

# Year range filter
min_year = int(df[year_col].min())
max_year = int(df[year_col].max())
year_range = st.sidebar.slider("Select Year Range", min_value=min_year, max_value=max_year,
                               value=(min_year, max_year))

# Single indicator selection
selected_indicator = st.sidebar.selectbox("Select One Indicator to Display", options=num_cols)

# Apply filters
filtered_df = df[(df[year_col] >= year_range[0]) & (df[year_col] <= year_range[1])]
plot_df = filtered_df[[year_col, selected_indicator]].groupby(year_col).sum().reset_index()

# Line Chart
st.subheader(f"📈 Line Chart - {selected_indicator} Over Time")
fig_line = px.line(plot_df, x=year_col, y=selected_indicator,
                   title=f"{selected_indicator} Over Time",
                   labels={year_col: "Year", selected_indicator: selected_indicator})
st.plotly_chart(fig_line, use_container_width=True)

# Bar Chart
st.subheader(f"📊 Bar Chart - {selected_indicator} by Year")
fig_bar = px.bar(plot_df, x=year_col, y=selected_indicator,
                 title=f"{selected_indicator} by Year",
                 labels={year_col: "Year", selected_indicator: selected_indicator})
st.plotly_chart(fig_bar, use_container_width=True)


