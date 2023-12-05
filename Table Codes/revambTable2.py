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

def process_line_for_delay(line):
    pattern = r'(\d{2}/\d{2}/\d{2}), (\d{1,2}:\d{2}\s?[APMapm]{2}) - (.*?): (.*)'
    match = re.match(pattern, line)
    if match:
        date_str, time_str, sender, message = match.groups()
        datetime_str = date_str + ' ' + time_str
        datetime_obj = datetime.strptime(datetime_str, '%d/%m/%y %I:%M %p')
        return {'datetime': datetime_obj, 'sender': sender, 'message': message}
    else:
        return None

# Function to read the chat file specifically for delay calculation
def read_chat_file_for_delay(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    concatenated_lines = []
    current_message = ""
    date_pattern = re.compile(r'^\d{2}/\d{2}/\d{2}, \d{1,2}:\d{2}\s?[APMapm]{2} - ')

    for line in lines:
        if date_pattern.match(line):
            if current_message:
                concatenated_lines.append(current_message)
            current_message = line.rstrip()
        else:
            # Append this line to the current message, if it's not empty
            if current_message:
                current_message += " " + line.strip()
    if current_message:
        concatenated_lines.append(current_message)

    return pd.DataFrame([process_line_for_delay(line) for line in concatenated_lines if process_line_for_delay(line) is not None])

# The process_line_for_delay function remains the same
       
    
def calculate_time_spent_student(chat_df, target_date, employee_name):
    student_messages = chat_df[(chat_df['date'].dt.date == target_date) & (chat_df['sender'] != employee_name)]
    total_chars = student_messages['message'].str.len().sum()
    time_spent_seconds = (total_chars / 10) * 5
    return strfdelta(timedelta(seconds=time_spent_seconds)) 

def format_delay_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours} hr {minutes} mins"
    else:
        return f"{minutes} mins"

def calculate_employee_delay(chat_df, employee_name, target_date):
    delays = []
    delay_times = []
    messages_for_reference = []

    last_student_message_time = None
    employee_responded_after_student = False

    delay_counter = 1

    for index, row in chat_df.iterrows():
        # Ensure datetime is correctly formatted
        row_date = row['datetime'].date()

        if row_date != target_date:
            continue

        if row['sender'] != employee_name:
            last_student_message_time = row['datetime']
            employee_responded_after_student = False
        elif row['sender'] == employee_name and last_student_message_time is not None and not employee_responded_after_student:
            time_diff = row['datetime'] - last_student_message_time

            if time_diff > timedelta(minutes=15):
                formatted_time = row['datetime'].strftime('%d %b %Y %I:%M%p')
                delays.append(f"{delay_counter} - {formatted_time}")
                delay_counter += 1

                delay_times.append(format_delay_time(time_diff.seconds))

                start_index = max(0, index - 5)
                end_index = min(index + 5, len(chat_df))
                context_messages = chat_df.iloc[start_index:end_index]

                formatted_context_messages = [f"{idx+1} - {message_row['datetime'].strftime('%d %b %Y %I:%M%p')} - {message_row['sender']}: {message_row['message']}" for idx, message_row in context_messages.iterrows()]
                formatted_message = "\n".join(formatted_context_messages)
                messages_for_reference.append(formatted_message)

            employee_responded_after_student = True

    # Combine the lists into multiline strings
    delays_str = "\n".join(delays)
    delay_times_str = "\n".join(delay_times)
    messages_for_reference_str = "\n".join(messages_for_reference)

    return delays_str, delay_times_str, messages_for_reference_str

def is_broken_chat_student(chat_df, employee_name, target_date):
    # Adjust for the previous day
    previous_day = target_date - timedelta(days=1)

    # Filter messages for the previous day
    daily_messages = chat_df[chat_df['date'].dt.date == previous_day]

    # Check if both the employee and the student had at least one text on that day
    if daily_messages.empty:
        return 'No'  # No conversation happened on this day

    employee_messages = daily_messages[daily_messages['sender'] == employee_name]
    student_messages = daily_messages[daily_messages['sender'] != employee_name]

    # Check if both parties have sent at least one message
    if employee_messages.empty or student_messages.empty:
        return 'No'  # One of the parties did not send any message

    # Check the sender of the last message of the day
    last_message_sender = daily_messages.iloc[-1]['sender']

    # If the last message is from the employee, it's a broken chat by the student
    if last_message_sender == employee_name:
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

