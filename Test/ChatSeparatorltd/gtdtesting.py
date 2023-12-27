import os
import pickle
import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate_google_drive():
    """Authenticate and create a Google Drive API service."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)
    return service


def find_folder_id(name, service, parent_id=None):
    """Find a folder on Google Drive by name and return its ID."""
    query = f"mimeType='application/vnd.google-apps.folder' and name='{name}'"
    
    # Include the parent folder ID in the query if provided
    if parent_id:
        query += f" and '{parent_id}' in parents"

    response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    for file in response.get('files', []):
        return file.get('id')
    return None

def create_folder(name, service, parent_id=None):
    """Create a folder on Google Drive if it doesn't exist, otherwise return its ID."""
    query = f"mimeType='application/vnd.google-apps.folder' and name='{name}'"
    
    # Include the parent folder ID in the query if provided
    if parent_id:
        query += f" and '{parent_id}' in parents"
    
    response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    folders = response.get('files', [])
    
    if folders:
        return folders[0]['id']
    else:
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        file = service.files().create(body=file_metadata, fields='id').execute()
        return file.get('id')


def upload_file(file_name, folder_id, service):
    """Upload a file to a specific Google Drive folder."""
    try:
        file_metadata = {
            'name': os.path.basename(file_name),
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_name)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"File {file_name} uploaded successfully to folder ID {folder_id}.")
        return file.get('id')
    except Exception as e:
        print(f"Failed to upload {file_name} to folder ID {folder_id}. Exception: {e}")
        return None

def main():
    service = authenticate_google_drive()

    # Locate the "WhatsApp Chat Analyzer" folder
    parent_folder_name = "WhatsApp Chat Analyzer"
    parent_folder_id = find_folder_id(parent_folder_name, service)

    if parent_folder_id is None:
        print(f'Error: Folder "{parent_folder_name}" not found.')
        return

    # Create a main folder with the current date inside the "WhatsApp Chat Analyzer" folder
    date_folder_name = datetime.datetime.now().strftime("%Y-%m-%d")
    date_folder_id = create_folder(date_folder_name, service, parent_folder_id)

    # Team and member information
    teams = {
        "EWYL": ["Ananya Edoofa", "Jasmine Edoofa", "Saloni Edoofa", "Sharda Edoofa", "Aditi Edoofa"],
        "KAM": ["Milan Edoofa", "Kirti Edoofa", "Shivjeet Edoofa", "Vilsha Edoofa", "Ashi Edoofa"],
        "SALES": ["Sahil Edoofa", "Shubham Edoofa", "Austin Edoofa", "Gurvinder", "Kunal Edoofa", "Shashwat Edoofa", "Harmehak Edoofa",
                  "Arshita Edoofa", "Tushti Edoofa", "Pallika Edoofa"]
    }

    # Process each team and member
    for team, members in teams.items():
        logging.info(f'Processing team: {team}')
        team_folder_id = create_folder(team, service, date_folder_id)
        logging.info(f'Team folder created with ID: {team_folder_id}')

        for member in members:
            logging.info(f'Processing member: {member}')
            # Replace spaces with underscores in member name for folder creation
            member_folder_name = member
            member_folder_id = find_folder_id(member_folder_name, service, team_folder_id)

            # Check if the member folder was found
            if member_folder_id is not None:
                member_chat_folder = os.path.join('C:\\whatsapp_chat_analyzer\\filtered_chats', member_folder_name)
                if os.path.exists(member_chat_folder):
                    logging.info(f'Found member chat folder: {member_chat_folder}')
                    for file_name in os.listdir(member_chat_folder):
                        file_path = os.path.join(member_chat_folder, file_name)
                        if os.path.isfile(file_path):
                            logging.info(f'Uploading file: {file_path}')
                            upload_file(file_path, member_folder_id, service)
                else:
                    logging.warning(f'Member chat folder not found: {member_chat_folder}')
            else:
                logging.warning(f'Member folder not found for: {member}')
                # Create a new folder for the member inside the team folder
                new_member_folder_id = create_folder(member_folder_name, service, team_folder_id)
                if new_member_folder_id is not None:
                    logging.info(f'Created new member folder: {member_folder_name}')
                    # Upload files for the new member
                    member_chat_folder = os.path.join('C:\\whatsapp_chat_analyzer\\filtered_chats', member_folder_name)
                    if os.path.exists(member_chat_folder):
                        for file_name in os.listdir(member_chat_folder):
                            file_path = os.path.join(member_chat_folder, file_name)
                            if os.path.isfile(file_path):
                                logging.info(f'Uploading file: {file_path}')
                                upload_file(file_path, new_member_folder_id, service)
                    else:
                        logging.warning(f'Member chat folder not found: {member_chat_folder}')
                else:
                    logging.error(f'Failed to create a new folder for member: {member_folder_name}')

    logging.info("Upload process complete.")

if __name__ == '__main__':
    main()
