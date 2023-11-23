import os
import pandas as pd
import datetime
import re

# Function to list all chat files in the directory structure
def list_chat_files(date_directory):
    chat_files = []
    for date_folder in os.listdir(date_directory):
        date_path = os.path.join(date_directory, date_folder)
        if os.path.isdir(date_path):
            for team_folder in os.listdir(date_path):
                team_path = os.path.join(date_path, team_folder)
                if os.path.isdir(team_path):
                    for person_folder in os.listdir(team_path):
                        person_path = os.path.join(team_path, person_folder)
                        if os.path.isdir(person_path):
                            for file in os.listdir(person_path):
                                if file.endswith('.txt'):
                                    chat_files.append(os.path.join(person_path, file))
    return chat_files

def parse_chat_file(file_path, expected_date):
    chat_data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            message_match = re.match(r'(\d{2}/\d{2}/\d{2}, \d{1,2}:\d{2} [ap]m) - (.*?): (.*)', line)
            system_match = re.match(r'(\d{2}/\d{2}/\d{2}, \d{1,2}:\d{2} [ap]m) - (.*)', line)
            if message_match:
                date_time_str, sender, message = message_match.groups()
            elif system_match:
                date_time_str, info = system_match.groups()
                sender = None
            else:
                continue

            date_time = pd.to_datetime(date_time_str, format='%d/%m/%y, %I:%M %p')

            if date_time.date() != expected_date:
                continue

            # Check if sender's name is not purely numeric
            is_person = not sender.isnumeric() if sender else False
            chat_data.append((date_time, sender, is_person))
    return chat_data

# Function to create a template dataframe
def create_template_dataframe():
    times = [datetime.datetime(2000, 1, 1, 0, 0) + datetime.timedelta(minutes=5 * i) for i in range(280)]
    intervals = [time.strftime('%I:%M %p') for time in times]
    df = pd.DataFrame(index=intervals)
    return df

# Function to populate the dataframe
def populate_dataframe(df, parsed_data, start_column_index):
    person_column_index = start_column_index
    for entry in parsed_data:
        date_time, sender, is_person = entry
        interval_index = min((date_time.hour * 60 + date_time.minute) // 5, 279)
        interval = df.index[interval_index]

        if person_column_index not in df.columns:
            df[person_column_index] = 0
        if person_column_index + 1 not in df.columns:
            df[person_column_index + 1] = 0

        if is_person:
            df.at[interval, person_column_index] = 1
        else:
            df.at[interval, person_column_index + 1] = 1

    return person_column_index + 2

def process_person_chats(chat_files):
    dataframes = {}
    for file in chat_files:
        parts = file.split(os.sep)
        date_folder, person = parts[-4], parts[-2]

        try:
            expected_date = pd.to_datetime(date_folder).date()
        except ValueError:
            print(f"Skipping file due to incorrect date format in folder name: {file}")
            continue

        key = f"{expected_date.strftime('%Y-%m-%d')}_{person}"

        if key not in dataframes:
            dataframes[key] = create_template_dataframe()
            start_column_index = 0
        else:
            # Check if the dataframe already has columns
            if not dataframes[key].columns.empty:
                start_column_index = max(dataframes[key].columns) + 1
            else:
                start_column_index = 0

        parsed_data = parse_chat_file(file, expected_date)
        next_column_index = populate_dataframe(dataframes[key], parsed_data, start_column_index)
    
    return dataframes




# Main script
date_directory = "C:\\Users\\mauriceyeng\\Python\\Daily-Reports\\Test\\filtered_chats"
chat_files = list_chat_files(date_directory)
person_dataframes = process_person_chats(chat_files)

# Save each dataframe as a CSV file in the current working directory for testing purpose only, will be omiited in real application

for key, df in person_dataframes.items():
    csv_file_path = f"csvs/{key}.csv"
    df.to_csv(csv_file_path)
    print(f"Saved DataFrame to {csv_file_path}")