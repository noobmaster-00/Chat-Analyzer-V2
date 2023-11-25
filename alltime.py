import os
import pandas as pd
import re
from datetime import datetime, timedelta
import logging
from datetime import timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# Set of processed chats to ensure each chat is analyzed only once
processed_chats = set()

# Function to process a single line of chat
def process_line(line):
    pattern = r'(\d{2}/\d{2}/\d{2}), (\d{1,2}:\d{2}\s?[APMapm]{2}) - (.*?): (.*)'
    match = re.match(pattern, line)
    if match:
        date_str, time_str, sender, message = match.groups()
        date = datetime.strptime(date_str, '%d/%m/%y')
        time = datetime.strptime(time_str, '%I:%M %p').strftime('%H:%M')
        return {'date': date, 'time': time, 'sender': sender, 'message': message}
    else:
        return None


def calculate_time_spent_student(chat_df, target_date, employee_name):
    student_messages = chat_df[(chat_df['date'].dt.date == target_date) & (chat_df['sender'] != employee_name)]
    total_chars = student_messages['message'].str.len().sum()
    time_spent_seconds = (total_chars / 10) * 5
    return strfdelta(timedelta(seconds=time_spent_seconds))
    
    
def is_broken_chat_student(chat_df, employee_name, report_date):
    messages_on_date = chat_df[chat_df['date'].dt.date == report_date]
    if not messages_on_date.empty and messages_on_date.iloc[-1]['sender'] != employee_name:
        return 'Yes'
    return 'No'    
    
    
    
def count_missed_replies_student(chat_df, employee_name, report_date):
    count = 0
    for i in range(7):
        check_date = report_date - timedelta(days=i)
        messages_on_date = chat_df[chat_df['date'].dt.date == check_date]
        employee_messages = messages_on_date[messages_on_date['sender'] == employee_name]
        student_messages = messages_on_date[messages_on_date['sender'] != employee_name]
        if employee_messages.empty and not student_messages.empty:
            count += 1
    return count



def check_missed_reply_student(chat_df, employee_name, report_date):
    messages_on_date = chat_df[chat_df['date'].dt.date == report_date]
    employee_messages = messages_on_date[messages_on_date['sender'] == employee_name]
    student_messages = messages_on_date[messages_on_date['sender'] != employee_name]
    
    if not employee_messages.empty and student_messages.empty:
        return 'Yes'
    return 'No'

    

def count_missed_replies_last_7_days(chat_df, employee_name, start_date):
    missed_replies_count = 0

    # Iterate over the last 7 days
    for i in range(7):
        date_to_check = start_date - timedelta(days=i)
        messages_on_date = chat_df[chat_df['date'].dt.date == date_to_check]

        # Check if there are messages on this date
        if not messages_on_date.empty:
            # Check if there's any message from the employee on this day
            employee_messages = messages_on_date[messages_on_date['sender'] == employee_name]
            
            # Check if there's any message from others (leads) on this day
            lead_messages = messages_on_date[messages_on_date['sender'] != employee_name]

            # If there are messages from others but none from the employee, count as a missed reply
            if not lead_messages.empty and employee_messages.empty:
                missed_replies_count += 1

    return missed_replies_count




# Function to calculate the time spent in chat based on message lengths
def calculate_time_spent(chat_df, target_date, employee_name):
    print(f"Target date: {target_date}")
    print(f"Employee name: {employee_name}")
    print("Sample chat_df dates:", chat_df['date'].head())

    daily_messages = chat_df[(chat_df['date'].dt.date == target_date) & (chat_df['sender'] == employee_name)]
    
    # Debug print to see what's inside daily_messages after filtering
    print(f"Daily messages for {employee_name} on {target_date}:")
    print(daily_messages)

    if daily_messages.empty:
        print(f"No messages found for {employee_name} on {target_date}.")
        return '00:00:00'
    
    total_chars = daily_messages['message'].str.len().sum()
    time_spent_seconds = (total_chars / 10) * 5
    time_spent_timedelta = timedelta(seconds=time_spent_seconds)
    
    # Call the new formatting function
    formatted_time_spent = strfdelta(time_spent_timedelta)
    
    return formatted_time_spent
    
def strfdelta(tdelta):
    # Extract days, hours, minutes, and seconds
    days, seconds = tdelta.days, tdelta.seconds
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 60)
    
    # Format the string as HH:MM:SS
    return f"{hours:02}:{minutes:02}:{seconds:02}"    

