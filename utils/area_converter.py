import requests
import time
import random
from bs4 import BeautifulSoup

def get_county_fips_code(state_fips, county_name, census_api_key):
    """
    Get county FIPS code from Census Bureau API with improved matching
    """
    try:
        # Clean county name
        original_county_name = county_name
        county_name = county_name.replace(' County', '').strip()
        
        print(f"\nDebugging county FIPS lookup:")
        print(f"Original county name: {original_county_name}")
        print(f"Cleaned county name: {county_name}")
        print(f"State FIPS: {state_fips}")
        
        # Census Bureau API endpoint for county codes
        url = f"https://api.census.gov/data/2010/dec/sf1?get=NAME&for=county:*&in=state:{state_fips}&key={census_api_key}"
        
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        headers = data[0]
        counties = data[1:]
        
        print(f"\nFound {len(counties)} counties in state")
        
        # Find matching county using more flexible matching
        for county in counties:
            name = county[0]  # County name is in first column
            # Clean the name from the API response
            clean_name = name.split(',')[0].replace(' County', '').strip()
            
            # Try exact match first
            if county_name.lower() == clean_name.lower():
                return county[2]  # County FIPS code is in third column
            
            # Try partial match if exact match fails
            if county_name.lower() in clean_name.lower() or clean_name.lower() in county_name.lower():
                return county[2]
        
        print(f"\n⚠ No match found for county: {county_name}")
        print("Available counties in state:")
        for county in counties:
            print(f"  - {county[0]}")
        
        return '000'  # Return default if not found
        
    except Exception as e:
        print(f"Error getting county FIPS code: {e}")
        return '000'

def convert_input_to_target_areas(input_df):
    """
    Convert user input DataFrame to target_areas dictionary format
    Dynamically scrapes county information from city-data.com
    Returns both target_areas dict and a mapping for county names
    """
    target_areas = {}
    county_mapping = {}
    
    # State abbreviation to full name mapping for URL construction
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
    
    # State FIPS codes
    state_fips = {
        'AL': '01', 'AK': '02', 'AZ': '04', 'AR': '05', 'CA': '06', 'CO': '08',
        'CT': '09', 'DE': '10', 'FL': '12', 'GA': '13', 'HI': '15', 'ID': '16',
        'IL': '17', 'IN': '18', 'IA': '19', 'KS': '20', 'KY': '21', 'LA': '22',
        'ME': '23', 'MD': '24', 'MA': '25', 'MI': '26', 'MN': '27', 'MS': '28',
        'MO': '29', 'MT': '30', 'NE': '31', 'NV': '32', 'NH': '33', 'NJ': '34',
        'NM': '35', 'NY': '36', 'NC': '37', 'ND': '38', 'OH': '39', 'OK': '40',
        'OR': '41', 'PA': '42', 'RI': '44', 'SC': '45', 'SD': '46', 'TN': '47',
        'TX': '48', 'UT': '49', 'VT': '50', 'VA': '51', 'WA': '53', 'WV': '54',
        'WI': '55', 'WY': '56', 'DC': '11'
    }
    
    headers = {"User-Agent": "Chrome/96.0.4664.110"}
    
    for _, row in input_df.iterrows():
        city = row['City']
        state = row['State']
        
        # Check if state is valid
        if state not in state_mapping:
            print(f"ERROR: Unknown state abbreviation: {state}")
            continue
            
        state_name = state_mapping[state]
        state_fips_code = state_fips.get(state, '00')
        
        # Create area identifier
        area_id = f"{city.lower().replace(' ', '_')}_{state.lower()}"
        
        # Construct URL for city page
        # Replace spaces with hyphens in city name for URL
        city_url_name = city.replace(' ', '-')
        url = f"https://www.city-data.com/city/{city_url_name}-{state_name}.html"
        
        print(f"\nScraping county info for {city}, {state}...")
        print(f"URL: {url}")
        
        try:
            # Add delay to be respectful
            time.sleep(random.uniform(1, 2))
            
            page = requests.get(url, headers=headers, timeout=15)
            page.raise_for_status()
            
            soup = BeautifulSoup(page.content, "html.parser")
            
            # Find the breadcrumb navigation
            breadcrumb = soup.find("ol", {"class": "breadcrumb"})
            
            if breadcrumb:
                # Get all list items
                list_items = breadcrumb.find_all("li")
                
                # The county is typically the third item (index 2)
                if len(list_items) > 2:
                    county_item = list_items[2]
                    county_link = county_item.find("a")
                    
                    if county_link:
                        county_name = county_link.get_text().strip()
                        
                        # Get county FIPS code from Census Bureau API
                        county_fips_code = get_county_fips_code(state_fips_code, county_name, "856e29b65185c3bc832572b45af9ff5e93758ce6")
                        
                        print(f"✓ Found: {city}, {state} → {county_name} (FIPS: {state_fips_code}-{county_fips_code})")
                        
                        target_areas[area_id] = {
                            "state": state,
                            "county": county_name,
                            "fips_state": state_fips_code,
                            "fips_county": county_fips_code,
                            "city": city
                        }
                        
                        # Create mapping for later use
                        county_mapping[county_name] = city
                    else:
                        print(f"✗ Could not find county link for {city}, {state}")
                        raise ValueError(f"Could not find county info for {city}, {state}")
                else:
                    print(f"✗ Breadcrumb structure unexpected for {city}, {state}")
                    raise ValueError(f"Could not find county info for {city}, {state}")
            else:
                print(f"✗ Could not find breadcrumb navigation for {city}, {state}")
                raise ValueError(f"Could not find county info for {city}, {state}")
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"✗ City page not found: {city}, {state}")
                print(f"  Try different spelling or check if city name is correct")
                raise ValueError(f"City not found: {city}, {state}")
            else:
                print(f"✗ HTTP Error for {city}, {state}: {e}")
                raise ValueError(f"HTTP Error for {city}, {state}: {e}")
        except Exception as e:
            print(f"✗ Error scraping {city}, {state}: {e}")
            raise ValueError(f"Error scraping {city}, {state}: {e}")
    
    if not target_areas:
        print("\nERROR: No valid cities found or scraped.")
        print("Please check city names and spellings.")
        raise ValueError("No valid cities could be processed")
    
    print(f"\nSuccessfully processed {len(target_areas)} cities")
    
    return target_areas, county_mapping 