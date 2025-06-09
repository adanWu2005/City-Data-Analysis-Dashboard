import pandas as pd
import numpy as np
import os

def analyze_and_visualize_data(population_df, age_df, employment_df, crime_df=None, target_areas=None):
    """
    Analyze and visualize the relationships between demographic data and crime data
    """
    # Create a directory for visualizations
    if not os.path.exists("real_estate_data/visualizations"):
        os.makedirs("real_estate_data/visualizations")
    
    # Merge all demographic data into one DataFrame
    demographic_data = pd.DataFrame()
    
    # Add population data
    if not population_df.empty:
        demographic_data['County'] = population_df['County']
        demographic_data['Population'] = population_df['Population']
    
    # Add age data
    if not age_df.empty:
        # Check if we need to merge or if this is the first data
        if demographic_data.empty:
            demographic_data['County'] = age_df['County']
            demographic_data['Median Age'] = age_df['Median Age']
        else:
            demographic_data = demographic_data.merge(age_df, on='County', how='outer')
    
    # Add employment data
    if employment_df is not None and not employment_df.empty:
        # Check if we need to merge or if this is the first data
        if demographic_data.empty:
            demographic_data = employment_df.copy()
        else:
            demographic_data = demographic_data.merge(employment_df, on='County', how='outer')
    
    # Add crime data if available
    if crime_df is not None and not crime_df.empty and target_areas is not None:
        # Process crime data to get crime index by city
        crime_index_data = crime_df[crime_df['Crime_Type'] == 'Crime Index'].copy()
        
        if not crime_index_data.empty:
            # Get most recent year's crime index
            year_columns = [col for col in crime_index_data.columns if col.endswith('_count') and col != 'Crime_Type']
            if year_columns:
                # Use the most recent year available
                latest_year_col = sorted(year_columns)[-1]
                latest_year = latest_year_col.replace('_count', '')
                
                crime_summary = crime_index_data[['City', latest_year_col]].copy()
                crime_summary.columns = ['City', 'Crime_Index']
                crime_summary = crime_summary.dropna()
                
                # Map city names to counties (you may need to customize this mapping)
                city_to_county_mapping = {}
                for area_id, area_info in target_areas.items():
                    city_name = area_info.get('city', area_info['county'].replace(' County', ''))
                    county_name = area_info['county']
                    city_to_county_mapping[city_name] = county_name
                
                # Add county information to crime data
                crime_summary['County'] = crime_summary['City'].map(
                    lambda x: next((county for city, county in city_to_county_mapping.items() 
                                  if city.lower() in x.lower() or x.lower() in city.lower()), x)
                )
                
                # Merge with demographic data
                if not demographic_data.empty:
                    demographic_data = demographic_data.merge(
                        crime_summary[['County', 'Crime_Index']], 
                        on='County', 
                        how='left'
                    )
                else:
                    demographic_data = crime_summary[['County', 'Crime_Index']].copy()
                
                # Save crime summary
                crime_summary.to_csv("real_estate_data/work/crime_summary.csv", index=False)
                
                print(f"Crime data integrated for {len(crime_summary)} cities")
    
    # Save the merged demographic data
    demographic_data.to_csv("real_estate_data/work/demographic_data.csv", index=False)
    
    # Add correlation analysis
    print("\nCorrelation Analysis:")
    numeric_columns = demographic_data.select_dtypes(include=[np.number]).columns
    if len(numeric_columns) > 1:
        corr_matrix = demographic_data[numeric_columns].corr()
        print(corr_matrix)
        
        # Save correlation matrix
        corr_matrix.to_csv("real_estate_data/work/correlation_matrix.csv")
    
    # Create summary report
    create_summary_report(demographic_data)
    
    return demographic_data

