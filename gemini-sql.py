import sqlite3
import json
import os
import google.generativeai as genai
import gradio as gr


conn = sqlite3.connect('employees_db-full-1.0.6.db', check_same_thread=False) # change here to your db file name
c = conn.cursor()
def send_results_to_llm(json_results, initial_prompt, db_scheme):
    prompt = f"""
            You are provided with the results of an SQL query based on a user's initial request. 

            ### SQL Query Results:
            {json_results}

            ### User's Initial Prompt:
            "{initial_prompt}"

            ### Database Schema and Sample Data:
            {db_scheme}

            We used Gemini to transform the user's initial request into the SQL query that generated the above results. Note: These results may be limited to the first 50 rows for display purposes.

            *Task:* Summarize the query results in the context of the user's initial prompt in one paragraph (less than 200 words). 
            Ensure your explanation references the database structure and how the results align with the user's request. 
            Focus on the company. Do not mention any technical terms like SQL, table or database. Just give information about the company, employees or anything user is searching.
            """

    model = genai.GenerativeModel('gemini-1.5-flash', generation_config=genai.GenerationConfig(max_output_tokens=512, temperature=0.7, top_p=0.9, top_k=30))
    

    summary_response  = model.generate_content(prompt).text.strip()
    return summary_response

def get_schema_with_samples():
    schema_with_samples = {}
    tables = c.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    for table in tables:
        table_name = table[0]
        columns = c.execute(f"PRAGMA table_info({table_name});").fetchall()
        schema = {col[1]: col[2] for col in columns}  # {column_name: data_type}
        
      
        samples = c.execute(f"SELECT * FROM {table_name} LIMIT 3;").fetchall()
        sample_data = []
        for row in samples:
            sample_data.append(dict(zip(schema.keys(), row)))
        
        schema_with_samples[table_name] = {
            "columns": schema,
            "examples": sample_data
        }
    return schema_with_samples


genai.configure(api_key=os.environ["GEMINI_KEY"])

db_schema_with_samples = get_schema_with_samples()


system_prompt = f"""
You are an advanced AI assistant designed to help users retrieve data efficiently from databases. Your task is to interpret natural language queries, provided either in English or Turkish, and transform them into precise SQL statements. Here's what you need to know:

- **Database Overview:** The database consists of multiple tables with specific columns. Below is the schema with example records:
  {json.dumps(db_schema_with_samples)}

- **Your Objective:** 
  1. Accurately understand the user's query.
  2. Formulate a complete SQL query that reflects the user's intent.
  3. Ensure the query uses the exact table and column names as specified in the schema.
  4. Support any type of database structure and domain.

- **Response Format:** 
  - Output the results strictly as structured JSON.
  - Do not include any additional text, explanations, or comments.
  - Example JSON structure:
    {{
      "query": [
        {{
          "SQL": "SELECT column1, column2 FROM table_name WHERE condition"
        }}
      ]
    }}

- **Guidelines:** 
  - Focus on delivering precise and efficient SQL queries.
  - Maintain clarity and precision in understanding the user's request.
  - Ensure the response adheres strictly to the JSON format without deviation.
  - Be adaptable to any database schema provided.
  - Use table and column names exactly as specified in the schema.

Your role is to facilitate seamless access to data by converting natural language queries into accurate SQL statements, regardless of the database domain or structure.
"""


def chatbot(user_input):
    
    
    
    model = genai.GenerativeModel('gemini-1.5-flash', generation_config=genai.GenerationConfig(max_output_tokens=256, temperature=0.5, top_p=0.9, top_k=40))
    response = model.generate_content(f"{system_prompt} Generate an SQL query to {user_input}").text
    print(f"Raw model response: {response}")


    try:
        query_json = json.loads(response)
    except json.JSONDecodeError:
        try:
            start_index = response.index('{')
            end_index = response.rindex('}') + 1  
            json_str = response[start_index:end_index]
            query_json = json.loads(json_str)
        except (ValueError, json.JSONDecodeError) as e:
            return {}, "Could not extract valid JSON from the response."  


    sql_query = query_json.get('query', [{}])[0] 
    sql_query_string = sql_query.get('SQL')  

    if not sql_query_string:
        return {}, "No SQL query found in the response."  

    print(f"Executing SQL query: {sql_query_string}")


    if "LIMIT" not in sql_query_string:
        sql_query_string += " LIMIT 50"


    if "SELECT" in sql_query_string:
        sql_query_string = sql_query_string.replace("SELECT", "SELECT DISTINCT", 1)

    # db ye gönderme
    try:
        c.execute(sql_query_string)
        result = c.fetchall()
    except sqlite3.OperationalError as e:
        return {}, str(e)  

    
    columns = [column[0] for column in c.description]
    json_result = {"result": [dict(zip(columns, row)) for row in result]}


    summary = send_results_to_llm(json.dumps(json_result), user_input, db_schema_with_samples)

  
    return summary, json_result




demo = gr.Interface(
    fn=chatbot,
    inputs=[gr.Textbox(label="Write anything about database.")],
    outputs=[gr.Textbox(label="Summary"), gr.JSON(label="Query Result in JSON")], 
    title="Natural Language Database Interaction",
    description="Ask questions about the database.",
    examples=[
        ["Show me all departments"],
        ["List employees who earn more than 100000"],
        ["Who are the managers?"],
        ["What is the average salary of employees?"],
        ["Show me female employees in the Development department"],
        ["List employees hired between 2000 and 2001"],
        ["Find employees who have changed departments"],
    ],

)

if __name__ == "__main__":
    demo.launch()