def count_missed_replies_studentt(chat_df, employee_name, target_date):
    previous_day = target_date - timedelta(days=1)
    #print(f"Checking for missed replies on: {previous_day}")

    daily_messages = chat_df[chat_df['date'].dt.date == previous_day]
    
    employee_messages = daily_messages[daily_messages['sender'] == employee_name]
    student_messages = daily_messages[daily_messages['sender'] != employee_name]

    #print(f"Employee messages count: {len(employee_messages)}")
    #print(f"Student messages count: {len(student_messages)}")

    # Check if there are messages from the employee but none from the student
    if not employee_messages.empty and student_messages.empty:
        #print("Missed reply found.")
        return 'Yes'
    
    #print("No missed reply.")
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
def calculate_time_spent(chat_df, target_date, employee_name, team_folder):
    daily_messages = chat_df[(chat_df['date'].dt.date == target_date) & (chat_df['sender'] == employee_name)]

    if daily_messages.empty:
        return '00:00:00'

    total_time_spent_seconds = 0

    for index, row in daily_messages.iterrows():
        message = row['message']
        total_chars = len(message)

        if team_folder == "KAM" and total_chars > 700:
            time_spent_seconds = 5  # Cap at 5 seconds for long messages in KAM team folder
        else:
            time_spent_seconds = total_chars * 0.2  # Assuming 0.2 seconds per character

        total_time_spent_seconds += time_spent_seconds

        # Optional: Debug print
        #print(f"New Chat Found in {team_folder}")
        #print(f"Message Length: '{total_chars}'")
        #print(f"Message: '{message}' - Time Spent: {time_spent_seconds} seconds")

    time_spent_timedelta = timedelta(seconds=total_time_spent_seconds)
    formatted_time_spent = strfdelta(time_spent_timedelta)

    return formatted_time_spent

def strfdelta(tdelta):
    hours, remainder = divmod(tdelta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"   

def calculate_lead_response(chat_df, employee_name, target_date):
    """
    Calculates the lead response based on the number of texts exchanged between the employee and others (non-employee).
    - If only the employee sent messages, the response is 100%.
    - If only non-employees sent messages, the response is 0%.
    - Otherwise, it's the ratio of the employee's texts to the total texts, constrained between 1% and 99%.
    """
    # Filter messages for the target date
    daily_messages = chat_df[chat_df['date'].dt.date == target_date]
    
    # Check if there are any messages from the employee and others on the target date
    employee_messages = daily_messages[daily_messages['sender'] == employee_name]
    non_employee_messages = daily_messages[daily_messages['sender'] != employee_name]

    # If only the employee sent messages
    if not employee_messages.empty and non_employee_messages.empty:
        return 0

    # If only non-employees sent messages
    if employee_messages.empty and not non_employee_messages.empty:
        return 100

    # If both the employee and non-employees have sent messages
    if not employee_messages.empty and not non_employee_messages.empty:
        num_texts_employee = len(employee_messages)
        num_texts_non_employee = len(non_employee_messages)
        total_texts = num_texts_employee + num_texts_non_employee
        lead_response = (num_texts_employee / total_texts) * 100
        return max(min(lead_response, 99), 1)

    # If neither the employee nor non-employees sent messages
    return 0



def calculate_broken_chat_within_working_hrs(chat_df, employee_name, report_date, team_folder):
    # Adjust working hours based on team folder
    if team_folder == 'EWYL':
        # KAM Team working hours: 7:30 AM to 4:00 PM
        work_start_time = datetime(report_date.year, report_date.month, report_date.day, 7, 30, 0)
        work_end_time = datetime(report_date.year, report_date.month, report_date.day, 16, 30, 0)
    else:
        # Default working hours for other teams: 12:00 AM to 12:00 PM
        work_start_time = datetime(report_date.year, report_date.month, report_date.day, 0, 0, 0)
        work_end_time = datetime(report_date.year, report_date.month, report_date.day, 23, 59, 0)

    # Filter the messages for the given report date
    messages_on_date = chat_df[chat_df['datetime'].dt.date == report_date.date()]

    # Check if both employee and lead have messaged on the report date
    if not messages_on_date.empty:
        employee_messages = messages_on_date[messages_on_date['sender'] == employee_name]
        lead_messages = messages_on_date[messages_on_date['sender'] != employee_name]
        last_message_sender = messages_on_date.iloc[-1]['sender']
        # Ensure both the employee and lead have at least one message
        if not employee_messages.empty and not lead_messages.empty:
            # Get the time of the last message from the lead
            last_lead_message_time = lead_messages.iloc[-1]['datetime']

            # Check if the last message is from the lead and within working hours
            if last_message_sender != employee_name and (work_start_time <= last_lead_message_time <= work_end_time):
                return 'Yes'  # Broken chat if last message from the lead is within working hours
            else:
                return 'No'  # Not a broken chat if last message from the lead is outside working hours or from the employee

    # If no messages or only one party messaged, return 'No'
    return 'No'

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

    

def missed_replies_employee(chat_df, employee_name, target_date):
    # Filter messages for the target date
    daily_messages = chat_df[chat_df['date'].dt.date == target_date]
    
    # Check if there are any messages from the student
    student_messages = daily_messages[daily_messages['sender'] != employee_name]
    
    # Check if there are any messages from the employee
    employee_messages = daily_messages[daily_messages['sender'] == employee_name]
    
    # If there are student messages but no employee messages, consider it a missed reply
    if not student_messages.empty and employee_messages.empty:
        return 'Yes'
    
    return 'No'

def missed_replies_employee_after_working_hrs(chat_df, employee_name, target_date, team_folder):
    # Check if the team folder is 'KAM Team' to define different working hours
    if team_folder == 'EWYL':
        # KAM Team working hours: 7:30 AM to 4:00 PM
        work_start_time = datetime(target_date.year, target_date.month, target_date.day, 7, 30, 0)
        work_end_time = datetime(target_date.year, target_date.month, target_date.day, 16, 30, 0)
    else:
        # Default working hours for other teams: 12:00 AM to 12:00 PM
        work_start_time = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)
        work_end_time = datetime(target_date.year, target_date.month, target_date.day, 23, 59, 0)

    # Ensure target_date is a datetime object
    if not isinstance(target_date, datetime):
        raise ValueError("target_date must be a datetime object")

    # Filter messages for the target date using 'datetime' column
    daily_messages = chat_df[chat_df['datetime'].dt.date == target_date.date()]
    
    # Check if there are any messages from the student
    student_messages = daily_messages[daily_messages['sender'] != employee_name]
    
    # Check if there are any messages from the employee
    employee_messages = daily_messages[daily_messages['sender'] == employee_name]

    # If there are student messages but no employee messages
    if not student_messages.empty and employee_messages.empty:
        print(f"ENTER THE LOOP:{student_messages}")
        # Check if any student message is within working hours
        for _, row in student_messages.iterrows():
            message_time = row['datetime']
            if work_start_time <= message_time <= work_end_time:
                return 'Yes'  # Missed reply within working hours
        return 'No'  # All student messages are outside working hours

    return 'No'

