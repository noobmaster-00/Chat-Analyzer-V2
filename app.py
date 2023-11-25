# app.py
from flask import Flask, render_template, request
import json
import subprocess   

app = Flask(__name__)

all_names = ['Jasmine Edoofa','Shivjeet Edoofa', 'Milan Edoofa', 'Kirti Edoofa', 'Ashi Edoofa', 'Vilsha Edoofa', 'Saloni Edoofa', 'Ananya Edoofa', 'Tenzin Tsomo ~ Mentor', 'Aditi Edoofa', 'Sharda Edoofa','Piiyush Nanda', 'Sahil Edoofa', 'Shubham Madhwal', 'Austin#276', 'Sagar', 'Kunal', 'Shashwat Edoofa 2', 'Harmehak', 'Arshita', 'Tushti', '+91 79820 48840']

@app.route('/update-gdrive-settings', methods=['POST'])
def update_gdrive_settings():
    gdrive_path = request.form['gdrive_path']
    ewyl_team = request.form['ewyl_team'].split(',')
    kam_team = request.form['kam_team'].split(',')
    sales_team = request.form['sales_team'].split(',')

    gdrive_settings = {
        'gdrive_path': gdrive_path,
        'ewyl_team': ewyl_team,
        'kam_team': kam_team,
        'sales_team': sales_team
    }

    save_gdrive_settings(gdrive_settings)
    return render_template('index.html', message="Google Drive Settings updated successfully!", settings=load_settings(), gdrive_settings=gdrive_settings, all_names=all_names)

def save_gdrive_settings(settings):
    with open('gdrive_settings.json', 'w') as file:
        json.dump(settings, file)

def load_gdrive_settings():
    try:
        with open('gdrive_settings.json', 'r') as file:
            return json.load(file)
    except (IOError, json.JSONDecodeError):
        return {}




@app.route('/')
def index():
    settings = load_settings()
    return render_template('index.html', settings=settings, all_names=all_names)

@app.route('/update-settings', methods=['POST'])
def update_settings():
    name_list = request.form.getlist('name_list')
    days_back = request.form['days_back']
    days_range = request.form['days_range']
    chat_file_path = request.form['chat_file_path']  # New field for chat file path

    settings = {
        'name_list': name_list,
        'days_back': int(days_back),
        'days_range': int(days_range),
        'chat_file_path': chat_file_path  # Store the chat file path
    }

    save_settings(settings)
    return render_template('index.html', message="Settings updated successfully!", settings=settings, all_names=all_names)
    

@app.route('/run-chat-separation', methods=['POST'])
def run_chat_separation():
    # Run the chat_separation.py script
    subprocess.run(['python', 'chat_separation.py'])
    return render_template('index.html', message="Chat Separation Script Executed", settings=load_settings(), all_names=all_names)

@app.route('/run-gtd', methods=['POST'])
def run_gtd():
    # Run the gtd.py script
    subprocess.run(['python', 'gtd.py'])
    return render_template('index.html', message="Google Drive Upload Script Executed", settings=load_settings(), all_names=all_names)    

def save_settings(settings):
    with open('settings.json', 'w') as file:
        json.dump(settings, file)

def load_settings():
    try:
        with open('settings.json', 'r') as file:
            return json.load(file)
    except (IOError, json.JSONDecodeError):
        return {}

if __name__ == '__main__':
    app.run(debug=True)
