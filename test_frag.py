import streamlit as st
import time

@st.dialog("Test Dialog")
def show_dialog():
    if st.button("Start heavy work"):
        st.session_state.do_work = True
        st.rerun()

if "do_work" not in st.session_state:
    st.session_state.do_work = False

@st.fragment
def heavy_worker():
    if st.session_state.do_work:
        with st.spinner("Heavy work taking 5 seconds..."):
            time.sleep(5)
            st.success("Done!")
        st.session_state.do_work = False

if st.button("Open Dialog"):
    show_dialog()

heavy_worker()
