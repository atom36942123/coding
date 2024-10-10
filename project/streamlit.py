#run=streamlit run streamlit.py


import streamlit as st

# Create an empty container
placeholder = st.empty()

# Insert a form in the container
with placeholder.form("Apply for a Job"):
    st.markdown("#### Apply for a Job")
    name = st.text_input("name")
    email = st.text_input("email")
    mobile = st.text_input("mobile")
    profile = st.text_input("profile")
    experience = st.number_input("experience")
    submit = st.form_submit_button("Apply")

if submit:
    if not name:st.error("name must")
    if not email:st.error("name must")
    else:
        placeholder.empty()
        st.success("Form Submitted Successfully")
   
    

    
    