# Function to read the chat file and return a dataframe
def read_chat_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    concatenated_lines = []
    current_message = ""
    date_pattern = re.compile(r'^\d{2}/\d{2}/\d{2}, \d{1,2}:\d{2}\s?[APMapm]{2} - ')

    for line in lines:
        if date_pattern.match(line):
            if current_message:
                concatenated_lines.append(current_message)
            current_message = line.rstrip()
        else:
            # Append this line to the current message, if it's not empty
            if current_message:
                current_message += " " + line.strip()
    if current_message:
        concatenated_lines.append(current_message)

    return pd.DataFrame([process_line(line) for line in concatenated_lines if process_line(line) is not None])

# process_line function remains the same


# Function to extract the chat file name based on a specific pattern
def extract_chat_name(chat_file_name):
    #logging.debug(f"Extracting name from chat file: {chat_file_name}")
    match = re.search(r'WhatsApp Chat with _?(.*?)(?:\(\d+\))?_?\.txt', chat_file_name)
    if match:
        extracted_name = re.sub(r'_*(?:\(\d+\))?$', '', match.group(1))
        #logging.debug(f"Extracted chat name: {extracted_name}")
        return extracted_name
    #logging.warning(f"No match found for chat file name: {chat_file_name}")
    return None

# Function to calculate the total count of missed replies by the student for the last N days
def calculate_total_count_missed_replies_student(chat_df, employee_name, num_days):
    total_count = 0

    # Iterate over the last N days
    for i in range(num_days):
        target_date = report_date - timedelta(days=i)
        count = count_missed_replies_student(chat_df, employee_name, target_date)
        total_count += count

    return total_count

# Function to extract the start date from a chat file
def get_chat_start_date(chat_df):
    if not chat_df.empty:
        #logging.debug(f"Extracted chat name: {chat_df['date'].min().date()}")
        return chat_df['date'].min().date()
    return None