def calculate_lead_response_percentage(chat_df, employee_name, day_0_date):
    """
    Calculates the lead response percentage based on message lengths for Day 0.
    """
    day_0_messages = chat_df[chat_df['date'].dt.date == day_0_date]

    if day_0_messages.empty:
        logging.debug(f"No messages found for Day 0: {day_0_date}")
        return 0

    total_percentage_diff, pair_count = 0, 0
    for index in range(len(day_0_messages) - 1):
        current_message = day_0_messages.iloc[index]
        next_message = day_0_messages.iloc[index + 1]
        
        # If current message is from employee and next message is from someone else (the lead)
        if current_message['sender'] == employee_name and next_message['sender'] != employee_name:
            employee_msg_length = len(current_message['message'])
            lead_msg_length = len(next_message['message'])
            if employee_msg_length > 0:
                percentage_diff = (lead_msg_length / employee_msg_length) * 100
                # Ensure the percentage does not exceed 100%
                percentage_diff = min(percentage_diff, 100)
                total_percentage_diff += percentage_diff
                pair_count += 1

    if pair_count == 0:
        logging.debug(f"No valid message pairs found for lead response calculation on Day 0: {day_0_date}")
        return 0

    average_lead_response = total_percentage_diff / pair_count
    return average_lead_response

def calculate_broken_chat(chat_df, employee_name, report_date):
    # Filter the messages for the given report date
    messages_on_date = chat_df[chat_df['date'].dt.date == report_date]
    
    # Check if both employee and lead have messaged on the report date
    if not messages_on_date.empty:
        employee_messages = messages_on_date[messages_on_date['sender'] == employee_name]
        lead_messages = messages_on_date[messages_on_date['sender'] != employee_name]
        
        # Ensure both the employee and lead have at least one message
        if not employee_messages.empty and not lead_messages.empty:
            # Check if the last message is from the lead
            last_message_sender = messages_on_date.iloc[-1]['sender']
            return last_message_sender != employee_name

    # If no messages or only one party messaged, return False
    return False
    # Filter messages for the target date
    daily_messages = chat_df[chat_df['date'].dt.date == target_date]
    
    # Check if the last message of the day is from the employee
    if not daily_messages.empty and daily_messages.iloc[-1]['sender'] == employee_name:
        return 'Yes'
    return 'No'

def count_missed_replies(chat_df, employee_name, target_date):
    # Filter messages for the target date
    daily_messages = chat_df[chat_df['date'].dt.date == target_date]
    
    # Check if there are any messages from the lead with no reply from the employee
    lead_messages = daily_messages[daily_messages['sender'] != employee_name]
    employee_replies = daily_messages[daily_messages['sender'] == employee_name]
    
    if not lead_messages.empty and (employee_replies.empty or (lead_messages.iloc[-1]['time'] > employee_replies.iloc[-1]['time'])):
        return 'Yes'
    return 'No'

# Function to read the chat file and return a dataframe
def read_chat_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    return pd.DataFrame([process_line(line) for line in lines if process_line(line) is not None])

# Function to extract the chat file name based on a specific pattern
def extract_chat_name(chat_file_name):
    logging.debug(f"Extracting name from chat file: {chat_file_name}")
    match = re.search(r'WhatsApp Chat with _?(.*?)(?:\(\d+\))?_?\.txt', chat_file_name)
    if match:
        extracted_name = re.sub(r'_*(?:\(\d+\))?$', '', match.group(1))
        logging.debug(f"Extracted chat name: {extracted_name}")
        return extracted_name
    logging.warning(f"No match found for chat file name: {chat_file_name}")
    return None

# Function to extract the start date from a chat file
def get_chat_start_date(chat_df):
    if not chat_df.empty:
        return chat_df['date'].min().date()
    return None

