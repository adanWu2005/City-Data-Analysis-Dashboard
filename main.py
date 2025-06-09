import os
import pandas as pd
from utils.input_handler import get_user_input
from utils.area_converter import convert_input_to_target_areas
from data_collection.census_data import get_census_data
from data_collection.bls_data import get_bls_data
from data_collection.crime_data import get_state_crime_data
from analysis.data_analysis import analyze_and_visualize_data
from analysis.visualization import create_visualizations
from dotenv import load_dotenv

def main():
    """
    Main function to run the real estate market analysis
    """
    # Create necessary directories
    os.makedirs("real_estate_data/work", exist_ok=True)
    os.makedirs("real_estate_data/visualizations", exist_ok=True)
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API keys from environment variables
    census_api_key = os.getenv('CENSUS_API_KEY')
    bls_api_key = os.getenv('BLS_API_KEY')
    
    if not census_api_key or not bls_api_key:
        print("Error: Please set CENSUS_API_KEY and BLS_API_KEY environment variables")
        return
    
    # Get user input
    input_df = get_user_input()
    
    # Convert input to target areas
    target_areas, county_mapping = convert_input_to_target_areas(input_df)
    
    # Get Census data
    print("\nFetching Census data...")
    population_df, age_df = get_census_data(input_df, target_areas, census_api_key)
    
    # Get BLS data
    print("\nFetching BLS data...")
    employment_df = get_bls_data(input_df, target_areas, bls_api_key)
    
    # Get crime data
    print("\nFetching crime data...")
    crime_df = get_state_crime_data(input_df)
    
    # Analyze and visualize data
    print("\nAnalyzing and visualizing data...")
    demographic_data = analyze_and_visualize_data(population_df, age_df, employment_df, crime_df, target_areas)
    
    # Create visualizations
    print("\nCreating visualizations...")
    create_visualizations(demographic_data)
    
    print("\nAnalysis complete!")
    print("Visualizations are available in: real_estate_data/visualizations/")
    print("Analysis data is available in: real_estate_data/work/")

if __name__ == "__main__":
    main() 