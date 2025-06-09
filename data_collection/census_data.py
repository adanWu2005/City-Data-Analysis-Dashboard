import requests
import pandas as pd

def get_census_data(input_df, target_areas, census_api_key):
    """
    Retrieve population and age data from the Census API for the target areas
    Compares data across years from start_year to end_year to identify strongest market
    """
    # Get the year range from input_df
    start_year = int(input_df['Start_Year'].iloc[0])
    end_year = int(input_df['End_Year'].iloc[0])
    
    print(f"Retrieving Census data for years {start_year} to {end_year}")
    
    # Store data for multiple years
    all_population_data = []
    all_age_data = []
    
    # Define the variables we want to retrieve
    # B01003_001E: Total population
    # B01002_001E: Median age
    variables = "B01003_001E,B01002_001E"
    
    # Loop through each year in the range
    for year in range(start_year, end_year + 1):
        print(f"\nRetrieving data for year {year}...")
        
        # Check if ACS 5-year estimates are available for this year
        # ACS 5-year estimates are typically available from 2009 onwards
        if year < 2009:
            print(f"ACS 5-year estimates not available for {year}, skipping...")
            continue
        
        year_population_data = {}
        year_age_data = {}
        
        for area_id, area_info in target_areas.items():
            # Skip if we don't have valid FIPS codes
            if area_info['fips_county'] == '000' or area_info['fips_county'] == '':
                print(f"  ⚠ Skipping {area_info['city']}, {area_info['state']} - no valid FIPS code")
                continue
                
            # Create the API URL with dynamic year
            url = f"https://api.census.gov/data/{year}/acs/acs5?get={variables}&for=county:{area_info['fips_county']}&in=state:{area_info['fips_state']}&key={census_api_key}"
            
            try:
                response = requests.get(url)
                response.raise_for_status()  # Raise exception for HTTP errors
                
                data = response.json()
                # The first row contains the column headers
                headers = data[0]
                # The second row contains the actual data
                values = data[1]
                
                # Create a dictionary from headers and values
                area_data = dict(zip(headers, values))
                
                population = int(area_data['B01003_001E'])
                median_age = float(area_data['B01002_001E'])
                
                # Use city name with county for clarity
                location_name = f"{area_info['city']}, {area_info['state']} ({area_info['county']})"
                
                year_population_data[location_name] = population
                year_age_data[location_name] = median_age
                
                # Store data with year and location information
                all_population_data.append({
                    'Year': year,
                    'City': area_info['city'],
                    'State': area_info['state'],
                    'County': area_info['county'],
                    'Population': population
                })
                
                all_age_data.append({
                    'Year': year,
                    'City': area_info['city'],
                    'State': area_info['state'],
                    'County': area_info['county'],
                    'Median_Age': median_age
                })
                
                print(f"  ✓ {location_name}: Population = {population:,}, Median Age = {median_age}")
                
            except Exception as e:
                print(f"  ✗ Error retrieving Census data for {area_info['city']}, {area_info['state']} in {year}: {e}")
                # Add placeholder data to maintain structure
                all_population_data.append({
                    'Year': year,
                    'City': area_info['city'],
                    'State': area_info['state'],
                    'County': area_info['county'],
                    'Population': None
                })
                all_age_data.append({
                    'Year': year,
                    'City': area_info['city'],
                    'State': area_info['state'],
                    'County': area_info['county'],
                    'Median_Age': None
                })
    
    # Create comprehensive DataFrames
    population_df = pd.DataFrame(all_population_data)
    age_df = pd.DataFrame(all_age_data)
    
    # Calculate population growth rates and identify strongest market
    strongest_market_info = None
    if not population_df.empty and len(population_df['Year'].unique()) > 1:
        print(f"\n{'-'*50}")
        print("POPULATION GROWTH ANALYSIS")
        print(f"{'-'*50}")
        
        # Calculate growth rates for each location
        growth_analysis = []
        
        # Group by City, State, County to handle each location
        for (city, state, county), location_data in population_df.groupby(['City', 'State', 'County']):
            location_data = location_data.sort_values('Year')
            location_data = location_data.dropna(subset=['Population'])
            
            if len(location_data) >= 2:
                start_pop = location_data.iloc[0]['Population']
                end_pop = location_data.iloc[-1]['Population']
                start_yr = location_data.iloc[0]['Year']
                end_yr = location_data.iloc[-1]['Year']
                
                # Calculate compound annual growth rate (CAGR)
                years_diff = end_yr - start_yr
                if years_diff > 0 and start_pop > 0:
                    cagr = ((end_pop / start_pop) ** (1/years_diff) - 1) * 100
                    total_growth = ((end_pop - start_pop) / start_pop) * 100
                    
                    growth_analysis.append({
                        'City': city,
                        'State': state,
                        'County': county,
                        'Start_Population': start_pop,
                        'End_Population': end_pop,
                        'Total_Growth_Pct': total_growth,
                        'CAGR_Pct': cagr,
                        'Years_Analyzed': years_diff
                    })
                    
                    print(f"{city}, {state} ({county}):")
                    print(f"  Population {start_yr}: {start_pop:,}")
                    print(f"  Population {end_yr}: {end_pop:,}")
                    print(f"  Total Growth: {total_growth:+.2f}%")
                    print(f"  CAGR: {cagr:+.2f}%")
                    print()
        
        # Create growth analysis DataFrame and identify strongest market
        if growth_analysis:
            growth_df = pd.DataFrame(growth_analysis)
            growth_df = growth_df.sort_values('CAGR_Pct', ascending=False)
            
            strongest_market = growth_df.iloc[0]
            strongest_market_info = {
                "city": strongest_market['City'],
                "county": strongest_market['County'],
                "cagr": strongest_market['CAGR_Pct'],
                "total_growth": strongest_market['Total_Growth_Pct']
            }
            print(f"🏆 STRONGEST MARKET (by population growth): {strongest_market['City']}, {strongest_market['State']}")
            print(f"   County: {strongest_market['County']}")
            print(f"   CAGR: {strongest_market['CAGR_Pct']:+.2f}%")
            print(f"   Total Growth: {strongest_market['Total_Growth_Pct']:+.2f}%")
            
            # Save growth analysis
            growth_df.to_csv("real_estate_data/work/population_growth_analysis.csv", index=False)
    
    # Save the comprehensive data
    population_df.to_csv("real_estate_data/work/population_data_by_year.csv", index=False)
    age_df.to_csv("real_estate_data/work/age_data_by_year.csv", index=False)
    
    # Also create summary DataFrames for the most recent year for backward compatibility
    if not population_df.empty:
        latest_year = population_df['Year'].max()
        latest_population = population_df[population_df['Year'] == latest_year][['County', 'Population']]
        latest_age = age_df[age_df['Year'] == latest_year][['County', 'Median_Age']]
        latest_age.columns = ['County', 'Median Age']  # Rename for compatibility
        
        # Save latest year data for compatibility with existing code
        latest_population.to_csv("real_estate_data/work/population_data.csv", index=False)
        latest_age.to_csv("real_estate_data/work/age_data.csv", index=False)
        
        return latest_population, latest_age, strongest_market_info
    else:
        # Return empty DataFrames if no data was retrieved
        empty_pop_df = pd.DataFrame(columns=['County', 'Population'])
        empty_age_df = pd.DataFrame(columns=['County', 'Median Age'])
        return empty_pop_df, empty_age_df, strongest_market_info

def prettify_columns(df):
    df = df.copy()
    df.columns = [col.replace('_', ' ').title() for col in df.columns]
    return df 