# Function to process a single chat file
def process_chat_file(file_path, report_date, main_directory, team_folder, employee_folder):
    global processed_chats
    broken_chat_count = 0
    missed_reply_count = 0
    max_time_spent = ('', '00:00:00')  # (date, time)

    chat_file_name = os.path.basename(file_path)
    logging.debug(f"Processing chat file: {chat_file_name}")

    chat_name = extract_chat_name(chat_file_name)
    logging.debug(f"Chat name extracted: {chat_name}")

    if chat_name is None:
        logging.warning(f"Chat name could not be extracted for file: {chat_file_name}")
        return None
    if chat_name in processed_chats:
        logging.info(f"Chat file already processed: {chat_name}")
        return None

    processed_chats.add(chat_name)
    logging.debug(f"Chat file added to processed list: {chat_name}")

    chat_df = read_chat_file(file_path)
    if chat_df.empty:
        logging.warning(f"Chat DataFrame is empty for file: {chat_file_name}")
        return None
    chat_start_date = get_chat_start_date(chat_df)

    # Calculate the time spent on Day 0 (report_date - 1 day)
    day_0_date = report_date - timedelta(days=1)
    day_0_time_spent = calculate_time_spent(chat_df, day_0_date, employee_folder)

    # Calculate the lead response based on text length difference for Day 0
    lead_response_percentage_day_0 = calculate_lead_response_percentage(
        chat_df, 
        employee_folder,  # Assuming this is the employee's name
        day_0_date
    )
    if lead_response_percentage_day_0 is None:
        lead_response_percentage_day_0 = 0  # Set to 0 if it's None

    day_0_date = report_date - timedelta(days=1)  # Assuming report_date is a datetime object of the target date
    broken_chat = calculate_broken_chat(chat_df, employee_folder, day_0_date)
    missed_replies_day_0 = count_missed_replies(chat_df, employee_folder, day_0_date)
    
    
    for i in range(7):  # Assuming you're checking the past 7 days
        check_date = report_date - timedelta(days=i)
        
        # Check for broken chats
        if calculate_broken_chat(chat_df, employee_folder, check_date):
            broken_chat_count += 1

        # Check for missed replies
        start_date_for_missed_replies = report_date - timedelta(days=7)
        
        missed_replies_count = count_missed_replies_last_7_days(chat_df, employee_folder, start_date_for_missed_replies)

        # Check for max time spent
        time_spent = calculate_time_spent(chat_df, check_date, employee_folder)
        if time_spent > max_time_spent[1]:
            max_time_spent = (check_date.strftime('%m-%d-%Y'), time_spent)
    
    
    
    # Calculate the time spent by students
    time_spent_student = {
    'Day 0 (Student)': calculate_time_spent_student(chat_df, report_date - timedelta(days=1), employee_folder),
    'Day 1 (Student)': calculate_time_spent_student(chat_df, report_date - timedelta(days=2), employee_folder),
    'Day 2 (Student)': calculate_time_spent_student(chat_df, report_date - timedelta(days=3), employee_folder),
    }

    total_time_spent_student = time_spent_student['Day 0 (Student)']

    broken_chat_student = is_broken_chat_student(chat_df, employee_folder, report_date)

    missed_replies_student = count_missed_replies_student(chat_df, employee_folder, report_date)
    
    missed_reply_student = check_missed_reply_student(chat_df, employee_folder, report_date)

    # Determine Day Indicator based on chat start date
    if chat_start_date:
        if (report_date - chat_start_date).days == 1:
            day_indicator = 'Day 0'
        elif (report_date - chat_start_date).days == 2:
            day_indicator = 'Day 1'
        elif (report_date - chat_start_date).days == 3:
            day_indicator = 'Day 2'
        else:
            day_indicator = 'OLD'  # For chats that don't fall into Day 0, Day 1, or Day 2

    # Calculate the time spent on each day relative to the report date
    time_spent = {}
    for i in range(1, 4):  # Start from 1 since we want Day 0 to be the day before the report date
        target_date = report_date - timedelta(days=i)
        time_spent[f'Day {i-1}'] = calculate_time_spent(chat_df, target_date, employee_folder)

    main_directory_name = os.path.basename(main_directory)

    row = {
        'Date': main_directory_name,
        'Team Folder': team_folder,
        'Employee Folder': employee_folder,
        'Chat File Name': chat_name,        # Inserting the extracted chat name
        'Day Indicator': day_indicator,
        'Total TS': day_0_time_spent,  # Use Day 0 time as the total time spent
        'LR': lead_response_percentage_day_0,  # Add the lead response here
        'Broken Chat': 'Yes' if broken_chat else 'No',
        'Missed Replies (BY Officer)': missed_replies_day_0,
        'TCBC (Employee)': broken_chat_count,
        'TCMR (Employee)': missed_replies_count,
        'Date of Max time': max_time_spent[0],
        **time_spent,
        'Total Time Spent (Student)': total_time_spent_student,
        'Broken Chat (Student)': broken_chat_student,
        'Missed Replies (Student)': missed_replies_student,
    }
    logging.debug(f"Row created for chat: {row}")
    return row


# Main directory path construction and report date setting
report_date_str = '11-24-2023'  # Replace with the desired report date in MM-DD-YYYY format
report_date = datetime.strptime(report_date_str, '%m-%d-%Y').date()
main_directory = 'C:\\ChatAnalysisProject'  # Replace with your base directory path
main_directory_path = os.path.join(main_directory, report_date_str)

# Function to navigate through the directory structure and process all chat files
def process_team_folders(main_directory, report_date):
    all_data = []
    for team_folder in os.listdir(main_directory):
        team_path = os.path.join(main_directory, team_folder)
        if not os.path.isdir(team_path):
            continue
        for employee_folder in os.listdir(team_path):
            employee_path = os.path.join(team_path, employee_folder)
            if not os.path.isdir(employee_path):
                continue
            for chat_file in os.listdir(employee_path):
                chat_file_path = os.path.join(employee_path, chat_file)
                row = process_chat_file(chat_file_path, report_date, main_directory, team_folder, employee_folder)
                if row:
                    all_data.append(row)
                    logging.debug(f"Row appended for chat file: {chat_file}")
    df = pd.DataFrame(all_data)
    logging.debug(f"DataFrame constructed with {len(df)} rows")
    return df

# Process all team folders and chats based on the report date
all_chats_df = process_team_folders(main_directory_path, report_date)


# Save to a CSV file
csv_file_path = 'C:\ChatAnalysisProject/chat_data8.csv'  # Define your desired path and file name
all_chats_df.to_csv(csv_file_path, index=False)
print(f"DataFrame saved as CSV at {csv_file_path}")
# Display the result
print(all_chats_df)
