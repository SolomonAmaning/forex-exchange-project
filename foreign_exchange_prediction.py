
import streamlit as st
import pandas as pd
from prophet import Prophet
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Loading historical data
@st.cache_data
def load_data():
    df = pd.read_csv('./HistoricalPrices.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    df.rename(columns={'Date': 'ds', 'Close': 'y'}, inplace=True)
    return df

# Training the Prophet model
def train_model(df):
    model = Prophet()
    model.fit(df)
    return model

# Generate forecast
def generate_forecast(model, days):
    future = model.make_future_dataframe(periods=days)
    forecast = model.predict(future)
    return forecast

# Set up Streamlit app title and description
st.title('USD/GBP Exchange Rate Forecast with Custom Starting Point')
st.write('Developed by Solomon Odum')

# Sidebar input for forecast options
st.sidebar.header("Input Current Values and Forecast Options")

# User input for the current USD and GBP values
current_usd = st.sidebar.number_input('Enter the current USD value:', min_value=0.1, value=1.0, step=0.1)
current_gbp = st.sidebar.number_input('Enter the current GBP closing rate:', min_value=0.1, value=1.0, step=0.1)
years = st.sidebar.slider('Select forecast period (years):', 1, 10, 5)

# Load historical data and append new row based on user input
df = load_data()

# Create today's date with the user input values and append to dataset
today = pd.DataFrame({'ds': [datetime.now()], 'y': [current_gbp]})
df_updated = pd.concat([df, today], ignore_index=True)

# Retrain model with updated data including today's custom value
model = train_model(df_updated)

# Generate forecast based on user-selected years
forecast = generate_forecast(model, years * 365)

# Adjust forecast based on current USD value
forecast['yhat_adjusted'] = forecast['yhat'] * current_usd

# Combine historical data and forecast
combined_df = pd.concat([df_updated[['ds', 'y']], forecast[['ds', 'yhat_adjusted']]], ignore_index=True)
combined_df['y_combined'] = combined_df['y']
combined_df['y_combined'].fillna(combined_df['yhat_adjusted'], inplace=True)

# Create a year slider
min_year = combined_df['ds'].dt.year.min()
max_year = combined_df['ds'].dt.year.max()
selected_year = st.sidebar.slider('Select a Year:', int(min_year), int(max_year), int(datetime.now().year))

# Retrieve data for the selected year
selected_year_data = combined_df[combined_df['ds'].dt.year == selected_year]

if not selected_year_data.empty:
    if selected_year <= datetime.now().year:
        # Historical year
        actual_rate = selected_year_data['y'].mean()  # Average rate for the year
        adjusted_rate = actual_rate * current_usd
        st.write(f"**Historical Data for {selected_year}:**")
        st.write(f"Actual Closing Rate: {actual_rate:.4f}")
        st.write(f"Adjusted Closing Rate (based on current USD value): {adjusted_rate:.4f}")
    else:
        # Future year
        forecasted_rate = selected_year_data['yhat_adjusted'].mean()  # Average forecasted rate for the year
        st.write(f"**Forecasted Data for {selected_year}:**")
        st.write(f"Forecasted Closing Rate: {forecasted_rate:.4f}")
else:
    st.write(f"No data available for the year {selected_year}.")

# Forecast visualization
fig = go.Figure()

# Plot historical data
fig.add_trace(go.Scatter(
    x=df_updated['ds'],
    y=df_updated['y'],
    mode='lines',
    name='Historical Data',
    line=dict(color='royalblue')
))

# Plot forecasted data
forecast_dates = forecast[forecast['ds'] > df_updated['ds'].max()]['ds']
forecast_values = forecast[forecast['ds'] > df_updated['ds'].max()]['yhat_adjusted']
fig.add_trace(go.Scatter(
    x=forecast_dates,
    y=forecast_values,
    mode='lines',
    name='Forecast',
    line=dict(color='orange')
))

# Highlight selected year on the plot
selected_year_start = datetime(selected_year, 1, 1)
selected_year_end = datetime(selected_year, 12, 31)
fig.add_vrect(
    x0=selected_year_start, x1=selected_year_end,
    fillcolor="LightGreen", opacity=0.25,
    layer="below", line_width=0,
    annotation_text=f"Selected Year: {selected_year}", annotation_position="top left"
)

# Update layout
end_date = df_updated['ds'].max() + timedelta(days=years * 365)
fig.update_layout(
    title=f'USD/GBP Exchange Rate Forecast - Starting from Today ({years} Year Forecast)',
    xaxis=dict(title='Date', range=[df_updated['ds'].min(), end_date], tickformat="%Y"),
    yaxis=dict(title='Exchange Rate'),
    hovermode='x'
)

# Display the plot
st.plotly_chart(fig)

# Show trend and seasonality components if selected
st.subheader("Trend and Seasonality Components")
if st.checkbox("Show trend and seasonality components"):
    # Trend Component
    trend_fig = go.Figure()
    trend_fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['trend'],
        mode='lines',
        name='Trend',
        line=dict(color='green')
    ))
    trend_fig.update_layout(title="Trend Component", xaxis_title="Date", yaxis_title="Trend")
    st.plotly_chart(trend_fig)

    # Yearly Seasonality
    if 'yearly' in forecast.columns:
        yearly_fig = go.Figure()
        yearly_fig.add_trace(go.Scatter(
            x=forecast['ds'],
            y=forecast['yearly'],
            mode='lines',
            name='Yearly Seasonality',
            line=dict(color='purple')
        ))
        yearly_fig.update_layout(title="Yearly Seasonality", xaxis_title="Date", yaxis_title="Yearly Seasonality")
        st.plotly_chart(yearly_fig)
    else:
        st.write("Yearly seasonality data not available.")
