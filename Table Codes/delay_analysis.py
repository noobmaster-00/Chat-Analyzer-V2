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

            is_person = sender is not None and re.match(r'^[+\d\s-]+$', sender) is None

            # Calculate delay
            delay = False
            if is_person and last_non_person_time:
                diff = date_time - last_non_person_time
                delay = diff.total_seconds() > 900  # 15 minutes in seconds

            chat_data.append((date_time, sender, is_person, delay))

            if not is_person:
                last_non_person_time = date_time

    return chat_data

# Function to create a template dataframe
def create_template_dataframe():
    times = [datetime.datetime(2000, 1, 1, 0, 0) + datetime.timedelta(minutes=1 * i) for i in range(1440)]
    intervals = [time.strftime('%I:%M %p') for time in times]
    df = pd.DataFrame(index=intervals)
    return df

def populate_dataframe(df, parsed_data, start_column_index):
    new_columns = {}  # Dictionary to hold new data before concatenation

    for entry in parsed_data:
        date_time, sender, is_person, delay = entry
        interval_index = min((date_time.hour * 60 + date_time.minute) // 1, 1439)
        interval = df.index[interval_index]

        # Initialize columns in new_columns dictionary if not exist
        if (start_column_index not in new_columns):
            new_columns[start_column_index] = pd.Series(0, index=df.index)
        if (start_column_index + 1 not in new_columns):
            new_columns[start_column_index + 1] = pd.Series(0, index=df.index)
        if (start_column_index + 2 not in new_columns):
            new_columns[start_column_index + 2] = pd.Series(False, index=df.index)  # For delay column

        # Populate the new_columns dictionary
        if is_person:
            new_columns[start_column_index].at[interval] = 1
            new_columns[start_column_index + 2].at[interval] = delay  # Set delay flag
        else:
            new_columns[start_column_index + 1].at[interval] = 1

    # Concatenate new columns to the DataFrame at once
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


print("analysis complete. Generating Graphs...")


# Function to create bar and trend graphs for each person
def create_graphs(df, person_identifier, base_directory):
    graph_directory = os.path.join(base_directory, "Graphs")
    os.makedirs(graph_directory, exist_ok=True)

    # Sum the values across all even columns for each minute
    person_chat_activity = df.iloc[:, 0::2].sum(axis=1)
    trend_data = df.iloc[:, 1::2].sum(axis=1)

    # Find the first and last non-zero indices for chats
    non_zero_indices = person_chat_activity[person_chat_activity > 0].index
    first_chat_time = non_zero_indices[0] if not non_zero_indices.empty else df.index[0]
    last_chat_time = non_zero_indices[-1] if not non_zero_indices.empty else df.index[-1]

    print(f"Generating graph for {person_identifier}")  # Debug line
    fig, ax = plt.subplots(figsize=(30, 10))  # Increased figure size for more stretch
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')

    # Set the colors of the tick labels
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')

    # If you have a legend, you can set the text color using:
    legend = ax.legend()
    for text in legend.get_texts():
        text.set_color('white')

    # Change the line and bar colors to something that would show up on a black background
    ax.bar(df.index, person_chat_activity, color='red', width=0.5, label=f'Person {person_identifier}')
    ax.plot(df.index, trend_data, color='white', linewidth=1, linestyle='-', label='Trend')
    ax.scatter(df.index[trend_data > 0], trend_data[trend_data > 0], color='white', s=2)  # Scatter plot for non-zero trend points

    # Rotate x-axis labels to prevent overlap and increase label font sizes
    plt.xticks(rotation=90, fontsize=8)
    plt.yticks(fontsize=10)

    # Set x-axis to show the range from the first chat to the last chat
    ax.set_xlim(first_chat_time - 1, last_chat_time + 1)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(96))  # Set locator for 15-minute intervals

    # Set y-axis dynamic range based on the maximum chat activity with a buffer
    max_chats = max(person_chat_activity.max(), trend_data.max())
    ax.set_ylim(0, max_chats + 1)  # Adjust y-axis limit based on maximum chat activity plus a buffer

    # Increasing font size for labels and title
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('Number of Chats', fontsize=12)
    ax.set_title(f'Chat Activity for {person_identifier}', fontsize=14)
    ax.legend()

    # Saving the graph
    graph_file_name = f"{person_identifier}.png"
    plt.savefig(os.path.join(graph_directory, graph_file_name), format='png', dpi=300, bbox_inches='tight')  # Save with tight bounding box
    print(f"Graph saved as {graph_file_name}")  # Debug line

    plt.close(fig)


# Main script
date_directory = "C:\\Users\\mauriceyeng\\Python\\Daily-Reports\\Test\\V1_maurice\\dates"
chat_files = list_chat_files(date_directory)
person_dataframes = process_person_chats(chat_files)

# Generating graphs for each DataFrame
for person_identifier, df in person_dataframes.items():
    create_graphs(df, person_identifier, date_directory)