# Function to process a single chat file
def process_chat_file(file_path, report_date, main_directory, team_folder, employee_folder):
    global processed_chats
    broken_chat_count = 0
    missed_reply_count = 0
    max_time_spent = ('', '00:00:00')  # (date, time)

    chat_file_name = os.path.basename(file_path)
    #logging.debug(f"Processing chat file: {chat_file_name}")

    chat_name = extract_chat_name(chat_file_name)
    #logging.debug(f"Chat name extracted: {chat_name}")



    

    if chat_name is None:
        #logging.warning(f"Chat name could not be extracted for file: {chat_file_name}")
        return None
    if chat_name in processed_chats:
        #logging.info(f"Chat file already processed: {chat_name}")
        return None

    processed_chats.add(chat_name)
    #logging.debug(f"Chat file added to processed list: {chat_name}")

    chat_df = read_chat_file(file_path)
    if chat_df.empty:
        #logging.warning(f"Chat DataFrame is empty for file: {chat_file_name}")
        return None
    chat_start_date = get_chat_start_date(chat_df)

    # Use read_chat_file_for_delay specifically for delay calculations
    chat_df_for_delay = read_chat_file_for_delay(file_path)
    if chat_df_for_delay.empty:
        return None

    
    target_date = report_date - timedelta(days=1)

    # Call the function with the target date
    delays, delay_times, messages_for_reference = calculate_employee_delay(chat_df_for_delay, employee_folder, target_date)
    



    # Calculate the time spent on Day 0 (report_date - 1 day)
    day_0_date = report_date - timedelta(days=1)
    day_0_time_spent = calculate_time_spent(chat_df, day_0_date, employee_folder,team_folder)
    #day_0_time_spent = timedelta(hours=int(day_0_time_spent.split(':')[0]), minutes=int(day_0_time_spent.split(':')[1]), seconds=int(day_0_time_spent.split(':')[2]))
    # Calculate the lead response based on text length difference for Day 0
    lead_response_day_0 = calculate_lead_response(chat_df, employee_folder, day_0_date)
     
    day_0_date = report_date - timedelta(days=1)  # Assuming report_date is a datetime object of the target date
    broken_chat = calculate_broken_chat(chat_df, employee_folder, day_0_date)
    missed_replies_day_0 = missed_replies_employee(chat_df, employee_folder, day_0_date)

    # Get the current datetime
    today_datetime = datetime.now()

    # Get today's date with time part (assuming start of the day as default)
    today_date_1 = today_datetime.replace(hour=0, minute=0, second=0, microsecond=0)

    # If today_date.weekday() logic remains the same
    # ...

    # Now, when you calculate target_date, it remains a datetime object
    target_date_1 = today_date_1 - timedelta(days=1)


    Actual_missed_Reply = missed_replies_employee_after_working_hrs(chat_df_for_delay, employee_folder, target_date_1,team_folder)
    Actual_broken_chat = calculate_broken_chat_within_working_hrs(chat_df_for_delay, employee_folder, target_date_1,team_folder)
    total_count_missed_reply_student = calculate_total_count_missed_replies_student(chat_df, employee_folder, 14)
    


    
    for i in range(7):  # Assuming you're checking the past 7 days
        check_date = report_date - timedelta(days=i)
        
        # Check for broken chats
        if calculate_broken_chat(chat_df, employee_folder, check_date):
            broken_chat_count += 1

        # Check for missed replies
        start_date_for_missed_replies = report_date - timedelta(days=7)
        
        missed_replies_count = count_missed_replies_last_7_days(chat_df, employee_folder, start_date_for_missed_replies)

        # Check for max time spent
        time_spent = calculate_time_spent(chat_df, check_date, employee_folder,team_folder)
        if time_spent > max_time_spent[1]:
            max_time_spent = (check_date.strftime('%m-%d-%Y'), time_spent)
    
    
    
    # Calculate the time spent by students
    time_spent_student = {
    'Day 0 (Student)': calculate_time_spent_student(chat_df, report_date - timedelta(days=1), employee_folder),
    'Day 1 (Student)': calculate_time_spent_student(chat_df, report_date - timedelta(days=2), employee_folder),
    'Day 2 (Student)': calculate_time_spent_student(chat_df, report_date - timedelta(days=3), employee_folder),
    }
    
    # Inside the process_chat_file function, after calculating day_0_time_spent:
    day_0_date = report_date - timedelta(days=1)
    day_1_date = report_date - timedelta(days=2)
    day_2_date = report_date - timedelta(days=3)

    # Calculate time spent by student for Day 0, Day 1, and Day 2
    time_spent_student_day_0 = calculate_time_spent_student(chat_df, day_0_date, employee_folder)
    time_spent_student_day_1 = calculate_time_spent_student(chat_df, day_1_date, employee_folder)
    time_spent_student_day_2 = calculate_time_spent_student(chat_df, day_2_date, employee_folder)



    total_time_spent_student = time_spent_student['Day 0 (Student)']

    broken_chat_student = is_broken_chat_student(chat_df, employee_folder, report_date)

    mmissed_reply_student = count_missed_replies_studentt(chat_df, employee_folder, report_date)

    # Calculate the time spent on each day relative to the report date
    time_spent = {}
    for i in range(1, 4):  # Start from 1 since we want Day 0 to be the day before the report date
        target_date = report_date - timedelta(days=i)
        time_spent[f'Day {i-1}'] = calculate_time_spent(chat_df, target_date, employee_folder,team_folder)
    
    target_date_for_chat_start_Date = report_date - timedelta(days=1)
    day_indicator_employee = (target_date_for_chat_start_Date - chat_start_date).days
    #logging.debug(f"day indicator employee: {day_indicator_employee}")
    # Determine Day Indicator based on chat start date
    if chat_start_date:
        if (target_date_for_chat_start_Date - chat_start_date).days == 0:
          
            day_indicator = 'Day 0'
        elif (target_date_for_chat_start_Date - chat_start_date).days == 1:
            
            day_indicator = 'Day 1'
        elif (target_date_for_chat_start_Date - chat_start_date).days == 2:
            
            day_indicator = 'Day 2'

        elif (target_date_for_chat_start_Date - chat_start_date).days == 3:
            
            day_indicator = 'OLD'

        else:
            day_indicator = 'OLD'  # For chats that don't fall into Day 0, Day 1, or Day 2

    

    main_directory_name = os.path.basename(main_directory)

    row = {
        'Date': main_directory_name,
        'Team Folder': team_folder,
        'Employee Folder': employee_folder,
        'Chat File Name': chat_name,        # Inserting the extracted chat name
        'Day Indicator': day_indicator,
        'Total_Time_Spent_Employee': day_0_time_spent,  # Use Day 0 time as the total time spent
        'LR': lead_response_day_0,  # Add the lead response here
        'Broken Chat(Employee)': 'Yes' if broken_chat else 'No',
        'Missed Replies (Employee)': missed_replies_day_0,
        'Count_Broken_Chat_Employee (Employee)': broken_chat_count,
        'Count_Missed_Replies_Missed_Replies (Employee)': missed_replies_count,
        'Date of Max time': max_time_spent[0],
        **time_spent,
        'Total Time Spent (Student)': total_time_spent_student,
        'Broken Chat (Student)': broken_chat_student,
        'Missed Replies (Student)': mmissed_reply_student,
        'Day_0_Time_Spent_Student': time_spent_student_day_0,  # Add time spent for Day 0
        'Day_1_Time_Spent_Student': time_spent_student_day_1,  # Add time spent for Day 1
        'Day_2_Time_Spent_Student': time_spent_student_day_2,
        'Total_Count_Missed_Reply_Chat_Student' : total_count_missed_reply_student,
        'Employee Delays': delays,
        'Delay Durations': delay_times,
        'Messages for Reference': messages_for_reference,
        'Actual Missed Reply from Employee': Actual_missed_Reply,
        'Actual Broken Chat from Employee' : Actual_broken_chat,
    }
    #logging.debug(f"Row created for chat: {row}")
    return row

# Main directory path construction and report date setting
# Main directory path construction and report date setting
local_date_format = '%Y-%m-%d'  # Adjust this to your local date format
main_directory = 'C:\\ChatAnalysisProject'  # Replace with your base directory path

# Get today's date
today_date = datetime.now().date()

# Check the day of the week
if today_date.weekday() in range(1, 6):  # Tuesday to Saturday
    report_date = today_date
else:  # Monday
    # You can adjust the number of days to subtract based on your specific requirements
    report_date = today_date - timedelta(days=1)
    logging.debug(f"Report Date: {report_date}")
report_date_str_local = report_date.strftime(local_date_format)
main_directory_path = os.path.join(main_directory, report_date_str_local)

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
    #logging.debug(f"DataFrame constructed with {len(df)} rows")
    return df

# Process all team folders and chats based on the report date
all_chats_df = process_team_folders(main_directory_path, report_date)


# Save to a CSV file
csv_file_path = 'C:\ChatAnalysisProject/chat_data14.csv'  # Define your desired path and file name
all_chats_df.to_csv(csv_file_path, index=False)
#print(f"DataFrame saved as CSV at {csv_file_path}")
# Display the result
#print(all_chats_df)