import streamlit as st
import pandas as pd
import plotly.express as px
import os
import warnings
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials
import numpy as np

warnings.filterwarnings('ignore')

# Set up the page configuration
st.set_page_config(page_title="Superstore!!!", page_icon=":bar_chart:", layout="wide")

# Title of the dashboard
st.title(" :bar_chart: Sample SuperStore EDA")
st.markdown('<style>div.block-container{padding-top:2rem;}</style>', unsafe_allow_html=True)

# Google Sheets setup using Streamlit Secrets
creds = Credentials.from_service_account_info(st.secrets["gspread"], scopes=[
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
])
client = gspread.authorize(creds)

# Open the spreadsheet by its URL
spreadsheet_url = "https://docs.google.com/spreadsheets/d/18HsrafM5ggen4G7KJbfZoFmm7hIpouPCEs9Mxiv9kYc"
workbook = client.open_by_url(spreadsheet_url)

# Select the first sheet
worksheet = workbook.get_worksheet(0)

# Get all the records of the data
records = worksheet.get_all_records()

 # Convert to DataFrame
data = pd.DataFrame(records)



print(data.info())
columns_to_convert = ['Count', 'Hybrid', 'Remote', 'In Person']

for column in columns_to_convert:
    # Replace commas and convert empty strings to NaN
    data[column] = data[column].replace(',', '').replace('', np.nan)

    # Use pd.to_numeric to convert data types, coercing errors to NaN
    data[column] = pd.to_numeric(data[column], errors='coerce')

data.loc[data['In Person'] == 0, 'In Person'] = np.nan
data.dropna(subset=['Hybrid', 'Remote', 'In Person'], how='all', inplace=True)
data['In Person'] = data['In Person'].fillna(0)
data.dropna(subset=['Date', 'Title'], how='all', inplace=True)


data['Count'] = data['Count'].fillna(data[['Hybrid', 'Remote', 'In Person']].sum(axis=1))











# Ensuring 'Date' is in datetime format
data['Date'] = pd.to_datetime(data['Date'])

idx = data.groupby(['Title', data['Date'].dt.date])['Date'].idxmax()

# Filter data based on the indices to keep only the most recent records
data = data.loc[idx].reset_index(drop=True)






col1, col2 = st.columns((2))
data["Date"] = pd.to_datetime(data["Date"])

# Getting the min and max date 
startDate = pd.to_datetime(data["Date"]).min()
endDate = pd.to_datetime(data["Date"]).max()

with col1:
    date1 = pd.to_datetime(st.date_input("Start Date", startDate))
    if date1 < startDate:
        date1 = startDate
    elif date1 > endDate:
        date1 = endDate

with col2:
    date2 = pd.to_datetime(st.date_input("End Date", endDate))
    if date2 < date1:
        date2 = date1
    elif date2 > endDate:
        date2 = endDate

df = data[(data["Date"] >= date1) & (data["Date"] <= date2)].copy()


st.sidebar.header("Choose your filter: ")
# Create for Region
title = st.sidebar.multiselect("Pick your Title", df["Title"].unique())
if not title:
    df2 = df.copy()
else:
    df2 = df[df["Title"].isin(title)]



df2['Count'] = df2['Count'].replace(',', '', regex=True).astype(int)
df2['Hybrid'] = df2['Hybrid'].replace(',', '', regex=True).astype(float)
df2['Remote'] = df2['Remote'].replace(',', '', regex=True).astype(float)
df2['In Person'] = df2['In Person'].replace(',', '', regex=True).astype(float)
df2['Date'] = pd.to_datetime(df2['Date'])

# Filter data to only include the most recent date
most_recent_date = df2['Date'].max()
recent_data = df2[df2['Date'] == most_recent_date]



with col1:
    # Group by 'Title' and calculate the mean of the 'Count' column
    mean_counts = df2.groupby('Title')['Count'].mean().reset_index()

    # Calculate the total to find percentages
    total_count = mean_counts['Count'].sum()

    # Create the pie chart using Plotly
    fig = px.pie(mean_counts, values='Count', names='Title',
                 title="Distribution of Titles",
                 labels={'Count':'Percentage'})

    # Customize hover template to show title, percentage, and count
    fig.update_traces(hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}')

    # Move the legend to the right side of the plot
    fig.update_layout(legend_title="Titles",
                      legend=dict(orientation="v",
                                  x=1.05, xanchor="left",
                                  y=0.5, yanchor="middle"))

    # Ensure equal aspect ratio to maintain the pie shape
    fig.update_traces(textposition='inside')

    # Display the pie chart using Streamlit
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Group by 'Title' and calculate the mean of the 'Count' column for the most recent data
    recent_mean_counts = recent_data.groupby('Title')['Count'].mean().reset_index()

    # Create the pie chart using Plotly
    fig2 = px.pie(recent_mean_counts, values='Count', names='Title',
                  title=f"Distribution of Titles on {most_recent_date.strftime('%Y-%m-%d')}",
                  labels={'Count':'Percentage'})
    fig2.update_traces(hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}')
    fig2.update_layout(legend_title="Titles",
                       legend=dict(orientation="v",
                                   x=1.05, xanchor="left",
                                   y=0.5, yanchor="middle"))
    fig2.update_traces(textposition='inside')
    st.plotly_chart(fig2, use_container_width=True)





