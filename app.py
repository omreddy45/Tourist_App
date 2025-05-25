import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime
import plotly.graph_objects as go
import wikipedia
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from utils import load_excel_data, get_weather, get_weather_forecast, get_city_recommendations

# Page Config
st.set_page_config(
    page_title="Indian Cities Explorer",
    page_icon="🇮🇳",
    layout="wide"
)

# Constants
WEATHER_API_KEY = "29ef3caba42f0b316a50b79b38d13023"
EXCEL_FILE_PATH = "attached_assets/India_Top_Cities_Tourism_and_Food.xlsx"
PLACES_CSV_PATH = "attached_assets/address1.csv"

# Title
st.title("🇮🇳 Indian Cities Explorer")
st.subheader("Discover weather, tourist spots, and food recommendations")

# Load Excel data
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.cities_data = None

try:
    if not st.session_state.data_loaded:
        df = load_excel_data(EXCEL_FILE_PATH)
        if df is not None:
            st.session_state.cities_data = df
            st.session_state.data_loaded = True
            st.session_state.cities_list = df['City'].unique().tolist() if 'City' in df.columns else []
except Exception as e:
    st.warning("Tourism and food data couldn't be loaded. Only weather information will be available.")
    st.session_state.data_loaded = False
    st.session_state.cities_list = []

# City input
city_input = st.text_input("Enter an Indian city:", placeholder="e.g., Mumbai, Delhi, Bangalore...")

geolocator = Nominatim(user_agent="city_explorer")

if city_input:
    location = geolocator.geocode(city_input)

    if location:
        city_latitude = location.latitude
        city_longitude = location.longitude
        st.write(f"Showing map for {city_input} at latitude: {city_latitude}, longitude: {city_longitude}")

        # Weather
        with st.spinner("Fetching weather data..."):
            weather_data = get_weather(city_input, WEATHER_API_KEY)

        if weather_data and 'error' not in weather_data:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"### {weather_data['name']}, {weather_data.get('sys', {}).get('country', '')}")
                st.markdown(f"**Temperature:** {weather_data['main']['temp']:.1f}°C")
                st.markdown(f"**Feels like:** {weather_data['main']['feels_like']:.1f}°C")
            with col2:
                weather_cols = st.columns(4)
                with weather_cols[0]:
                    st.markdown(f"**Weather:** {weather_data['weather'][0]['description'].title()}")
                with weather_cols[1]:
                    st.markdown(f"**Humidity:** {weather_data['main']['humidity']}%")
                with weather_cols[2]:
                    st.markdown(f"**Wind:** {weather_data['wind']['speed']} m/s")
                with weather_cols[3]:
                    st.markdown(f"**Pressure:** {weather_data['main']['pressure']} hPa")

            st.divider()

            # Forecast
            forecast_data = get_weather_forecast(city_input, WEATHER_API_KEY)
            if forecast_data and 'list' in forecast_data:
                st.subheader("📈 5-Day Weather Forecast")
                temps, dates = [], []
                for item in forecast_data['list']:
                    if '12:00:00' in item['dt_txt']:
                        temps.append(item['main']['temp'])
                        dates.append(item['dt_txt'].split(" ")[0])
                if temps and dates:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=dates, y=temps, mode='lines+markers', name='Temp (°C)'))
                    fig.update_layout(title='5-Day Temperature Forecast (12 PM)',
                                      xaxis_title='Date',
                                      yaxis_title='Temperature (°C)')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No forecast data found for 12:00 PM.")
            else:
                st.error("Forecast data could not be loaded.")

            st.divider()

            # Tourist + Food Recommendations
            if st.session_state.data_loaded:
                recommendations = get_city_recommendations(st.session_state.cities_data, city_input)

                if recommendations and recommendations.get('tourist_places'):
                    st.subheader("🏛️ Tourist Attractions")
                    tourist_places = recommendations['tourist_places']
                    num_cols = min(len(tourist_places), 4)
                    rows = [tourist_places[i:i + num_cols] for i in range(0, len(tourist_places), num_cols)]
                    for row in rows:
                        cols = st.columns(len(row))
                        for idx, place in enumerate(row):
                            with cols[idx]:
                                st.markdown(f"### {place}")
                                try:
                                    summary = wikipedia.summary(place + f", {city_input}", sentences=2)
                                    st.write(summary)
                                except wikipedia.exceptions.DisambiguationError:
                                    st.write("⚠️ Multiple results found. Try a more specific name.")
                                except wikipedia.exceptions.PageError:
                                    st.write("⚠️ No Wikipedia page found.")
                                except Exception:
                                    st.write("⚠️ Unable to fetch summary.")

                    st.divider()

                breakfast_col, dinner_col = st.columns(2)
                with breakfast_col:
                    st.subheader("🍳 Top Breakfast Spots")
                    if recommendations.get('breakfast_spots'):
                        for spot in recommendations['breakfast_spots']:
                            col1, col2 = st.columns([8, 1])
                            with col1:
                                st.write(f"• {spot}")
                            with col2:
                                maps_url = f"https://www.google.com/maps/search/?api=1&query={spot.replace(' ', '+')}+{city_input}"
                                st.markdown(f"[📍 Map]({maps_url})")
                    else:
                        st.write("No breakfast spot data available for this city.")
                with dinner_col:
                    st.subheader("🍽️ Top Dinner Spots")
                    if recommendations.get('dinner_spots'):
                        for spot in recommendations['dinner_spots']:
                            col1, col2 = st.columns([8, 1])
                            with col1:
                                st.write(f"• {spot}")
                            with col2:
                                maps_url = f"https://www.google.com/maps/search/?api=1&query={spot.replace(' ', '+')}+{city_input}"
                                st.markdown(f"[📍 Map]({maps_url})")
                    else:
                        st.write("No dinner spot data available for this city.")
            else:
                st.info("Tourism and food data is not available.")

        st.divider()

        # --- Folium Map ---
        m = folium.Map(location=[city_latitude, city_longitude], zoom_start=12)

        # City Marker
        folium.Marker(
            [city_latitude, city_longitude],
            popup=f"City: {city_input}",
            tooltip=f"City: {city_input}",
            icon=folium.Icon(color='purple', icon='home')
        ).add_to(m)

        # Load CSV Places
        try:
            df = pd.read_csv(PLACES_CSV_PATH)
        except FileNotFoundError:
            st.error("Error: The file 'address1.csv' was not found.")
            st.stop()

        category_colors = {
            'tourist': 'blue',
            'breakfast': 'green',
            'dinner': 'red'
        }

        for _, row in df.iterrows():
            city = row['City']
            place = row['Place']
            category = row['Category'].lower()
            latitude = row['Latitude']
            longitude = row['Longitude']
            color = category_colors.get(category, 'gray')
            tooltip_text = f"City: {city}<br>Place: {place}<br>Category: {category.title()}"
            folium.Marker(
                [latitude, longitude],
                tooltip=tooltip_text,
                icon=folium.Icon(color=color, icon='info-sign')
            ).add_to(m)

        # --- Centered Map Display ---
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            st_folium(m, width=700, height=500)

    else:
        st.warning(f"Could not find the location for '{city_input}'. Please check the spelling or try a different city.")

# Footer
st.markdown("---")
st.markdown("🔍 Tourist info is powered by Wikipedia summaries.")
st.markdown("📍 Clickable map links help you navigate easily.")
st.markdown("Data sources: OpenWeatherMap API and curated tourism/food Excel data.")
