import os
import pandas as pd
import datetime
import re

# Constants
DELAY_THRESHOLD = 15  # minutes
LAST_DAYS = 7  # number of days to filter

# Function to check if a string is numeric
def is_numeric(s):
    return s.replace('+', '', 1).isdigit()

# Function to filter messages from the last 7 days
def filter_last_7_days_messages(file_path):
    print(f"Filtering messages from the last 7 days in file: {file_path}")  # Debug
    recent_messages = []
    current_date = datetime.datetime.now()
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            match = re.match(r'(\d{2}/\d{2}/\d{2}, \d{1,2}:\d{2} [ap]m) -', line)
            if match:
                timestamp = datetime.datetime.strptime(match.group(1), '%d/%m/%y, %I:%M %p')
                if (current_date - timestamp).days < LAST_DAYS:
                    recent_messages.append(line.strip())
    print(f"Found {len(recent_messages)} messages from the last 7 days.")  # Debug
    return recent_messages

# Function to calculate delays and identify the person
def calculate_delays_and_identify_person(messages):
    print("Calculating delays and identifying the person...")  # Debug
    delays = []
    last_person_message_time = None
    for message in messages:
        timestamp_str, sender_and_message = message.split(' - ', 1)
        timestamp = datetime.datetime.strptime(timestamp_str, '%d/%m/%y, %I:%M %p')
        sender = sender_and_message.split(':', 1)[0]
        if not is_numeric(sender):  # Person's message
            if last_person_message_time and (timestamp - last_person_message_time).total_seconds() / 60 > DELAY_THRESHOLD:
                delays.append(last_person_message_time.strftime('%d/%m/%y, %I:%M %p'))
            last_person_message_time = timestamp
    print(f"Delays identified: {delays}")  # Debug
    return delays

# Main analysis process
def main_analysis(root_directory):
    print(f"Starting delay analysis in root directory: {root_directory}")  # Debug
    analysis_table = pd.DataFrame(columns=['Date', 'Chat Group Name', 'Person', 'Time of Delay', 'Last 7 Messages'])
    
    # Iterate over the directory structure
    for date_folder in os.listdir(root_directory):
        date_path = os.path.join(root_directory, date_folder)
        print(f"Processing date folder: {date_folder}")  # Debug
        for team_folder in os.listdir(date_path):
            team_path = os.path.join(date_path, team_folder)
            print(f"Processing team folder: {team_folder}")  # Debug
            for person_folder in os.listdir(team_path):
                person_path = os.path.join(team_path, person_folder)
                print(f"Processing person folder: {person_folder}")  # Debug
                for file in os.listdir(person_path):
                    if file.endswith('.txt'):
                        chat_file_path = os.path.join(person_path, file)
                        messages = filter_last_7_days_messages(chat_file_path)
                        delays = calculate_delays_and_identify_person(messages)
                        last_7_messages = ' | '.join(messages[-7:])
                        for delay in delays:
                            analysis_table = analysis_table.append({
                                'Date': date_folder, 
                                'Chat Group Name': team_folder, 
                                'Person': person_folder, 
                                'Time of Delay': delay, 
                                'Last 7 Messages': last_7_messages
                            }, ignore_index=True)
                            print(f"Added delay entry for {person_folder} on {date_folder}")  # Debug

    print("Analysis complete. Returning DataFrame.")  # Debug
    return analysis_table

# Run the analysis
root_directory = 'C:\\Users\\mauriceyeng\\Python\\Daily-Reports\\Test\\V1_maurice\\TestingData'  # Replace with the actual path
delay_analysis_table = main_analysis(root_directory)
print(delay_analysis_table.head())  # Displaying the first few rows of the analysis table
