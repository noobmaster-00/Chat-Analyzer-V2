import os
import re
from datetime import datetime
import logging
import json

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_settings():
    try:
        with open('settings.json', 'r') as file:
            settings = json.load(file)
            logging.info("Settings file read successfully.")
            return settings
    except Exception as e:
        logging.error(f"Error reading settings: {e}")
        return {}

def normalize_chat_file_name(chat_file):
    normalized_name = re.sub(r' ?\(\d+\)\.txt$', '.txt', chat_file)
    logging.info(f"Normalized file name: {normalized_name}")
    return normalized_name

def is_duplicate_file(folder_path, normalized_file_name):
    for existing_file in os.listdir(folder_path):
        if normalize_chat_file_name(existing_file) == normalized_file_name:
            logging.info(f"Duplicate file found: {normalized_file_name}")
            return True
    logging.info(f"No duplicates found for: {normalized_file_name}")
    return False

def save_chat(chat, sender_names, chat_file):
    for sender_name in sender_names:
        folder_name = sender_name
        folder_path = f'filtered_chats/{folder_name}'
        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path)
                logging.info(f"Created folder: {folder_path}")
            except Exception as e:
                logging.error(f"Error creating folder {folder_path}: {e}")
                continue

        normalized_file_name = normalize_chat_file_name(chat_file)
        if is_duplicate_file(folder_path, normalized_file_name):
            logging.info(f"Skipping duplicate chat file {chat_file} for {sender_name}")
            continue

        file_path = f'{folder_path}/{normalized_file_name}'
        try:
            with open(file_path, 'w', encoding='utf-8-sig') as file:
                for line in chat:
                    # Check if the line contains a date
                    match = re.search(r'(\d{2}/\d{2}/\d{2}), \d{1,2}:\d{2} - ', line)
                    if match:
                        date_str = match.group(1)
                        try:
                            date_obj = datetime.strptime(date_str, '%m/%d/%y')
                            formatted_date = date_obj.strftime('%d/%m/%y')
                            line = line.replace(date_str, formatted_date, 1)
                        except ValueError:
                            logging.warning(f"Date format error in line: {line.strip()}")

                    file.write(line)
                logging.info(f"Saved filtered chat to {file_path}")
        except Exception as e:
            logging.error(f"Error saving chat to {file_path}: {e}")


def main():
    try:
        settings = read_settings()
        name_list = set(settings.get('name_list', []))
        chat_file_path = settings.get('chat_file_path', 'C:\\Users\\ayush\\Documents\\Chat-Analyzer-V2\\ChatSeparatorltd\\')

        shared_chats_folder = 'shared_chats'
        if not os.path.exists(shared_chats_folder):
            os.makedirs(shared_chats_folder)
            logging.info(f"Created '{shared_chats_folder}' directory")

        if not os.path.exists('filtered_chats'):
            os.makedirs('filtered_chats')
            logging.info("Created 'filtered_chats' directory")

        chat_files = os.listdir(chat_file_path)
        logging.info(f"Found {len(chat_files)} files in the directory")

        for chat_file in chat_files:
            if not chat_file.endswith('.txt'):
                logging.info(f"Skipping {chat_file} as it's not a .txt file")
                continue

            logging.info(f"Processing {chat_file}")
            try:
                with open(f'{chat_file_path}{chat_file}', 'r', encoding='utf-8-sig') as file:
                    chat = file.readlines()

                for line in reversed(chat):
                    date_match = re.search(r'(\d{2}/\d{2}/\d{2}), \d{1,2}:\d{2}(?:\u202f)?(?:[ap]m)? - (.*?): ', line)
                    if date_match:
                        date, sender = date_match.groups()
                        if sender in name_list:
                            # Check for other senders on the same date
                            other_senders = {sender}
                            for other_line in chat:
                                other_date_match = re.search(r'(\d{2}/\d{2}/\d{2}), \d{1,2}:\d{2}(?:\u202f)?(?:[ap]m)? - (.*?): ', other_line)
                                if other_date_match:
                                    other_date, other_sender = other_date_match.groups()
                                    if other_date == date and other_sender in name_list and other_sender != sender:
                                        other_senders.add(other_sender)
                            
                            save_chat(chat, other_senders, chat_file)

                            if len(other_senders) > 1:
                                # Save in shared_chats folder if the chat involves communication between two senders
                                shared_file_path = f'{shared_chats_folder}/{normalize_chat_file_name(chat_file)}'
                                with open(shared_file_path, 'w', encoding='utf-8-sig') as shared_file:
                                    shared_file.writelines(chat)
                                    logging.info(f"Saved shared chat to {shared_file_path}")
                            
                            break  # Stop after the first occurrence

            except Exception as e:
                logging.error(f"Error processing file {chat_file}: {e}")
            
    except Exception as e:
        logging.error(f"Error in main function: {e}")

if __name__ == "__main__":
    main()