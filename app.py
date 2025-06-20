import streamlit as st
import pandas as pd
import os
from datetime import datetime
from utils.area_converter import convert_input_to_target_areas
from data_collection.census_data import get_census_data
from data_collection.bls_data import get_bls_data
from data_collection.crime_data import get_state_crime_data
from analysis.data_analysis import analyze_and_visualize_data
from analysis.visualization import create_visualizations
from dotenv import load_dotenv

def convert_to_title_case(city_name):
    """
    Convert city name to proper title case.
    e.g., "st. augustine" -> "St. Augustine"
    """
    if not isinstance(city_name, str) or not city_name:
        return city_name
    
    # Split the city name into words and process each one
    words = city_name.strip().split()
    processed_words = [word.capitalize() for word in words]
    
    return ' '.join(processed_words)

def create_input_dataframe(cities_data):
    """Convert cities data to DataFrame format"""
    input_data = []
    for i, city_info in enumerate(cities_data):
        input_data.append({
            'ID': i + 1,
            'City': city_info['city'],
            'State': city_info['state'],
            'Analysis_Date': datetime.now().strftime("%Y-%m-%d"),
            'Start_Year': city_info['start_year'],
            'End_Year': city_info['end_year']
        })
    return pd.DataFrame(input_data)

def prettify_columns(df):
    df = df.copy()
    df.columns = [col.replace('_', ' ').title() for col in df.columns]
    return df

