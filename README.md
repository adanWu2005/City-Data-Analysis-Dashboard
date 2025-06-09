# City Data Web App

A Streamlit-powered dashboard for analyzing demographic, employment, and crime data for US cities. The app scrapes, processes, and visualizes data from public sources, providing year-by-year insights and highlighting the strongest markets for population growth, employment, and crime index decrease.

## Features
- **User-friendly Streamlit interface** for city selection and analysis
- **Dynamic scraping** of county, census, BLS, and crime data
- **Year-by-year tables** for population, age, employment, and crime statistics
- **Visualizations** including correlation heatmap and (optionally) year-by-year bar/scatter plots
- **Strongest market detection** for population growth, employment, and crime index decrease
- **Error handling** for missing or invalid cities and missing crime data

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/CityDataWebApp.git
   cd CityDataWebApp
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API keys:**
   - Create a `.env` file in the root directory with your Census and BLS API keys:
     ```env
     CENSUS_API_KEY=your_census_api_key
     BLS_API_KEY=your_bls_api_key
     ```

4. **Run the app:**
   ```bash
   streamlit run app.py
   ```

## Usage

1. **Add cities** by entering the city name and state abbreviation (e.g., `Orlando`, `FL`).
2. **Set the year range** for analysis.
3. **Add multiple cities** as needed. Use the "Remove" or "Clear All Cities" buttons to manage your list.
4. **Click "Run Analysis"** to fetch, process, and visualize the data.
5. **Review the results:**
   - Year-by-year tables for age, population, employment, and crime data
   - Correlation heatmap
   - Strongest market highlights for population, employment, and crime index decrease
   - Warnings for cities with missing crime data

## Project Structure

```
CityDataWebApp/
├── app.py                  # Streamlit app
├── requirements.txt        # Python dependencies
├── .env                    # API keys (not committed)
├── utils/
│   ├── input_handler.py
│   └── area_converter.py
├── data_collection/
│   ├── census_data.py
│   ├── bls_data.py
│   └── crime_data.py
├── analysis/
│   ├── data_analysis.py
│   └── visualization.py
├── real_estate_data/
│   ├── work/               # Output CSVs
│   └── visualizations/     # Output plots
└── README.md
```

## Notes
- The app will halt and display an error if a city/county cannot be found or scraped.
- If crime data is missing for a city, a warning will be shown below the crime data table.
- All data is fetched live from public APIs and city-data.com.

