# Friday AI Assistant

Friday is an AI assistant designed to help with various tasks such as email management, reminders, and answering questions about scientific papers and biomedical topics. The assistant integrates with multiple APIs and services to provide a comprehensive set of tools.

## Features
- Email Management: Automatically checks for new emails and notifies the AI.
- Reminders: Create and manage reminders with customizable intervals.
- Scientific Paper Search: Search for scientific papers on Arxiv and PubMed.
- GUI Updates: Update the GUI with custom messages.
- Chat History Management: Save and load chat history.
- File Uploads: Handle file uploads and integrate them into the chat.

## Installation
1. clone the repo:
```bash
git clone https://github.com/SohamTilekar/friday
```
2. Navigate to the project directory:
```bash
cd friday
```
3. Install the required dependencies:
```bash
pip install -r requirements.txt
```
## Usage
Set up the environment variables in a `.env` file.
Run the application:
```bash
python main.py
```
or
```bash
pip install uwsgi
uwsgi --socket 127.0.0.1:5000 --protocol=http -w wsgi:app --workers 1 # DOnt work curently
```
open the https://127.0.0.1:5000 in your Browser to accsis the AI
