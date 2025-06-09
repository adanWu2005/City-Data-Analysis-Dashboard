import requests
import pandas as pd
import time
import random
import re
from bs4 import BeautifulSoup

def parse_crime_table(crtable, city_name="Unknown"):
    """
    Parse the crime table and return a clean DataFrame
    """
    if not crtable:
        return None
    
    # Extract header row (years)
    header_row = crtable.find('thead')
    if not header_row:
        return None
    
    header_row = header_row.find('tr')
    headers = [th.get_text().strip() for th in header_row.find_all('th')]
    
    # Extract data rows
    tbody = crtable.find('tbody')
    if not tbody:
        return None
    
    rows = tbody.find_all('tr')
    crime_data = []
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 2:
            # First cell contains crime type
            crime_type_elem = cells[0].find('b')
            if not crime_type_elem:
                continue
            
            crime_type = crime_type_elem.get_text().strip()
            if crime_type == "City-Data.com crime index":
                continue  # Skip this row entirely
            
            # Extract data for each year
            row_data = {'City': city_name, 'Crime_Type': crime_type}
            
            # Process each year's data (skip first cell which is crime type)
            for i, cell in enumerate(cells[1:], 1):
                if i < len(headers):
                    year = headers[i]
                    cell_text = cell.get_text().strip()
                    if cell_text:
                        # Remove commas from the count string
                        count_match = re.match(r'([\d,]+)', cell_text)
                        count_str = count_match.group(1).replace(',', '') if count_match else '0'
                        try:
                            raw_count = int(count_str)
                        except ValueError:
                            raw_count = 0
                        # Rate per 100k (number in parentheses)
                        rate_match = re.search(r'\(([^)]+)\)', cell_text)
                        rate_per_100k = rate_match.group(1) if rate_match else ''
                        # Format as 'count (rate)' if rate exists
                        if rate_per_100k:
                            formatted = f"{raw_count:,} ({rate_per_100k})"
                        else:
                            formatted = f"{raw_count:,}"
                        row_data[f'{year}'] = formatted
                    else:
                        row_data[f'{year}'] = '0'
            
            crime_data.append(row_data)
    
    # Handle footer (Crime Index) separately
    tfoot = crtable.find('tfoot')
    if tfoot:
        footer_row = tfoot.find('tr')
        if footer_row:
            cells = footer_row.find_all('td')
            if len(cells) >= 2:
                # Only add if not already present for this city
                if not any(d['Crime_Type'] == 'Crime Index' for d in crime_data):
                    crime_index_data = {'City': city_name, 'Crime_Type': 'Crime Index'}
                    for i, cell in enumerate(cells[1:], 1):
                        if i < len(headers):
                            year = headers[i]
                            value = cell.get_text().strip()
                            crime_index_data[year] = value if value else 'Not Found'
                    crime_data.append(crime_index_data)
    
    # Create DataFrame
    df = pd.DataFrame(crime_data)
    # Only keep columns: City, Crime_Type, and year columns (e.g., 2010-2023)
    if not df.empty:
        # Find all year columns (numeric)
        year_cols = [col for col in df.columns if col.isdigit()]
        keep_cols = ['City', 'Crime_Type'] + year_cols
        df = df[[col for col in keep_cols if col in df.columns]]
        # Remove the first 'Crime Index' row (originally 'City-Data.com crime index')
        # Keep only the last 'Crime Index' row for each city
        df = df[~((df.duplicated(subset=['City', 'Crime_Type'], keep='last')) & (df['Crime_Type'] == 'Crime Index'))]
        # Replace None/missing values with 'Not Found'
        df.fillna('Not Found', inplace=True)
    return df

def get_state_crime_data(input_df):
    """
    Scrape crime data for cities from city-data.com
    Now supports any state based on user input
    """
    # Get unique states from user input
    unique_states = input_df['State'].unique()
    
    # State abbreviation to full name mapping
    state_mapping = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
        'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
        'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
        'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
        'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
        'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
        'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
        'NH': 'New-Hampshire', 'NJ': 'New-Jersey', 'NM': 'New-Mexico', 'NY': 'New-York',
        'NC': 'North-Carolina', 'ND': 'North-Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
        'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode-Island', 'SC': 'South-Carolina',
        'SD': 'South-Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
        'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West-Virginia',
        'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District-of-Columbia'
    }
    
    all_crime_data = []
    headers = {"User-Agent": "Chrome/96.0.4664.110"}
    
    for state_abbr in unique_states:
        if state_abbr not in state_mapping:
            print(f"Unknown state abbreviation: {state_abbr}. Skipping...")
            continue
            
        state_name = state_mapping[state_abbr]
        state_cities = input_df[input_df['State'] == state_abbr]['City'].tolist()
        
        if not state_cities:
            continue
            
        print(f"\nScraping crime data for {state_name} cities: {state_cities}")
        
        # Build URL dynamically based on state
        url = f"https://www.city-data.com/city/{state_name}.html"
        cityUrl = "https://www.city-data.com/city/"
        
        try:
            page = requests.get(url, headers=headers)
            page.raise_for_status()
            soup = BeautifulSoup(page.content, "html.parser")
            table = soup.find("table", {"class": "tabBlue tblsort tblsticky"})
            
            if not table:
                print(f"Could not find cities table for {state_name}")
                continue
            
            rows = table.find_all("tr", class_="rB")
            cities_data = []
            
            for i, row in enumerate(rows):
                cells = row.find_all("td")
                if len(cells) >= 3:
                    city_cell = cells[1]
                    pop_cell = cells[2]
                    
                    city_link = city_cell.find("a")
                    if city_link:
                        city_name = city_link.get_text().strip()
                        city_href = city_link.get('href', '')
                        population_text = pop_cell.get_text().strip()
                        
                        # Clean population number
                        pop_clean = re.sub(r'[,\s]', '', population_text)
                        try:
                            pop_number = int(pop_clean)
                        except ValueError:
                            pop_number = 0
                        
                        cities_data.append({
                            'city_name': city_name,
                            'population_text': population_text,
                            'population_number': pop_number,
                            'detail_url': cityUrl + city_href if city_href else '',
                            'row_index': i + 1
                        })
            
            print(f"Found {len(cities_data)} {state_name} cities on city-data.com")
            
            # Filter to only user-specified cities (exact matching)
            user_cities_lower = [city.lower() for city in state_cities]
            filtered_cities = []
            
            for city_data in cities_data:
                # Remove state suffix from city name for matching
                city_name_clean = city_data['city_name'].replace(f', {state_abbr}', '').strip().lower()
                # Only match if the city name exactly matches (ignoring case)
                if city_name_clean in user_cities_lower:
                    filtered_cities.append(city_data)
                    print(f"  Matched: {city_data['city_name']} for user input")
            
            if not filtered_cities:
                print(f"No exact matches found for user-specified {state_name} cities: {state_cities}")
                continue
            
            # Now scrape crime data for matched cities
            successful_scrapes = 0
            
            for i, city_info in enumerate(filtered_cities):
                city_name = city_info['city_name']
                detail_url = city_info['detail_url']
                
                print(f"\n[{i+1}/{len(filtered_cities)}] Scraping crime data for {city_name}")
                
                try:
                    # Add delay to be respectful
                    time.sleep(random.uniform(1, 3))
                    
                    response = requests.get(detail_url, headers=headers, timeout=15)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    crtable = soup.find("table", {"class": "table tabBlue tblsort tblsticky sortable"})
                    
                    if crtable:
                        df_crime = parse_crime_table(crtable, city_name)
                        if df_crime is not None and not df_crime.empty:
                            all_crime_data.append(df_crime)
                            successful_scrapes += 1
                            print(f"    ✓ Found {len(df_crime)} crime records")
                        else:
                            print(f"    ⚠ Crime table found but no data extracted")
                    else:
                        print(f"    ⚠ No crime table found")
                        
                except Exception as e:
                    print(f"    ✗ Error scraping {city_name}: {e}")
            
            print(f"\nCrime data scraping complete for {state_name}!")
            print(f"Successfully scraped {successful_scrapes}/{len(filtered_cities)} cities")
            
        except Exception as e:
            print(f"Error scraping {state_name} crime data: {e}")
    
    # Combine all crime data across all states
    if all_crime_data:
        combined_crime_df = pd.concat(all_crime_data, ignore_index=True)
        
        # Save crime data
        combined_crime_df.to_csv("real_estate_data/work/crime_data.csv", index=False)
        
        print(f"\nTotal crime records collected: {len(combined_crime_df)}")
        
        return combined_crime_df
    else:
        print("No crime data was successfully scraped")
        return pd.DataFrame() 