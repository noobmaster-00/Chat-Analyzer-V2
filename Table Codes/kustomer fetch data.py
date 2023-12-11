import requests
import pandas as pd
from datetime import datetime, date, timedelta
import pytz
import os

# Constants
KUSTOMER_API_URL = "https://edoofa.api.kustomerapp.com/v1/customers"
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY1MGVjMDVkNjg4MGQwNmJlNTNjZWVhMyIsInVzZXIiOiI2NTBlYzA1YmEzODAxZTQ4YjAwOGNhMDQiLCJvcmciOiI2M2JiZGEzNzY4ODFhYTZlMzdmZGRjNmMiLCJvcmdOYW1lIjoiZWRvb2ZhIiwidXNlclR5cGUiOiJtYWNoaW5lIiwicG9kIjoicHJvZDIiLCJyb2xlcyI6WyJvcmcucGVybWlzc2lvbi5tZXNzYWdlLnJlYWQiLCJvcmcucGVybWlzc2lvbi5ub3RlLnJlYWQiLCJvcmcudXNlci5jdXN0b21lci5yZWFkIiwib3JnLnVzZXIubWVzc2FnZS5yZWFkIiwib3JnLnVzZXIubm90ZS5yZWFkIiwib3JnLnBlcm1pc3Npb24uY3VzdG9tZXIucmVhZCJdLCJhdWQiOiJ1cm46Y29uc3VtZXIiLCJpc3MiOiJ1cm46YXBpIiwic3ViIjoiNjUwZWMwNWJhMzgwMWU0OGIwMDhjYTA0In0.IJI5P-BtBDCda9faVA3gfUYHA_rOZnWYuGM0np2Fbng"  # Replace with your actual API token
HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

mentor_mapping = {
    "64e5b276a184b56000839253": "Sharda Nayak",
    "63c01cb8bb84f3f762184233": "Saloni Rastogi",
    "645cc7e93d165050197cc502": "Ananya",
    "63c01c92a204a608c19c95cb": "Tenzin",
    "640e1696673d90d1182aadc6": "Jasmine Kaur",
    "63beab6b88e9f12575db3466": "Aditi Kapoor"
}

def fetch_customer_messages(customer_id):
    message_endpoint = f"{KUSTOMER_API_URL}/{customer_id}/messages"
    page = 1
    all_messages = []
    while True:
        response = requests.get(f"{message_endpoint}?page={page}&pageSize=1000", headers=HEADERS)
        if response.status_code != 200:
            break
        message_data = response.json()
        all_messages.extend(message_data['data'])
        if len(message_data['data']) < 1000:
            break
        page += 1
    return all_messages

def analyze_chats(chat_df, analysis_date):
    analysis_data = []
    unique_students = chat_df['Student'].unique()
    
    for student in unique_students:
        student_chats = chat_df[(chat_df['Student'] == student) & (chat_df['Date'].dt.date == analysis_date)]
        
        if student_chats.empty:
            missed_reply_mentor = 'No'
            missed_reply_student = 'No'
            broken_chat_mentor = 'No'
            broken_chat_student = 'No'
        else:
            # Check if mentor replied
            mentor_replied = not student_chats[student_chats['Direction'] == 'out'].empty
            # Check if student replied
            student_replied = not student_chats[student_chats['Direction'] == 'in'].empty

            # Determine missed replies
            missed_reply_mentor = 'Yes' if student_replied and not mentor_replied else 'No'
            missed_reply_student = 'Yes' if mentor_replied and not student_replied else 'No'

            # Determine broken chats
            last_message = student_chats.iloc[-1]
            broken_chat_mentor = 'Yes' if last_message['Direction'] == 'in' and mentor_replied else 'No'
            broken_chat_student = 'Yes' if last_message['Direction'] == 'out' and student_replied else 'No'

        analysis_data.append([student, missed_reply_mentor, missed_reply_student, broken_chat_mentor, broken_chat_student])

    return pd.DataFrame(analysis_data, columns=['Student', 'Missed Reply by Mentor', 'Missed Reply by Student', 'Broken Chat by Mentor', 'Broken Chat by Student'])

def main():
    # Set the date range for filtering
    # Define the current date in the 'Asia/Kolkata' timezone
    current_date = datetime.now(pytz.timezone("Asia/Kolkata"))

    # Define start date as the start of the day three days ago
    start_date = current_date - timedelta(days=1)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

    # Define end date as the end of the day yesterday
    end_date = current_date  #timedelta(days=0)
    end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

    # Define the analysis date as two days ago
    analysis_date = current_date.date() - timedelta(days=1)

    response = requests.get(KUSTOMER_API_URL, headers=HEADERS)
    if response.status_code != 200:
        print("Failed to fetch customer data")
        return

    customers = response.json()['data']
    all_rows = []

    for customer in customers:
        customer_id = customer['id']
        first_name = customer['attributes'].get('firstName', 'Unknown')
        last_name = customer['attributes'].get('lastName', 'Unknown')
        full_name = f"{first_name} {last_name}"

        messages = fetch_customer_messages(customer_id)
        for message in messages:
            sent_at_utc = datetime.strptime(message['attributes']['sentAt'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.utc)
            sent_at_ist = sent_at_utc.astimezone(pytz.timezone("Asia/Kolkata"))

            # Filter messages based on the date range
            if start_date <= sent_at_ist <= end_date:
                sent_at_local = sent_at_ist.strftime("%m/%d/%Y %H:%M:%S")
                direction = message['attributes']['direction']
                preview = message['attributes']['preview']
                user_id = message['relationships'].get('createdBy', {}).get('data', {}).get('id', None)
                mentor_name = mentor_mapping.get(user_id, "Unknown Mentor")

                all_rows.append([sent_at_local, preview, mentor_name, full_name, direction])

    chat_df = pd.DataFrame(all_rows, columns=['Date', 'Body', 'Mentor', 'Student', 'Direction'])
    chat_df['Date'] = pd.to_datetime(chat_df['Date'])
    analysis_df = analyze_chats(chat_df, analysis_date)

    # Save as Excel with multiple sheets
    excel_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kustomer_analysis15.xlsx')
    with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:
        chat_df.to_excel(writer, sheet_name='Chat Data', index=False)
        analysis_df.to_excel(writer, sheet_name='Analysis', index=False)

    print(f"Analysis saved to {excel_file_path}")

if __name__ == "__main__":
    main()