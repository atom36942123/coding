#run=streamlit run langchainn.py

#env
from dotenv import load_dotenv
import os
load_dotenv()
grok_key=os.getenv("grok_key")

#llm
from langchain_groq import ChatGroq
llm=ChatGroq(temperature=0,groq_api_key=grok_key,model_name="llama-3.1-70b-versatile")

#chromadb add csv
import chromadb
import pandas as pd
import uuid
df=pd.read_csv("./portfolio.csv")
client=chromadb.PersistentClient('vectorstore')
chromadb_collection=client.get_or_create_collection(name="portfolio")
if not chromadb_collection.count():
    for _,row in df.iterrows():chromadb_collection.add(documents=[row["Techstack"]],metadatas=[{"links": row["Links"]}],ids=[str(uuid.uuid4())])

#data clean
import re
def data_clean(data):
    data=re.sub(r'<[^>]*?>', '', data)
    data=re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', data)
    data=re.sub(r'[^a-zA-Z0-9 ]', '', data)
    data=re.sub(r'\s{2,}', ' ', data)
    data=data.strip()
    data=' '.join(data.split())
    return data

#website data load
from langchain_community.document_loaders import WebBaseLoader
def website_data_load(url):
    loader=WebBaseLoader(url)
    data=loader.load().pop().page_content
    return data

#website data json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
def website_data_to_json(llm,website_data):
    prompt_extract=PromptTemplate.from_template(
    """
    ### SCRAPED TEXT FROM WEBSITE:
    {website_data}
    ### INSTRUCTION:
    The scraped text is from the career's page of a website.
    Your job is to extract the job postings and return them in JSON format containing the following keys: `role`, `experience`, `skills` and `description`.
    Only return the valid JSON.
    ### VALID JSON (NO PREAMBLE):
    """
    )
    chain_extract=prompt_extract | llm
    response=chain_extract.invoke(input={"website_data":website_data})
    try:response=JsonOutputParser().parse(response.content)
    except OutputParserException:raise OutputParserException("Context too big")
    return response

#write mail
from langchain_core.prompts import PromptTemplate
def write_email(llm,website_data_json,portfolio_link):
    prompt_email=PromptTemplate.from_template(
    """
    ### JOB DESCRIPTION:
    {website_data_json}
    ### INSTRUCTION:
    You are Mohan, a business development executive at AtliQ. AtliQ is an AI & Software Consulting company dedicated to facilitating
    the seamless integration of business processes through automated tools. 
    Over our experience, we have empowered numerous enterprises with tailored solutions, fostering scalability, 
    process optimization, cost reduction, and heightened overall efficiency. 
    Your job is to write a cold email to the client regarding the job mentioned above describing the capability of AtliQ 
    in fulfilling their needs.
    Also add the most relevant ones from the following links to showcase Atliq's portfolio: {portfolio_link}
    Remember you are Mohan, BDE at AtliQ. 
    Do not provide a preamble.
    ### EMAIL (NO PREAMBLE):
    """
    )
    chain_email=prompt_email | llm
    response=chain_email.invoke({"website_data_json":str(website_data_json),"portfolio_link":portfolio_link})
    return response.content

#streamlit
import streamlit as st
st.set_page_config(layout="wide",page_title="Cold Email Generator",page_icon="📧")
url_input=st.text_input("Enter a URL:")
submit_button=st.button("Submit")
if submit_button:
    try:
        website_data=website_data_load(url_input)
        website_data=data_clean(website_data)
        website_data_json=website_data_to_json(llm,website_data)
        skills=website_data_json['skills']
        portfolio_link=chromadb_collection.query(query_texts=skills,n_results=2).get('metadatas',[])
        email=write_email(llm,website_data_json,portfolio_link)
        st.code(email,language='markdown')
    except Exception as e:st.error(f"An Error Occurred: {e.args}")

