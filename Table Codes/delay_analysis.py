import os
import pandas as pd
import datetime
import re
import logging

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def list_chat_files(date_directory):
    chat_files = []
    for date_folder in os.listdir(date_directory):
        date_path = os.path.join(date_directory, date_folder)
        if os.path.isdir(date_path):
            for team_folder in os.listdir(date_path):
                if team_folder != "KAM":
                    continue
                
                team_path = os.path.join(date_path, team_folder)
                if os.path.isdir(team_path):
                    for person_folder in os.listdir(team_path):
                        person_path = os.path.join(team_path, person_folder)
                        if os.path.isdir(person_path):
                            for file in os.listdir(person_path):
                                if file.endswith('.txt'):
                                    chat_files.append(os.path.join(person_path, file))
    logging.debug(f"Chat files listed: {chat_files}")
    return chat_files

def parse_chat_file(file_path, expected_date_minus_one):
    chat_data = []
    last_person_time = None
    last_sender = None
    delay_count = 0

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
            if date_time.date() != expected_date_minus_one:
                continue

            is_person = sender is not None and re.match(r'^[+\d\s-]+$', sender) is None
            delay = False
            if is_person:
                if last_person_time and sender != last_sender and (date_time - last_person_time).total_seconds() > 900:
                    delay = True
                    delay_count += 1
                if not delay:
                    last_person_time = date_time
                    last_sender = sender

            chat_data.append((date_time, sender, is_person, delay))
    logging.debug(f"File parsed: {file_path}. Delays detected: {delay_count}")
    return chat_data, extract_group_name(file_path)

def create_template_dataframe():
    times = [datetime.datetime(2000, 1, 1, 0, 0) + datetime.timedelta(minutes=1 * i) for i in range(1440)]
    intervals = [time.strftime('%I:%M %p') for time in times]
    df = pd.DataFrame(index=pd.to_datetime(intervals).strftime('%I:%M %p').unique())  # Ensure unique intervals
    return df

def populate_dataframe(df, parsed_data, group_name):
    # Define new column names
    person_col = f"{group_name}_person"
    others_col = f"{group_name}_others"
    delay_col = f"{group_name}_delay"

    # Initialize new columns
    if person_col not in df.columns:
        df[person_col] = 0
    if others_col not in df.columns:
        df[others_col] = 0
    if delay_col not in df.columns:
        df[delay_col] = 0

    # Populate the new columns with parsed data
    for date_time, sender, is_person, delay in parsed_data:
        interval_index = min((date_time.hour * 60 + date_time.minute) // 1, 1439)
        interval = df.index[interval_index]

        if is_person:
            df.at[interval, person_col] = 1
        else:
            df.at[interval, others_col] = 1

        if delay:
            df.at[interval, delay_col] = 1

        logging.debug(f"Updated DataFrame at {interval} for {group_name}: Person={is_person}, Delay={delay}")

    # Update active_chat column
    if 'active_chat' not in df.columns:
        df['active_chat'] = 0

    relevant_columns = [person_col, others_col]
    df['active_chat'] = df[relevant_columns].any(axis=1).astype(int)

    return df

def extract_group_name(file_path):
    group_name = os.path.basename(file_path).replace('WhatsApp Chat with ', '').split('.')[0]
    group_name = re.sub(r'\(\d+\)$', '', group_name)  # Remove any numbers in parentheses at the end
    return group_name  # Removed the extra "_person" suffix

date_directory = "C:\\Users\\maurice\\Documents\\Chat-Analyzer-V2\\Chat Folder from Drive\\drive-download-20231201T052455Z-001"
chat_files = list_chat_files(date_directory)
dataframes = {}

for file in chat_files:
    parts = file.split(os.sep)
    date_folder, person = parts[-4], parts[-2]

    try:
        folder_date = pd.to_datetime(date_folder, format='%Y-%m-%d').date()
    except ValueError:
        continue

    expected_date_minus_one = folder_date - datetime.timedelta(days=1)
    key = f"{folder_date.strftime('%Y-%m-%d')}_{person}"

    if key not in dataframes:
        dataframes[key] = create_template_dataframe()
    parsed_data, group_name = parse_chat_file(file, expected_date_minus_one)
    dataframes[key] = populate_dataframe(dataframes[key], parsed_data, group_name)
    logging.debug(f"Dataframe created for key: {key}")

# Example to show a dataframe
example_key = next(iter(dataframes))  # Just for demonstration
logging.debug(f"Example dataframe for key {example_key}: \n{dataframes[example_key]}")
