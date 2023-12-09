# Chat-Analyzer-V2
A standard version of the daily chats reports 
# Chat Data Analysis Toolkit

## Overview
This repository contains a set of Python scripts designed for the analysis and visualization of chat data. The toolkit includes functionalities such as validation of chat group names, detailed report generation, delay analysis, and graph generation for insightful data presentation.

## Scripts

### 1. Table1 Validator (`table1_validater.py`)
- **Purpose**: Parses and validates chat group names from file names.
- **Key Functions**: 
  - Removing prefixes and file extensions from chat group names.
  - Handling special cases for team names, particularly 'SALES' team.

### 2. Table2 Report Generator (`table2_report.py`)
- **Purpose**: Processes individual lines of chat data for analysis.
- **Key Functions**: 
  - Pattern recognition in chat data.
  - Logging and data processing for chat analysis.

### 3. Table3 Delay Analysis (`table3_delay_analysis.py`)
- **Purpose**: Analyzes delays in chat data.
- **Key Functions**: 
  - Lists chat files for time-based analysis.
  - Basic logging setup for tracking analysis process.

### 4. Table4 Graph Generator (`table4_graph_generator.py`)
- **Purpose**: Generates graphs and visualizations from chat data.
- **Key Functions**: 
  - Data visualization using `matplotlib`.
  - Supports detailed analysis through graphical representations.

## Installation
Clone this repository to your local machine using:
