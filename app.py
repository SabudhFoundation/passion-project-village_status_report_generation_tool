import streamlit as st

# Import the wrapped functions using the full package path
from school_report_gen_tool.src.main import run_school_app
from village_report_gen_tool.app import run_village_app

# Run set_page_config ONLY HERE
st.set_page_config(page_title="Master Data Portal", layout="wide")

def main():
    if 'current_tool' not in st.session_state:
        st.session_state.current_tool = 'home'

    # Sidebar back button (only shows if NOT on home page)
    if st.session_state.current_tool != 'home':
        if st.sidebar.button("🔙 Back to Portal"):
            st.session_state.current_tool = 'home'
            st.rerun()

    if st.session_state.current_tool == 'home':
        st.title("📊 Master Data Generation Portal")
        st.write("Select a tool to begin:")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info("### 🏫 School Status Report")
            if st.button("Open School Tool", use_container_width=True):
                st.session_state.current_tool = 'school'
                st.rerun()
                
        with col2:
            st.success("### 🏘️ Village Report")
            if st.button("Open Village Tool", use_container_width=True):
                st.session_state.current_tool = 'village'
                st.rerun()

    elif st.session_state.current_tool == 'school':
        run_school_app()

    elif st.session_state.current_tool == 'village':
        run_village_app()

if __name__ == "__main__":
    main()