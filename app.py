import streamlit as st
import boto3
import pandas as pd
import matplotlib.pyplot as plt
import datetime

# Set Streamlit page to wide mode
st.set_page_config(layout="wide")

# Initialize a DynamoDB session
# Replace 'your-region' with your AWS region where the DynamoDB is hosted
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('uncertainty')

def fetch_data():
    # Scan DynamoDB table to fetch all data
    try:
        response = table.scan()
        data = response['Items']
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response['Items'])
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        return pd.DataFrame()

def filter_data(df, start_date, end_date, prediction):
    df['timestamp'] = pd.to_datetime(df['timestamp']) # mengubah format timestamp yang tadinya string menjadi datetime objek
    df['confidence'] = pd.to_numeric(df['confidence']) # merubah format confidence yang tadinya string menjadi numerical
    filtered = df[(df['timestamp'] >= pd.to_datetime(start_date)) & (df['timestamp'] <= pd.to_datetime(end_date))] #melakukan filter datetime
    if prediction != 'all': #jika jenis prediction tidak all maka akan melakukan filter tambahan dia masuk prediksi yang mana
        filtered = filtered[filtered['prediction'] == prediction]
    return filtered

def plot_confidence(df, time_frame, threshold=0.6):
    #jika data kosong maka akan ada tulisan no data to plot
    if df.empty:
        st.write("No data to plot.")
        return #supaya function berhenti disitu atau melakukan return None
    
    df.set_index('timestamp', inplace=True)
    if time_frame == 'Hourly':
        df_resample = df['confidence'].resample('H').mean()
    elif time_frame == 'Daily':
        df_resample = df['confidence'].resample('D').mean()
    elif time_frame == 'Monthly':
        df_resample = df['confidence'].resample('M').mean()
    elif time_frame == 'Yearly':
        df_resample = df['confidence'].resample('A').mean()

    plt.figure(figsize=(10, 4)) #menyesuaikan shape dari plot figure
    plt.plot(df_resample.index, df_resample, marker='o', linestyle='-') #melakukan plot pada data dari hasil resample
    plt.title(f'Mean Confidence Scores: {time_frame}') # memberikan title
    plt.ylabel('Mean Confidence') # set y label
    plt.xlabel('Time') # set x label
    plt.grid(True) #menambahkan grid supaya mudah dilihat
    plt.xticks(rotation=45) #melakukan rotasi 45 derajat
    plt.ylim(0, 1)  # Set the limits of the y-axis to be between 0 and 1 
    plt.axhline(y=threshold, color='r', linestyle='--')  # Add a red horizontal line at the threshold
    st.pyplot(plt)

# Streamlit UI Components
st.title("DynamoDB Data Viewer for Uncertainty Table")

default_start_date = datetime.date.today() - datetime.timedelta(days=366)

data = fetch_data()
print(data)
with st.sidebar: #untuk menaruh keseluruhan komponen ke kiri
    # set threshold menggunakan number_input
    threshold = st.number_input("Threshold", min_value=0.0, max_value=1.0, value=0.5, step=0.01)
    # set start date dengan kompnen date_input
    start_date = st.date_input("Start Date", value=default_start_date)
    # set end date dengan komponen date_input
    end_date = st.date_input("End Date")
    # set filter prediction type dengan selectbox
    prediction = st.selectbox("Prediction Type", ["All", "Positive", "Negative"]).lower()
    time_frame = st.selectbox("Aggregate Time Frame", ["Hourly", "Daily", "Monthly", "Yearly"])

if not data.empty:
    data_filtered = filter_data(data, start_date, end_date, prediction)
    st.write(data_filtered)
    plot_confidence(data_filtered, time_frame, threshold=threshold)
else:
    st.write("No data available.")
