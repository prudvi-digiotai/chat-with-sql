import streamlit as st
import pandas as pd
from vyzeai.models.openai import ChatOpenAI
from vyzeai.agents.react_agent import Agent
from vyzeai.tools.prebuilt_tools import execute_query
from vyzeai.tools.raw_functions import excel_to_sql

st.set_page_config(page_title="Excel to SQL Chat App")
st.title("Excel to SQL Chat App")

if 'api_key' not in st.session_state:
    st.session_state['api_key'] = None

api_key = st.text_input("Enter opeani api key", type='password', key='api_key')
user = st.text_input("MySQL Username", 'ue7o33jvbwbjki1bpn9u', key='user')
password = st.text_input("MySQL Password", 'X0JhUt0EXd4ptTjQjMwmrZCnxGUMdb', type="password", key='password')
host = st.text_input("MySQL Host", 'b3vgwfjpijctkrf2vqro-postgresql.services.clever-cloud.com:50013', key='host')
database = st.text_input("Database Name", 'b3vgwfjpijctkrf2vqro', key='database')

uploaded_files = st.file_uploader("Upload Excel Files", type=["xlsx"], key='files', accept_multiple_files=True)

if st.session_state.api_key:

    if 'llm' not in st.session_state:
        st.session_state['llm'] = ChatOpenAI(memory=True, api_key=st.session_state.api_key)
    if not 'agent' in st.session_state:
        query_tool = execute_query()
        tools = [query_tool]
        with open('system_prompt.py') as f:
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
            
                response = excel_to_sql(excel_file_path, table_name, user, password, host, database)
                st.success(response)
        else:
            st.error("Please upload at least one Excel file.")

    st.subheader("Chat with your Data")
    query = st.text_area("Enter your message", height=95)

    if st.button("Execute Query"):
        st.session_state.messages.append({"role": "user", "content": query})

        command = f"""
            user = '{user}'
            password = '{password}'
            host = '{host}'
            database = '{database}'

            tables prvided by the user are {st.session_state.tables}. Consider these tables for user queries.
            
            \nUser query: {query}
            """
        
        response = st.session_state.agent(command)
        response = response.split('**:')[-1]
        st.session_state.messages.append({"role": "assistant", "content": response})
        ai_message = st.chat_message('ai')
        ai_message.write(response)


    with st.sidebar:
        st.header("Chat Log")
        for message in st.session_state.messages:
            with st.expander(message['role']):
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
