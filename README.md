# Natural Language Database Query Chatbot

A Gradio-based web interface that allows users to query a company employee database using natural language. The application uses Google's Gemini AI to convert natural language queries into SQL and provide human-friendly summaries of the results.


## Natural language to SQL conversion


## Requirements
- Python 3.8+
- SQLite database (employees_db-full-1.0.6.db)
- Google Gemini API key
- Required Python packages:
  - google.generativeai
  - gradio
  - sqlite3

## Setup
1. Clone the repository
2. Install required packages:
   ```bash
   pip install google-generativeai gradio
3. Set your Gemini API key as an environment variable:
    ```bash
    export GEMINI_KEY='your-api-key-here'
4. Place your SQLite database file in the project directory and change the name of the database file in the code
5. Run the application:
    ```bash
    python gemini-sql.py

## Usage
1. Access the web interface (default: http://localhost:7860)
2. Type your question in natural language or select from example queries
3. View both the summarized response and detailed JSON results

## Example Queries
- "Show me all departments"
- "List employees who earn more than 100000"
- "Who are the managers?"
- "What is the average salary of employees?"
- "Show me female employees in the Development department"

## Note
The application limits query results to 50 rows by default to ensure reasonable response times and readability.



