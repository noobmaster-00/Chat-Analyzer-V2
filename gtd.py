import os
import pickle
import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

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

def create_folder(name, service, parent_id=None):
    """Create a folder on Google Drive."""
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
    file_metadata = {
        'name': os.path.basename(file_name),
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_name)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

def find_folder_id(name, service):
    """Find a folder on Google Drive by name and return its ID."""
    query = f"mimeType='application/vnd.google-apps.folder' and name='{name}'"
    response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    for file in response.get('files', []):
        return file.get('id')
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
        "EWYL": ["Ananya_Edoofa", "Jasmine_Edoofa", "Saloni_Edoofa", "Sharda_Edoofa", "Aditi_Edoofa"],
        "KAM": ["Milan_Edoofa", "Kirti_Edoofa", "Shivjeet_Edoofa", "Vilsha_Edoofa", "Ashi_Edoofa"],
        "SALES": ["Shubham_Edoofa", "Austin_Edoofa", "Sahil_Edoofa", "Shash_Edoofa", "Arshita_Edooofa","Tushti_Edoofa","Pallika_Edoofa","Kunal_Edoofa","Gurvider_Edoofa"]
    }

    # Process each team and member
    for team, members in teams.items():
        team_folder_id = create_folder(team, service, date_folder_id)
        for member in members:
            member_folder_id = create_folder(member, service, team_folder_id)
            member_chat_folder = os.path.join('C:\\whatsapp_chat_analyzer\\filtered_chats', f'{member}')
            if os.path.exists(member_chat_folder):
                for file_name in os.listdir(member_chat_folder):
                    file_path = os.path.join(member_chat_folder, file_name)
                    if os.path.isfile(file_path):
                        upload_file(file_path, member_folder_id, service)

    print("Upload complete.")

if __name__ == '__main__':
    main()
