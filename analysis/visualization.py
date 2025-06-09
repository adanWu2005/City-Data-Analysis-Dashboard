import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def create_visualizations(demographic_data):
    """
    Create various visualizations from the demographic data, year by year for bar and scatter plots.
    """
    # Set style
    sns.set_style('whitegrid')
    
    # Create visualizations directory if it doesn't exist
    viz_dir = "real_estate_data/visualizations"
    if not os.path.exists(viz_dir):
        os.makedirs(viz_dir)

    # Identify year column if present
    year_col = None
    for col in demographic_data.columns:
        if col.lower() == 'year':
            year_col = col
            break
    
    years = demographic_data[year_col].unique() if year_col else [None]
    
    for year in years:
        if year_col:
            data = demographic_data[demographic_data[year_col] == year]
        else:
            data = demographic_data
        year_str = f"_{year}" if year is not None else ""

        # 1. Population Distribution
        if 'Population' in data.columns:
            plt.figure(figsize=(12, 6))
            sns.barplot(data=data, x='County', y='Population')
            plt.xticks(rotation=45, ha='right')
            plt.title(f'Population Distribution by County{year_str.replace("_", " ")}')
            plt.tight_layout()
            plt.savefig(os.path.join(viz_dir, f'population_distribution{year_str}.png'))
            plt.close()
        
        # 2. Age Distribution
        if 'Median Age' in data.columns:
            plt.figure(figsize=(12, 6))
            sns.barplot(data=data, x='County', y='Median Age')
            plt.xticks(rotation=45, ha='right')
            plt.title(f'Median Age by County{year_str.replace("_", " ")}')
            plt.tight_layout()
            plt.savefig(os.path.join(viz_dir, f'age_distribution{year_str}.png'))
            plt.close()
        
        # 3. Unemployment Rate
        if 'unemployment_rate' in data.columns:
            plt.figure(figsize=(12, 6))
            sns.barplot(data=data, x='County', y='unemployment_rate')
            plt.xticks(rotation=45, ha='right')
            plt.title(f'Unemployment Rate by County{year_str.replace("_", " ")}')
            plt.tight_layout()
            plt.savefig(os.path.join(viz_dir, f'unemployment_rate{year_str}.png'))
            plt.close()
        
        # 4. Crime Index
        if 'Crime_Index' in data.columns:
            plt.figure(figsize=(12, 6))
            sns.barplot(data=data, x='County', y='Crime_Index')
            plt.xticks(rotation=45, ha='right')
            plt.title(f'Crime Index by County{year_str.replace("_", " ")}')
            plt.tight_layout()
            plt.savefig(os.path.join(viz_dir, f'crime_index{year_str}.png'))
            plt.close()
        
        # 6. Scatter Plots
        numeric_columns = data.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_columns) > 1:
            # Population vs Crime Index
            if 'Population' in data.columns and 'Crime_Index' in data.columns:
                plt.figure(figsize=(10, 6))
                sns.scatterplot(data=data, x='Population', y='Crime_Index')
                plt.title(f'Population vs Crime Index{year_str.replace("_", " ")}')
                plt.tight_layout()
                plt.savefig(os.path.join(viz_dir, f'population_vs_crime{year_str}.png'))
                plt.close()
            
            # Unemployment vs Crime Index
            if 'unemployment_rate' in data.columns and 'Crime_Index' in data.columns:
                plt.figure(figsize=(10, 6))
                sns.scatterplot(data=data, x='unemployment_rate', y='Crime_Index')
                plt.title(f'Unemployment Rate vs Crime Index{year_str.replace("_", " ")}')
                plt.tight_layout()
                plt.savefig(os.path.join(viz_dir, f'unemployment_vs_crime{year_str}.png'))
                plt.close()
            
            # Age vs Crime Index
            if 'Median Age' in data.columns and 'Crime_Index' in data.columns:
                plt.figure(figsize=(10, 6))
                sns.scatterplot(data=data, x='Median Age', y='Crime_Index')
                plt.title(f'Median Age vs Crime Index{year_str.replace("_", " ")}')
                plt.tight_layout()
                plt.savefig(os.path.join(viz_dir, f'age_vs_crime{year_str}.png'))
                plt.close()

    # 5. Correlation Heatmap (single, not year-by-year)
    numeric_columns = demographic_data.select_dtypes(include=['float64', 'int64']).columns
    if len(numeric_columns) > 1:
        plt.figure(figsize=(10, 8))
        corr_matrix = demographic_data[numeric_columns].corr()
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
        plt.title('Correlation Heatmap')
        plt.tight_layout()
        plt.savefig(os.path.join(viz_dir, 'correlation_heatmap.png'))
        plt.close()

    print(f"Visualizations have been saved to {viz_dir}/") 