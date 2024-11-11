import os

def delete_images_in_current_directory() -> None:
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
    
    current_directory = os.getcwd()

    for filename in os.listdir(current_directory):

        _, extension = os.path.splitext(filename)

        if extension.lower() in image_extensions:
            file_path = os.path.join(current_directory, filename)
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Error: {e} - {file_path}")

def get_images_in_current_directory() -> list:
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
    
    current_directory = os.getcwd()

    image_files = []

    for filename in os.listdir(current_directory):

        _, extension = os.path.splitext(filename)
          
        if extension.lower() in image_extensions:
            file_path = os.path.join(current_directory, filename)
            image_files.append(file_path)
    return image_files

import streamlit as st
import pandas as pd
from wyge.models.openai import ChatOpenAI
from wyge.agents.react_agent import Agent
from wyge.tools.prebuilt_tools import execute_query, execute_code, install_library
from wyge.tools.raw_functions import file_to_sql, get_metadata
# from plots import tools as plot_tools
# from sql import get_metadata

st.set_page_config(page_title="Excel to SQL Chat App")
st.title("Excel to SQL Chat App")

if 'api_key' not in st.session_state:
    st.session_state['api_key'] = None

api_key = st.text_input("Enter opeani api key", type='password', key='api_key')
user = st.text_input("MySQL Username", 'uibcedotbqcywunfl752', key='user')
password = st.text_input("MySQL Password", 'LrdjP9dvLV0GP8PWRDmvREDB9IxmGu', type="password", key='password')
host = st.text_input("MySQL Host", 'by80v7itmu1gw3kjmblq-postgresql.services.clever-cloud.com:50013', key='host')
database = st.text_input("Database Name", 'by80v7itmu1gw3kjmblq', key='database')

uploaded_files = st.file_uploader("Upload Excel Files", type=["xlsx"], key='files', accept_multiple_files=True)

if st.session_state.api_key:

    if 'llm' not in st.session_state:
        st.session_state['llm'] = ChatOpenAI(memory=True, api_key=st.session_state.api_key)
    if not 'agent' in st.session_state:
        tools = [execute_query(), execute_code(), install_library()] 
        with open('system_prompt3.py') as f:
            sys_p = f.read()
        st.session_state['agent'] = Agent(st.session_state['llm'], tools, react_prompt=sys_p)
    if not 'tables' in st.session_state:
        st.session_state['tables'] = []
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if st.button("Store Data", key='files_uploaded'):
        if uploaded_files:
            for uploaded_file in uploaded_files:
                excel_file_path = uploaded_file.name
                table_name = uploaded_file.name.split('.')[0]
                st.session_state.tables.append(table_name)

                with open(excel_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            
                response = file_to_sql(excel_file_path, table_name, user, password, host, database)
                st.success(response)
        else:
            st.error("Please upload at least one Excel file.")

    st.subheader("Chat with your Data")
    query = st.text_area("Enter your message", height=95)


    if st.button("Execute Query"):
        st.session_state.messages.append({"role": "user", "content": query})
        
        if not 'metadata' in st.session_state:
            st.session_state['metadata'] = get_metadata(host, user, password, database, st.session_state.tables)
        command = f"""
            user = '{user}'
            password = '{password}'
            host = '{host}'
            database = '{database}'

            Answer the queries from the these tables: 
            {st.session_state.tables}

            Metadata of the tables : 
            {st.session_state.metadata}

            User query: 
            {query}
            """
        
        # delete_images_in_current_directory()
        delete_images_in_current_directory()
        response = st.session_state.agent(command)
        if '**Answer**:' in response:
            response = response.split('**Answer**:')[-1]
        elif 'Answer:' in response:
            response = response.split('Answer:')[-1]
        elif 'Answer' in response:
            response = response.split('Answer')[-1]
        st.session_state.messages.append({"role": "assistant", "content": response})
        ai_message = st.chat_message('ai')
        ai_message.write(response)
        plots = get_images_in_current_directory()
        for plot in plots:
            st.image(plot)

    with st.sidebar:
        st.header("Chat Log")
        for message in st.session_state.messages:
            with st.expander(message['role']):
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])


# st.write(st.session_state.llm.chat_memory.get_memory())