with st.expander("Detailed Analysis by Title"):
    col_exp1, col_exp2 = st.columns(2)

    # Single select dropdown for titles in both columns
    with col_exp1:
        selected_title1 = st.selectbox('Select Title for Analysis (Column 1):', options=df2['Title'].unique())
        # Filter data based on selected title and calculate means for each category
        title_data1 = df2[df2['Title'] == selected_title1]
        title_summary1 = title_data1[['Hybrid', 'Remote', 'In Person']].mean().reset_index()
        title_summary1.columns = ['Type', 'Mean']
     

        # Create pie chart for selected title
        fig_exp1 = px.pie(title_summary1, values='Mean', names='Type',
                          title=f"Work Type Distribution for {selected_title1}",
                          labels={'Mean':'Percentage'})
        fig_exp1.update_traces(hovertemplate='<b>%{label}</b><br>Mean: %{value}<br>Percentage: %{percent}')
        fig_exp1.update_layout(legend_title="Work Type",
                               legend=dict(orientation="v",
                                           x=1.05, xanchor="left",
                                           y=0.5, yanchor="middle"))
        fig_exp1.update_traces(textposition='inside')
        st.plotly_chart(fig_exp1, use_container_width=True)

    with col_exp2:
        selected_title2 = st.selectbox('Select Title for Analysis (Column 2):', options=df2['Title'].unique())
        # Filter data based on selected title and calculate means for each category
        title_data2 = df2[df2['Title'] == selected_title2]
        title_summary2 = title_data2[['Hybrid', 'Remote', 'In Person']].mean().reset_index()
        title_summary2.columns = ['Type', 'Mean']

        # Create pie chart for selected title
        fig_exp2 = px.pie(title_summary2, values='Mean', names='Type',
                          title=f"Work Type Distribution for {selected_title2}",
                          labels={'Mean':'Percentage'})
        fig_exp2.update_traces(hovertemplate='<b>%{label}</b><br>Mean: %{value}<br>Percentage: %{percent}')
        fig_exp2.update_layout(legend_title="Work Type",
                               legend=dict(orientation="v",
                                           x=1.05, xanchor="left",
                                           y=0.5, yanchor="middle"))
        fig_exp2.update_traces(textposition='inside')
        st.plotly_chart(fig_exp2, use_container_width=True)


with st.expander("Trend Analysis by Title"):
    # Multi-select filter for selecting titles
    selected_titles = st.multiselect('Select Titles:', options=df2['Title'].unique())

    # Filter the data based on selected titles
    if selected_titles:
        filtered_data = df2[df2['Title'].isin(selected_titles)]

        # Group by Date and Title to aggregate counts
        grouped_data = filtered_data.groupby(['Date', 'Title'])['Count'].sum().reset_index()

        # Create line chart
        fig = px.line(grouped_data, x='Date', y='Count', color='Title',
                      title="Trend of Counts Over Time",
                      labels={'Count': 'Total Count', 'Date': 'Date'},
                      markers=True)

        # Add hover data
        fig.update_traces(mode='markers+lines', 
                          hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Count:</b> %{y}")

        # Update layout for better readability
        fig.update_layout(xaxis_title='Date',
                          yaxis_title='Count',
                          legend_title="Title",
                          xaxis=dict(tickformat="%Y-%m-%d"),
                          # Set dynamic y-axis range if appropriate or consider uncommenting for log scale
                          # yaxis_type="log" 
                          )

        # Dynamically adjust Y-axis to better show changes
        if grouped_data['Count'].min() > 0:  # Check to ensure no zero or negative values for log scale
            fig.update_yaxes(range=[grouped_data['Count'].min() * 0.95, grouped_data['Count'].max() * 1.05])
        
        # Display the line chart using Streamlit
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Please select at least one title to display the trends.")



