# WhatsApp Chat Analyzer

This project is designed to analyze WhatsApp chat exports and organize the data into structured formats for further analysis. It processes chat files based on a specific directory structure and outputs the data into CSV files.

## How It Works

1. **Directory Structure**: The chat files are expected to be in a directory structure of Date/Team/Person. The script navigates through these directories to find `.txt` files, which are assumed to be WhatsApp chat exports.

2. **Chat File Processing**: Each chat file is read, and the contents are parsed to extract meaningful information such as the date, time, and sender of each message.

3. **Data Organization**: The data is organized into DataFrames where each row represents a minute of the day, and columns represent the occurrence of messages by either the 'person' or 'others'.

4. **Output**: The final output is a set of CSV files, each corresponding to a person's chat on a particular date, providing a minute-by-minute breakdown of chat activity.

## Usage

To use this script:
1. Place your WhatsApp chat files in the appropriate directory structure.
2. Update the `date_directory` variable in the script with the path to your directory.
3. Run the script to generate CSV files in the specified output directory.

## Note

This script is part of a larger project and is intended for data analysis purposes. Ensure compliance with data privacy and protection regulations when using or modifying this script.
