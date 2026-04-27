import streamlit as st
import time

@st.dialog("Hello")
def my_dialog():
    if st.button("Start 5s blocking task"):
        st.session_state.start_task = True
        st.rerun() # Attempt to close dialog

if "start_task" not in st.session_state:
    st.session_state.start_task = False

if st.button("Open Dialog"):
    my_dialog()

if st.session_state.start_task:
    with st.spinner("Processing..."):
        time.sleep(5)
    st.session_state.start_task = False
    st.write("Done!")