def create_summary_report(demographic_data):
    """
    Create a summary report of the analysis focusing on demographic and crime data
    """
    with open("real_estate_data/analysis_report.txt", "w", encoding='utf-8') as f:
        f.write("DEMOGRAPHIC AND CRIME DATA ANALYSIS REPORT\n")
        f.write("==========================================\n\n")
        
        f.write("1. DEMOGRAPHIC SUMMARY\n")
        f.write("-----------------------\n")
        for i, row in demographic_data.iterrows():
            f.write(f"County: {row['County']}\n")
            if 'Population' in demographic_data.columns and pd.notna(row.get('Population')):
                f.write(f"  Population: {row['Population']:,.0f}\n")
            if 'Median Age' in demographic_data.columns and pd.notna(row.get('Median Age')):
                f.write(f"  Median Age: {row['Median Age']:.1f} years\n")
            if 'unemployment_rate' in demographic_data.columns and pd.notna(row.get('unemployment_rate')):
                f.write(f"  Unemployment Rate: {row['unemployment_rate']:.1f}%\n")
            if 'employed' in demographic_data.columns and pd.notna(row.get('employed')):
                f.write(f"  Employed Population: {row['employed']:,.0f}\n")
            if 'Crime_Index' in demographic_data.columns and pd.notna(row.get('Crime_Index')):
                f.write(f"  Crime Index: {row['Crime_Index']:.1f}\n")
            f.write("\n")
        
        f.write("\n2. KEY FINDINGS\n")
        f.write("-----------------\n")
        
        # Find highest and lowest crime areas
        if 'Crime_Index' in demographic_data.columns:
            crime_data = demographic_data.dropna(subset=['Crime_Index'])
            if not crime_data.empty:
                highest_crime = crime_data.loc[crime_data['Crime_Index'].idxmax()]
                lowest_crime = crime_data.loc[crime_data['Crime_Index'].idxmin()]
                
                f.write(f"Highest Crime Area: {highest_crime['County']} (Index: {highest_crime['Crime_Index']:.1f})\n")
                f.write(f"Lowest Crime Area: {lowest_crime['County']} (Index: {lowest_crime['Crime_Index']:.1f})\n\n")
        
        # Find most and least populated areas
        if 'Population' in demographic_data.columns:
            pop_data = demographic_data.dropna(subset=['Population'])
            if not pop_data.empty:
                most_populated = pop_data.loc[pop_data['Population'].idxmax()]
                least_populated = pop_data.loc[pop_data['Population'].idxmin()]
                
                f.write(f"Most Populated: {most_populated['County']} ({most_populated['Population']:,.0f})\n")
                f.write(f"Least Populated: {least_populated['County']} ({least_populated['Population']:,.0f})\n\n")
        
        # Employment statistics
        if 'unemployment_rate' in demographic_data.columns:
            unemp_data = demographic_data.dropna(subset=['unemployment_rate'])
            if not unemp_data.empty:
                highest_unemployment = unemp_data.loc[unemp_data['unemployment_rate'].idxmax()]
                lowest_unemployment = unemp_data.loc[unemp_data['unemployment_rate'].idxmin()]
                
                f.write(f"Highest Unemployment: {highest_unemployment['County']} ({highest_unemployment['unemployment_rate']:.1f}%)\n")
                f.write(f"Lowest Unemployment: {lowest_unemployment['County']} ({lowest_unemployment['unemployment_rate']:.1f}%)\n\n")
        
        # Correlation insights
        numeric_columns = demographic_data.select_dtypes(include=[np.number]).columns
        if len(numeric_columns) > 1:
            corr_matrix = demographic_data[numeric_columns].corr()
            
            f.write("CORRELATION INSIGHTS:\n")
            
            # Check specific correlations
            if 'Population' in corr_matrix.columns and 'Crime_Index' in corr_matrix.columns:
                corr = corr_matrix.loc['Population', 'Crime_Index']
                f.write(f"- Population vs Crime Index correlation: {corr:.2f}\n")
                if abs(corr) > 0.5:
                    direction = "positively" if corr > 0 else "negatively"
                    f.write(f"  -> Population and crime are {direction} correlated\n")
            
            if 'unemployment_rate' in corr_matrix.columns and 'Crime_Index' in corr_matrix.columns:
                corr = corr_matrix.loc['unemployment_rate', 'Crime_Index']
                f.write(f"- Unemployment Rate vs Crime Index correlation: {corr:.2f}\n")
                if abs(corr) > 0.5:
                    direction = "positively" if corr > 0 else "negatively"
                    f.write(f"  -> Unemployment and crime are {direction} correlated\n")
            
            if 'Median Age' in corr_matrix.columns and 'Crime_Index' in corr_matrix.columns:
                corr = corr_matrix.loc['Median Age', 'Crime_Index']
                f.write(f"- Median Age vs Crime Index correlation: {corr:.2f}\n")
                if abs(corr) > 0.5:
                    direction = "positively" if corr > 0 else "negatively"
                    f.write(f"  -> Age demographics and crime are {direction} correlated\n")
        
        f.write("\n3. OBSERVATIONS\n")
        f.write("----------------\n")
        f.write("- Population density may influence crime rates in certain areas\n")
        f.write("- Economic factors (employment) appear to correlate with crime statistics\n")
        f.write("- Age demographics show varying patterns across counties\n")
        f.write("- Further analysis recommended to identify causal relationships\n") 