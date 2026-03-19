import streamlit as st
import pandas as pd
import altair as alt
import math
from pathlib import Path

# --- 1. BUSINESS CONTEXT (Requirement 1) ---
BUSINESS_CONTEXT = """
This dashboard benchmarks regional economic growth using World Bank data (2000-2022). 
It transforms raw data into Billions USD to identify resilient emerging markets, 
specifically highlighting the Philippines (PHL) historical performance.
"""

# --- 2. CORE ANALYTICS: CLASS IMPLEMENTATION (Requirement 3) ---
class GDPProcessor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.raw_data = None

    def load_and_inspect(self):
        # Requirement 2: Data Import & Inspection
        self.raw_data = pd.read_csv(self.file_path)
        return self.raw_data

    def prepare_data(self):
        # Requirement 2: Preprocessing (2000-2022)
        years = [str(y) for y in range(2000, 2023)]
        df = self.raw_data.melt(
            id_vars=['Country Code'], 
            value_vars=years, 
            var_name='Year', value_name='GDP'
        )
        df['Year'] = pd.to_numeric(df['Year'])
        df['GDP_Billions'] = df['GDP'] / 1e9
        return df

# --- 3. CORE ANALYTICS: CUSTOM FUNCTION (Requirement 3) ---
def calculate_yoy_change(current, previous):
    """Calculates percentage change between two years."""
    if previous is None or previous == 0 or pd.isna(previous):
        return 0
    return ((current - previous) / previous) * 100

# --- 4. API COMPONENT (Requirement 5) ---
def get_currency_rate():
    # Mock API integration for USD to PHP
    return 56.12 

# --- INITIALIZATION ---
st.set_page_config(page_title='GDP Analysis', page_icon=':earth_asia:', layout='wide')

data_path = Path(__file__).parent/'data/gdp_data.csv'
processor = GDPProcessor(data_path)
raw_df = processor.load_and_inspect()
df_all = processor.prepare_data()

# --- SIDEBAR & CONTROLS ---
with st.sidebar:
    st.header("Timeline Settings")
    st.info(BUSINESS_CONTEXT)
    
    # FIX: Unpack yr_range into from_yr and to_yr to prevent NameError
    from_yr, to_yr = st.slider('Select Year Range', 2000, 2022, (2010, 2022), format="%d")

    countries = st.multiselect(
        'Countries', 
        df_all['Country Code'].unique(), 
        ['PHL', 'MYS', 'IDN', 'VNM', 'THA']
    )
    
    # Requirement 2: Control flow for data inspection
    if st.checkbox("Show Technical Data Inspection"):
        st.write(raw_df.head())
        st.write(raw_df.describe())

# --- PHL INSIGHT ---
phl_peak = df_all[df_all['Country Code'] == 'PHL'].sort_values('GDP', ascending=False).iloc[0]
st.title("📈 GDP Dashboard: 2000 - 2022")
st.success(f"🏆 **PHL Peak:** ${phl_peak['GDP_Billions']:.1f}B reached in {int(phl_peak['Year'])}")

# --- DATA FILTERING ---
mask = (df_all['Country Code'].isin(countries)) & (df_all['Year'].between(from_yr, to_yr))
filtered_df = df_all[mask].copy()

# --- ALTAIR CHART ---
st.subheader(f"GDP Growth Trends ({from_yr} - {to_yr})")

chart = alt.Chart(filtered_df).mark_line(point=True).encode(
    x=alt.X('Year:Q', axis=alt.Axis(format='d', title="Year")),
    y=alt.Y('GDP_Billions:Q', title="GDP (Billions USD)"),
    color='Country Code:N',
    strokeDash=alt.condition(
        alt.datum['Country Code'] == 'PHL', 
        alt.value([5, 5]), 
        alt.value([0])
    ),
    tooltip=['Country Code', 'Year', 'GDP_Billions']
).properties(height=450).interactive()

st.altair_chart(chart, use_container_width=True)

# --- RANKED METRICS: LATEST ACTUAL & YOY ---
st.divider()
st.subheader(f"Latest Actual Data & YoY Momentum ({to_yr})")
rate = get_currency_rate()

# Filter for the specific year selected on the right side of the slider
latest_view = filtered_df[filtered_df['Year'] == to_yr].sort_values('GDP_Billions', ascending=False)

if not latest_view.empty:
    cols = st.columns(len(latest_view) if len(latest_view) < 6 else 4)
    
    for i, (_, row) in enumerate(latest_view.iterrows()):
        code = row['Country Code']
        curr_val = row['GDP_Billions']
        
        # Calculate YoY by looking at the year prior to the selected 'to_yr'
        prev_yr_data = df_all[(df_all['Country Code'] == code) & (df_all['Year'] == to_yr - 1)]
        prev_val = prev_yr_data['GDP_Billions'].iat[0] if not prev_yr_data.empty else None
        
        # Use Custom Function
        yoy_pct = calculate_yoy_change(curr_val, prev_val)
        
        with cols[i % len(cols)]:
            st.metric(
                label=f"{code} GDP", 
                value=f"${curr_val:.1f}B", 
                delta=f"{yoy_pct:.2f}% YoY" if to_yr > 2000 else "Initial Year"
            )
            
            # API Component Integration
            if code == 'PHL':
                st.caption(f"Local Value: ₱{curr_val * rate:,.1f}B (API Rate: {rate})")
else:
    st.warning("Select at least one country to view metrics.")