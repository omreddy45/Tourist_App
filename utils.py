import pandas as pd
import requests
import os
import re
import streamlit as st

def load_excel_data(file_path):
    """
    Load data from Excel file

    Args:
        file_path: Path to the Excel file

    Returns:
        Pandas DataFrame or None if file doesn't exist
    """
    try:
        if os.path.exists(file_path):
            df = pd.read_excel(file_path)
            return df
        else:
            return None
    except Exception as e:
        st.error(f"Error loading Excel file: {str(e)}")
        return None

def get_weather(city, api_key):
    """
    Get current weather data for a city using OpenWeatherMap API

    Args:
        city: Name of the city
        api_key: OpenWeatherMap API key

    Returns:
        Dictionary with weather data or error message
    """
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": f"{city},in",  # Add 'in' for India to improve results
            "appid": api_key,
            "units": "metric"  # Get temperature in Celsius
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            error_info = response.json()
            return {"error": f"{error_info.get('message', 'Unknown error')} (Code: {response.status_code})"}

    except requests.exceptions.RequestException as e:
        return {"error": f"Network error: {str(e)}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}

def normalize_city_name(city_name):
    """
    Normalize city name for better matching

    Args:
        city_name: Name of the city

    Returns:
        Normalized city name
    """
    if not city_name:
        return ""

    # Convert to lowercase, remove extra spaces and special characters
    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', city_name.lower()).strip()

    # Handle common variations
    mapping = {
        "bengaluru": "bangalore",
        "bombay": "mumbai",
        "calcutta": "kolkata",
        "madras": "chennai",
        "hydrabad": "hyderabad",  # Common misspelling
        "benares": "varanasi",
        "benaras": "varanasi",
        "kashi": "varanasi",
        "mysore": "mysuru",
        "poona": "pune",
        "cochin": "kochi",
        "trivandrum": "thiruvananthapuram",
        "baroda": "vadodara",
        "simla": "shimla",
        "pondicherry": "puducherry",
    }

    return mapping.get(normalized, normalized)

def get_city_recommendations(df, city_name):
    """
    Get tourism and food recommendations for a city

    Args:
        df: DataFrame with city data
        city_name: Name of the city

    Returns:
        Dictionary with recommendations or None if city not found
    """
    if df is None or 'City' not in df.columns:
        return None

    normalized_input = normalize_city_name(city_name)

    # Normalize city names in dataframe
    df['NormalizedCity'] = df['City'].apply(normalize_city_name)

    # Find the city in the dataframe
    city_data = df[df['NormalizedCity'] == normalized_input]

    if city_data.empty:
        # Try fuzzy matching if exact match fails
        for df_city in df['NormalizedCity'].unique():
            if normalized_input in df_city or df_city in normalized_input:
                city_data = df[df['NormalizedCity'] == df_city]
                break

    if city_data.empty:
        return None

    # Extract recommendations based on the Excel structure
    recommendations = {}

    try:
        # Collect tourist places
        tourist_places = []
        for i in range(1, 4):
            spot_col = f'Tourist Spot {i}'
            if spot_col in df.columns and not pd.isna(city_data[spot_col].iloc[0]):
                spot = city_data[spot_col].iloc[0]
                if isinstance(spot, str) and spot.strip():
                    tourist_places.append(spot.strip())

        # Collect breakfast spots
        breakfast_spots = []
        for i in range(1, 4):
            spot_col = f'Breakfast Spot {i}'
            if spot_col in df.columns and not pd.isna(city_data[spot_col].iloc[0]):
                spot = city_data[spot_col].iloc[0]
                if isinstance(spot, str) and spot.strip():
                    breakfast_spots.append(spot.strip())

        # Collect dinner spots
        dinner_spots = []
        for i in range(1, 4):
            spot_col = f'Dinner Spot {i}'
            if spot_col in df.columns and not pd.isna(city_data[spot_col].iloc[0]):
                spot = city_data[spot_col].iloc[0]
                if isinstance(spot, str) and spot.strip():
                    dinner_spots.append(spot.strip())

        recommendations = {
            'tourist_places': tourist_places,
            'breakfast_spots': breakfast_spots,
            'dinner_spots': dinner_spots
        }

        return recommendations

    except Exception as e:
        st.error(f"Error extracting recommendations: {str(e)}")
        return None
def get_weather_forecast(city, api_key):
    """
    Get 5-day weather forecast for a city using OpenWeatherMap API

    Args:
        city: Name of the city
        api_key: OpenWeatherMap API key

    Returns:
        List of forecast data points or error message
    """
    try:
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            "q": f"{city},in",
            "appid": api_key,
            "units": "metric"
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            error_info = response.json()
            return {"error": f"{error_info.get('message', 'Unknown error')} (Code: {response.status_code})"}

    except requests.exceptions.RequestException as e:
        return {"error": f"Network error: {str(e)}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}
    