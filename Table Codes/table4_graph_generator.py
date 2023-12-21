import os
import pandas as pd
import datetime
import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

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

def parse_chat_file(file_path, expected_date_minus_one):
    chat_data = []
    last_non_person_time = None  # Tracks the time of the last non-person message

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

            if sender is not None and re.match(r'^[+\d\s-]+$', sender) is None:
                message_type = 'person'
            else:
                message_type = 'other'

            # Calculate delay
            delay = False
            if message_type == 'person' and last_non_person_time:
                diff = date_time - last_non_person_time
                delay = diff.total_seconds() > 900  # 15 minutes in seconds

            chat_data.append((date_time, sender, message_type, delay))

            if message_type == 'other':
                last_non_person_time = date_time

    return chat_data

def create_template_dataframe():
    times = [datetime.datetime(2000, 1, 1, 0, 0) + datetime.timedelta(minutes=1 * i) for i in range(1440)]
    intervals = [time.strftime('%I:%M %p') for time in times]
    df = pd.DataFrame(index=intervals)
    return df

def populate_dataframe(df, parsed_data, start_column_index):
    new_columns = {}

    for entry in parsed_data:
        date_time, sender, message_type, delay = entry
        interval_index = min((date_time.hour * 60 + date_time.minute) // 1, 1439)
        interval = df.index[interval_index]

        if start_column_index not in new_columns:
            new_columns[start_column_index] = pd.Series(0, index=df.index)  # For 'person'
        if start_column_index + 1 not in new_columns:
            new_columns[start_column_index + 1] = pd.Series(0, index=df.index)  # For 'other'
        if start_column_index + 2 not in new_columns:
            new_columns[start_column_index + 2] = pd.Series(False, index=df.index)  # For delay column

        if message_type == 'person':
            new_columns[start_column_index].at[interval] = 1
        elif message_type == 'other':
            new_columns[start_column_index + 1].at[interval] = 1

        new_columns[start_column_index + 2].at[interval] = delay  # Set delay flag

    df = pd.concat([df, pd.DataFrame(new_columns)], axis=1)
    return df, start_column_index + 3

def process_person_chats(chat_files):
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
            start_column_index = 0
        else:
            if not dataframes[key].columns.empty:
                start_column_index = max(dataframes[key].columns) + 1
            else:
                start_column_index = 0

        parsed_data = parse_chat_file(file, expected_date_minus_one)
        dataframes[key], start_column_index = populate_dataframe(dataframes[key], parsed_data, start_column_index)

    return dataframes

def create_graphs(df, person_identifier, base_directory):
    graph_directory = os.path.join(base_directory, "Graphs")
    os.makedirs(graph_directory, exist_ok=True)

    # Sum the values for 'person' and 'other' messages for each minute
    person_chat_activity = df.iloc[:, 0::3].sum(axis=1)
    other_chat_activity = df.iloc[:, 1::3].sum(axis=1)
    
    # Find the first and last non-zero indices for chats
    non_zero_indices = person_chat_activity[person_chat_activity > 0].index
    first_chat_time = non_zero_indices[0] if not non_zero_indices.empty else df.index[0]
    last_chat_time = non_zero_indices[-1] if not non_zero_indices.empty else df.index[-1]

    # Creating the plot
    fig, ax = plt.subplots(figsize=(30, 10))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    ax.xaxis.label.set_color('black')
    ax.yaxis.label.set_color('black')
    ax.title.set_color('black')
    ax.tick_params(axis='x', colors='black')
    ax.tick_params(axis='y', colors='black')


    # Plot the bar for 'person' messages
    ax.bar(df.index, person_chat_activity, color='lime', width=2, label='Counselor')

    # Plot the bar for 'other' messages, stacked on top of 'person' messages
    #ax.bar(df.index, other_chat_activity, color='darkgreen', width=1, label='Other Messages', bottom=person_chat_activity)
    ax.plot(df.index, other_chat_activity, color='darkgreen', linestyle=':', label='Student')
    # Draw white lines for the axes
    ax.axhline(0, color='black', linewidth=3)  # Changed color to black
    ax.axvline(first_chat_time, color='white', linewidth=3)
    #ax.axvline(df.index[0], color='black', linewidth=3)  # Changed color to black


    # Rotate x-axis labels to prevent overlap and increase label font sizes
    plt.xticks(rotation=90, fontsize=12)

    # Set y-axis to show every integer tick
    plt.yticks(np.arange(0, 11, 1), fontsize=12)

    # Set x-axis to show the range from the first chat to the last chat
    ax.set_xlim(first_chat_time, last_chat_time)
    #ax.set_xlim(df.index[0], df.index[-1])
    ax.xaxis.set_major_locator(ticker.MaxNLocator(96))  # Set locator for 15-minute intervals

    # Set y-axis dynamic range based on the maximum chat activity with a buffer
    max_activity = max(person_chat_activity.max(), other_chat_activity.max())
    ax.set_ylim(0, 11)

    # Increasing font size for labels and title
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('Number of Chats', fontsize=12)
    ax.set_title(f'Chat Activity for {person_identifier}', fontsize=14)

    # Create and set the legend
    legend = ax.legend(facecolor='lightgray', edgecolor='black', fontsize=12, fancybox=True)
    for text in legend.get_texts():
        text.set_color('black')
        text.set_weight('bold')

    # Saving the graph
    graph_file_name = f"{person_identifier}.png"
    plt.savefig(os.path.join(graph_directory, graph_file_name), format='png', dpi=300, bbox_inches='tight')
    print(f"Graph saved as {graph_file_name}")

    plt.close(fig)


# Main script
date_directory = "C:\\Users\\aditya\\OneDrive\\Documents\\Chat-Analyzer-V2"
chat_files = list_chat_files(date_directory)
person_dataframes = process_person_chats(chat_files)

for person_identifier, df in person_dataframes.items():
    create_graphs(df, person_identifier, date_directory)