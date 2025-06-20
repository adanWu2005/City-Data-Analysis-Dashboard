import pandas as pd
from datetime import datetime

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

def get_user_input():
    """
    Get user input for cities and date ranges
    """
    print("=== REAL ESTATE ANALYSIS SETUP ===")
    print("Please provide the following information:\n")
    
    # Get user input
    cities = []
    states_set = set()  # Track unique states
    
    while True:
        city = input("Enter a city name (or 'done' to finish): ").strip()
        if city.lower() == 'done':
            if len(cities) == 0:
                print("Please enter at least one city.")
                continue
            break
        if city:
            # Convert city name to proper title case
            city = convert_to_title_case(city)
            # Get state for the city
            state = input(f"Enter the state abbreviation for {city} (e.g., NY, PA, CA): ").strip().upper()
            cities.append({'city': city, 'state': state})
            states_set.add(state)  # Track unique states
    
    # Get year range with validation
    current_year = datetime.now().year
    min_year = 2009  # Earliest available Census data
    max_year = current_year - 2  # Most recent complete Census data (2 years behind)
    
    print(f"\nAvailable years for analysis: {min_year} to {max_year}")
    print("Note: Census data is typically available 2 years behind the current year")
    
    while True:
        start_year = input(f"Enter start year for data analysis ({min_year}-{max_year}): ").strip()
        if not start_year.isdigit() or len(start_year) != 4:
            print("Please enter a valid 4-digit year.")
            continue
        start_year = int(start_year)
        if start_year < min_year or start_year > max_year:
            print(f"Start year must be between {min_year} and {max_year}")
            continue
        break
    
    while True:
        end_year = input(f"Enter end year for data analysis ({start_year}-{max_year}): ").strip()
        if not end_year.isdigit() or len(end_year) != 4:
            print("Please enter a valid 4-digit year.")
            continue
        end_year = int(end_year)
        if end_year < start_year or end_year > max_year:
            print(f"End year must be between {start_year} and {max_year}")
            continue
        break
    
    # Prepare data for DataFrame
    input_data = []
    for i, city_info in enumerate(cities):
        input_data.append({
            'ID': i + 1,
            'City': city_info['city'],
            'State': city_info['state'],
            'Analysis_Date': datetime.now().strftime("%Y-%m-%d"),
            'Start_Year': start_year,
            'End_Year': end_year
        })
    
    # Create DataFrame
    input_df = pd.DataFrame(input_data)
    
    # Inform about state restrictions if multiple states detected
    if len(states_set) > 1:
        print("\nNOTE: Crime data scraping is currently configured for individual states.")
        print(f"You've entered cities from multiple states: {', '.join(sorted(states_set))}")
        print("Crime data will be scraped for each state separately.")
    
    return input_df 