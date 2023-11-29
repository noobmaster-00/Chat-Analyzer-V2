import os
import pandas as pd
import re
import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


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

def parse_chat_file_for_delay_analysis(file_path):
    # Extract person_name and date from the file path
    person_name = os.path.basename(os.path.dirname(file_path))
    folder_date_str = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(file_path))))
    expected_date_minus_one = pd.to_datetime(folder_date_str, format='%Y-%m-%d').date() - datetime.timedelta(days=1)

    delay_messages = []

    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    last_person_msg_time = None
    last_person_msg_index = None

    for i, line in enumerate(lines):
        message_match = re.match(r'(\d{2}/\d{2}/\d{2}, \d{1,2}:\d{2} [ap]m) - (.*?): (.*)', line)
        if message_match:
            date_time_str, sender, message = message_match.groups()
            date_time = pd.to_datetime(date_time_str, format='%d/%m/%y, %I:%M %p')

            if date_time.date() != expected_date_minus_one:
                continue

            # Check if the sender is a person (not purely numeric or starting with +)
            is_person = sender is not None and not (sender.strip().isnumeric() or sender.startswith('+'))

            logging.info(f"Sender: {sender}, Is Person: {is_person}, Message: {message}")  # Debug line

            if is_person:
                if last_person_msg_time is not None:
                    # Calculate the time difference in minutes
                    time_diff_seconds = (date_time - last_person_msg_time).total_seconds()
                    time_diff_minutes = time_diff_seconds / 60
                    logging.info(f"Time Difference (minutes): {time_diff_minutes}")  # Debug line
                    if time_diff_minutes > 15:
                        # There is a delay
                        delay = True
                    else:
                        # No delay
                        delay = False
                        time_diff_minutes = None
                else:
                    # No previous message from a person
                    delay = False
                    time_diff_minutes = None
                last_person_msg_time = date_time
                last_person_msg_index = i
            else:
                # Not a message from a person
                delay = False
                time_diff_minutes = None

            if delay:
                # Fetch reference messages
                start_index = max(last_person_msg_index - 3, 0)
                end_index = min(i + 4, len(lines) - 1)
                reference_msgs = lines[start_index:end_index + 1]

                delay_messages.append((date_time, sender, message, delay, time_diff_minutes, reference_msgs))

    return delay_messages, file_path

            
def process_all_files(chat_files):
    all_delay_messages = []

    for file_path in chat_files:
        logging.debug(f"Processing file: {file_path}")  # Debug line
        delay_messages, file_path_from_function = parse_chat_file_for_delay_analysis(file_path)
        for message in delay_messages:
            all_delay_messages.append((*message, file_path_from_function))

    return all_delay_messages



def create_delay_data_dataframe(all_delay_data):
    columns = ['Date', 'Person', 'Chat Group Name', 'Delay', 'Delay in Mins', 'Reference Messages']
    df_data = []

    for delay_instance in all_delay_data:
        date_time, sender, message, delay, time_diff_minutes, reference_msgs, file_path = delay_instance

        file_name = os.path.basename(file_path)
        logging.info(f"Processing file name: {file_name}")  # Debugging line

        # Regex to extract the chat group name
        group_name_match = re.match(r'WhatsApp Chat with (.+?)\.txt', file_name)
        chat_group_name = group_name_match.group(1) if group_name_match else "Unknown Group"

        df_data.append([date_time, sender, chat_group_name, delay, time_diff_minutes, reference_msgs])

    delay_df = pd.DataFrame(df_data, columns=columns)
    return delay_df



# Main Execution
date_directory = "C:\\Users\\mauriceyeng\\Python\\Daily-Reports\\Test\\filtered_chats"
chat_files = list_chat_files(date_directory)
all_delay_data = process_all_files(chat_files)
delay_analysis_df = create_delay_data_dataframe(all_delay_data)

# Display the first few rows of the DataFrame
print(delay_analysis_df.head())
