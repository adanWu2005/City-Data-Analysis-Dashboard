import requests
import pandas as pd
import json
import time

def get_bls_data(input_df, target_areas, bls_api_key):
    """
    Retrieve labor data from the BLS API for the target areas
    Compares data across years from start_year to end_year to identify strongest market
    """
    # Get the year range from input_df
    start_year = int(input_df['Start_Year'].iloc[0])
    end_year = int(input_df['End_Year'].iloc[0])
    
    print(f"Retrieving BLS data for years {start_year} to {end_year}")
    
    # Define area codes for BLS API
    # These are different from FIPS codes
    bls_area_codes = {}
    valid_areas = []
    
    for area_id, area_info in target_areas.items():
        # Skip if we don't have valid FIPS codes
        if area_info['fips_county'] == '000' or area_info['fips_county'] == '':
            print(f"⚠ Skipping BLS data for {area_info['city']}, {area_info['state']} - no valid FIPS code")
            continue
            
        # Construct BLS area code from FIPS codes
        location_key = f"{area_info['city']}, {area_info['state']} ({area_info['county']})"
        bls_area_codes[location_key] = f"{area_info['fips_state']}{area_info['fips_county']}"
        valid_areas.append(area_info)
    
    if not bls_area_codes:
        print("No valid areas with FIPS codes for BLS data retrieval")
        return pd.DataFrame(), None
    
    # Store data for multiple years
    all_employment_data = []
    
    # Loop through each year in the range
    for year in range(start_year, end_year + 1):
        print(f"\nRetrieving BLS data for year {year}...")
        
        # Define series IDs for the data we want
        # Format: LAUCN{area_code}0000000{data_type}
        # data_type: 03 for unemployment rate, 06 for unemployment level, 05 for employed
        series_ids = []
        series_to_location = {}  # Map series ID back to location
        
        for location_key, area_code in bls_area_codes.items():
            # Unemployment rate series
            unemp_series = f"LAUCN{area_code}0000000003"
            series_ids.append(unemp_series)
            series_to_location[unemp_series] = (location_key, 'unemployment_rate')
            
            # Employment level series
            emp_series = f"LAUCN{area_code}0000000005"
            series_ids.append(emp_series)
            series_to_location[emp_series] = (location_key, 'employed')
        
        # BLS API has a limit on series per request, so batch if needed
        batch_size = 50
        for i in range(0, len(series_ids), batch_size):
            batch_series = series_ids[i:i + batch_size]
            
            # Call BLS API
            headers = {'Content-type': 'application/json'}
            data = json.dumps({
                "seriesid": batch_series,
                "startyear": str(year),
                "endyear": str(year),
                "registrationkey": bls_api_key
            })
            
            url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
            
            try:
                response = requests.post(url, data=data, headers=headers)
                response.raise_for_status()
                
                results = response.json()
                
                if results.get('status') == 'REQUEST_SUCCEEDED':
                    # Process results into employment data
                    year_employment_data = {}
                    
                    for series in results.get('Results', {}).get('series', []):
                        series_id = series['seriesID']
                        
                        # Get location and data type from our mapping
                        if series_id in series_to_location:
                            location_key, data_type = series_to_location[series_id]
                            
                            # Get the most recent data point for this year
                            if len(series.get('data', [])) > 0:
                                value = float(series['data'][0]['value'])
                                
                                if location_key not in year_employment_data:
                                    year_employment_data[location_key] = {}
                                
                                year_employment_data[location_key][data_type] = value
                    
                    # Store data with year and location information
                    for location_key, emp_data in year_employment_data.items():
                        # Parse location key to get city, state, county
                        parts = location_key.split(' (')
                        city_state = parts[0].split(', ')
                        city = city_state[0]
                        state = city_state[1]
                        county = parts[1].rstrip(')')
                        
                        employment_record = {
                            'Year': year,
                            'City': city,
                            'State': state,
                            'County': county,
                            'unemployment_rate': emp_data.get('unemployment_rate', None),
                            'employed': emp_data.get('employed', None)
                        }
                        all_employment_data.append(employment_record)
                        
                        if emp_data.get('unemployment_rate') is not None and emp_data.get('employed') is not None:
                            print(f"  ✓ {location_key}: Unemployment Rate = {emp_data.get('unemployment_rate')}%, Employed = {emp_data.get('employed'):,.0f}")
                    
                else:
                    print(f"BLS API request failed for {year}: {results.get('message', 'Unknown error')}")
                    
            except Exception as e:
                print(f"Error retrieving BLS data for {year}: {e}")
            
            # Add delay between batches
            if i + batch_size < len(series_ids):
                time.sleep(1)
    
    # Convert to DataFrame for processing
    employment_df = pd.DataFrame(all_employment_data)
    
    # Calculate employment trends and identify strongest market
    strongest_employment_info = None
    if not employment_df.empty and len(employment_df['Year'].unique()) > 1:
        print(f"\n{'-'*50}")
        print("EMPLOYMENT TREND ANALYSIS")
        print(f"{'-'*50}")
        
        # Calculate employment growth and unemployment improvement for each location
        employment_analysis = []
        
        # Group by City, State, County to handle each location
        for (city, state, county), location_data in employment_df.groupby(['City', 'State', 'County']):
            location_data = location_data.sort_values('Year')
            location_data = location_data.dropna(subset=['employed', 'unemployment_rate'])
            
            if len(location_data) >= 2:
                # Employment data
                start_employed = location_data.iloc[0]['employed']
                end_employed = location_data.iloc[-1]['employed']
                start_yr = location_data.iloc[0]['Year']
                end_yr = location_data.iloc[-1]['Year']
                
                # Unemployment data
                start_unemployment = location_data.iloc[0]['unemployment_rate']
                end_unemployment = location_data.iloc[-1]['unemployment_rate']
                
                # Calculate metrics
                years_diff = end_yr - start_yr
                if years_diff > 0 and start_employed > 0:
                    employment_growth = ((end_employed - start_employed) / start_employed) * 100
                    employment_cagr = ((end_employed / start_employed) ** (1/years_diff) - 1) * 100
                    unemployment_change = end_unemployment - start_unemployment  # Negative is good
                    
                    # Calculate composite score (higher employment growth + lower unemployment change = better)
                    composite_score = employment_cagr - (unemployment_change * 2)  # Weight unemployment change more
                    
                    employment_analysis.append({
                        'City': city,
                        'State': state,
                        'County': county,
                        'Start_Employed': start_employed,
                        'End_Employed': end_employed,
                        'Employment_Growth_Pct': employment_growth,
                        'Employment_CAGR_Pct': employment_cagr,
                        'Start_Unemployment_Rate': start_unemployment,
                        'End_Unemployment_Rate': end_unemployment,
                        'Unemployment_Change': unemployment_change,
                        'Composite_Score': composite_score,
                        'Years_Analyzed': years_diff
                    })
                    
                    print(f"{city}, {state} ({county}):")
                    print(f"  Employment {start_yr}: {start_employed:,.0f}")
                    print(f"  Employment {end_yr}: {end_employed:,.0f}")
                    print(f"  Employment Growth: {employment_growth:+.2f}%")
                    print(f"  Employment CAGR: {employment_cagr:+.2f}%")
                    print(f"  Unemployment Rate {start_yr}: {start_unemployment:.1f}%")
                    print(f"  Unemployment Rate {end_yr}: {end_unemployment:.1f}%")
                    print(f"  Unemployment Change: {unemployment_change:+.1f}% {'(Improved)' if unemployment_change < 0 else '(Worsened)'}")
                    print(f"  Composite Score: {composite_score:.2f}")
                    print()
        
        # Create employment analysis DataFrame and identify strongest market
        if employment_analysis:
            employment_analysis_df = pd.DataFrame(employment_analysis)
            employment_analysis_df = employment_analysis_df.sort_values('Composite_Score', ascending=False)
            
            strongest_employment_market = employment_analysis_df.iloc[0]
            strongest_employment_info = {
                "city": strongest_employment_market['City'],
                "county": strongest_employment_market['County'],
                "employment_cagr": strongest_employment_market['Employment_CAGR_Pct'],
                "unemployment_change": strongest_employment_market['Unemployment_Change'],
                "composite_score": strongest_employment_market['Composite_Score']
            }
            print(f"🏆 STRONGEST EMPLOYMENT MARKET: {strongest_employment_market['City']}, {strongest_employment_market['State']}")
            print(f"   County: {strongest_employment_market['County']}")
            print(f"   Employment CAGR: {strongest_employment_market['Employment_CAGR_Pct']:+.2f}%")
            print(f"   Unemployment Change: {strongest_employment_market['Unemployment_Change']:+.1f}%")
            print(f"   Composite Score: {strongest_employment_market['Composite_Score']:.2f}")
            
            # Save employment analysis
            employment_analysis_df.to_csv("real_estate_data/work/employment_trend_analysis.csv", index=False)
    
    # Save the comprehensive employment data
    employment_df.to_csv("real_estate_data/work/employment_data_by_year.csv", index=False)
    
    # Create summary DataFrame for the most recent year for backward compatibility
    if not employment_df.empty:
        latest_year = employment_df['Year'].max()
        latest_employment = employment_df[employment_df['Year'] == latest_year][['County', 'unemployment_rate', 'employed']]
        
        # Save latest year data for compatibility with existing code
        latest_employment.to_csv("real_estate_data/work/employment_data.csv", index=False)
        
        return latest_employment, strongest_employment_info
    else:
        # Return empty DataFrame if no data was retrieved
        return pd.DataFrame(), strongest_employment_info 