def main():
    st.set_page_config(page_title="City Data Analysis", layout="wide")
    
    st.title("City Data Analysis Dashboard")
    st.write("Analyze demographic, employment, and crime data for multiple cities.")
    
    # Create necessary directories
    os.makedirs("real_estate_data/work", exist_ok=True)
    os.makedirs("real_estate_data/visualizations", exist_ok=True)
    
    # Load environment variables
    load_dotenv()
    
    # Get API keys
    census_api_key = os.getenv('CENSUS_API_KEY')
    bls_api_key = os.getenv('BLS_API_KEY')
    
    if not census_api_key or not bls_api_key:
        st.error("Please set CENSUS_API_KEY and BLS_API_KEY environment variables")
        return
    
    # Input section
    st.header("Input Parameters")
    
    # Year range selection
    current_year = datetime.now().year
    min_year = 2009
    max_year = current_year - 2
    
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.number_input(
            "Start Year",
            min_value=min_year,
            max_value=max_year,
            value=min_year,
            help=f"Available years: {min_year} to {max_year}"
        )
    with col2:
        end_year = st.number_input(
            "End Year",
            min_value=start_year,
            max_value=max_year,
            value=max_year,
            help=f"Must be between {start_year} and {max_year}"
        )
    
    # City input section
    st.subheader("Add Cities")
    
    cities_data = []
    if 'cities' not in st.session_state:
        st.session_state.cities = []
    
    col1, col2 = st.columns(2)
    with col1:
        new_city = st.text_input("City Name")
    with col2:
        new_state = st.text_input("State Abbreviation (e.g., NY, CA)").upper()
    
    if st.button("Add City"):
        if new_city and new_state:
            # Convert city name to proper title case
            new_city = convert_to_title_case(new_city)
            st.session_state.cities.append({
                'city': new_city,
                'state': new_state,
                'start_year': start_year,
                'end_year': end_year
            })
            st.success(f"Added {new_city}, {new_state}")
        else:
            st.warning("Please enter both city name and state")
    
    # Display current cities
    if st.session_state.cities:
        st.subheader("Selected Cities")
        remove_index = None
        for i, city in enumerate(st.session_state.cities):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"{city['city']}, {city['state']}")
            with col2:
                if st.button("Remove", key=f"remove_{i}"):
                    remove_index = i
        if remove_index is not None:
            st.session_state.cities.pop(remove_index)
            st.rerun()
        # Add Clear All button
        if st.button("Clear All Cities"):
            st.session_state.cities.clear()
            st.rerun()
    
    # Analysis button
    if st.button("Run Analysis", disabled=len(st.session_state.cities) == 0):
        if len(st.session_state.cities) == 0:
            st.warning("Please add at least one city")
            return
        
        # Create progress bar 
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Convert input to DataFrame
        input_df = create_input_dataframe(st.session_state.cities)
        
        # Convert input to target areas
        try:
            target_areas, county_mapping = convert_input_to_target_areas(input_df)
        except ValueError as e:
            st.error(str(e))
            return
        progress_bar.progress(20)
        
        # Get Census data
        status_text.text("Fetching Census data...")
        population_df, age_df, strongest_market_info = get_census_data(input_df, target_areas, census_api_key)
        progress_bar.progress(40)
        
        # Get BLS data
        status_text.text("Fetching BLS data...")
        employment_df, strongest_employment_info = get_bls_data(input_df, target_areas, bls_api_key)
        progress_bar.progress(60)
        
        # Get crime data
        status_text.text("Fetching crime data...")
        crime_df = get_state_crime_data(input_df)
        progress_bar.progress(80)
        
        # Analyze and visualize data
        status_text.text("Analyzing and visualizing data...")
        demographic_data = analyze_and_visualize_data(population_df, age_df, employment_df, crime_df, target_areas)
        create_visualizations(demographic_data)
        progress_bar.progress(100)
        
        # Display results
        st.header("Analysis Results")
        st.info("Population and Median Age are from the county (Census Bureau). Crime Index is from the city (City-Data.com). All tables below are year-by-year.")

        # Age Data Table (year-by-year)
        st.subheader("Age Data (Year-by-Year)")
        age_path = "real_estate_data/work/age_data_by_year.csv"
        if os.path.exists(age_path):
            age_year_df = pd.read_csv(age_path)
            age_year_df = prettify_columns(age_year_df)
            age_year_df.index = age_year_df.index + 1
            st.dataframe(age_year_df)
        else:
            st.write("No age data available.")

        # Population Data Table (year-by-year)
        st.subheader("Population Data (Year-by-Year)")
        population_path = "real_estate_data/work/population_data_by_year.csv"
        if os.path.exists(population_path):
            population_year_df = pd.read_csv(population_path)
            population_year_df = prettify_columns(population_year_df)
            population_year_df.index = population_year_df.index + 1
            st.dataframe(population_year_df)
        else:
            st.write("No population data available.")

        # Employment Data Table (year-by-year)
        st.subheader("Employment Data (Year-by-Year)")
        employment_path = "real_estate_data/work/employment_data_by_year.csv"
        if os.path.exists(employment_path):
            employment_year_df = pd.read_csv(employment_path)
            employment_year_df = prettify_columns(employment_year_df)
            employment_year_df.index = employment_year_df.index + 1
            st.dataframe(employment_year_df)
        else:
            st.write("No employment data available.")

        # Crime Data Table (Year-by-Year)
        st.subheader("Crime Data (Year-by-Year)")
        crime_path = "real_estate_data/work/crime_data.csv"
        strongest_crime_info = None
        missing_crime_cities = []
        if os.path.exists(crime_path):
            crime_year_df = pd.read_csv(crime_path)
            crime_year_df = prettify_columns(crime_year_df)
            # Filter year columns based on user input
            if st.session_state.cities:
                start_year = st.session_state.cities[0]['start_year']
                end_year = st.session_state.cities[0]['end_year']
                year_cols = [str(y) for y in range(start_year, end_year + 1)]
                year_cols = [y for y in year_cols if y in crime_year_df.columns]
                keep_cols = ['City', 'Crime Type'] + year_cols
                crime_year_df = crime_year_df[[col for col in keep_cols if col in crime_year_df.columns]]
                # Find strongest market by crime index decrease
                crime_index_rows = crime_year_df[crime_year_df['Crime Type'] == 'Crime Index']
                best_city = None
                best_county = None
                max_decrease = None
                best_start_val = None
                best_end_val = None
                best_start_year = None
                best_end_year = None
                for idx, row in crime_index_rows.iterrows():
                    try:
                        start_val = float(row[year_cols[0]]) if row[year_cols[0]] != 'Not Found' else None
                        end_val = float(row[year_cols[-1]]) if row[year_cols[-1]] != 'Not Found' else None
                        if start_val is not None and end_val is not None:
                            decrease = start_val - end_val
                            if (max_decrease is None) or (decrease > max_decrease):
                                max_decrease = decrease
                                best_city = row['City']
                                best_county = row['City']  # If you have county info, replace with row['County']
                                best_start_val = start_val
                                best_end_val = end_val
                                best_start_year = year_cols[0]
                                best_end_year = year_cols[-1]
                    except Exception:
                        continue
                if best_city is not None and max_decrease is not None:
                    strongest_crime_info = {
                        'city': best_city,
                        'decrease': max_decrease,
                        'start_val': best_start_val,
                        'end_val': best_end_val,
                        'start_year': best_start_year,
                        'end_year': best_end_year
                    }
                user_cities = set(f"{c['city']}, {c['state']}" for c in st.session_state.cities)
                crime_cities = set(crime_year_df['City'].unique())
                missing_crime_cities = [city for city in user_cities if city not in crime_cities]
            crime_year_df.index = crime_year_df.index + 1
            st.dataframe(crime_year_df)
        else:
            st.write("No crime data available.")
        # Show missing crime data cities
        if missing_crime_cities:
            st.warning("The following cities do not have crime data: " + ", ".join(missing_crime_cities))

        # Display correlation heatmap
        st.subheader("Correlation Heatmap")
        viz_dir = "real_estate_data/visualizations"
        heatmap_file = os.path.join(viz_dir, 'correlation_heatmap.png')
        if os.path.exists(heatmap_file):
            st.image(heatmap_file, caption='Correlation Heatmap')
        else:
            st.write("No correlation heatmap available.")
        
        # Display strongest market info
        if strongest_market_info:
            st.markdown(
                f"<h3>🏆 Strongest Market (by population growth): {strongest_market_info['city']} ({strongest_market_info['county']})<br>"
                f"CAGR: {strongest_market_info['cagr']:.2f}%<br>"
                f"Total Growth: {strongest_market_info['total_growth']:.2f}%</h3>", unsafe_allow_html=True
            )
        if strongest_employment_info:
            st.markdown(
                f"<h3>🏆 Strongest Employment Market: {strongest_employment_info['city']} ({strongest_employment_info['county']})<br>"
                f"Employment CAGR: {strongest_employment_info['employment_cagr']:.2f}%<br>"
                f"Unemployment Change: {strongest_employment_info['unemployment_change']:.2f}%<br>"
                f"Composite Score: {strongest_employment_info['composite_score']:.2f}</h3>", unsafe_allow_html=True
            )
        if strongest_crime_info:
            st.markdown(    
                f"<h3>🏆 Strongest Market (by crime index decrease): {strongest_crime_info['city']}<br>"
                f"Crime Index {strongest_crime_info['start_year']}: {strongest_crime_info['start_val']}<br>"
                f"Crime Index {strongest_crime_info['end_year']}: {strongest_crime_info['end_val']}<br>"
                f"Decrease: {strongest_crime_info['decrease']:.2f}</h3>", unsafe_allow_html=True
            )
        
        status_text.text("Analysis complete!")
        st.success("Analysis completed successfully!")

if __name__ == "__main__":
    main() 