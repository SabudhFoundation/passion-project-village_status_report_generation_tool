import streamlit as st

# Import the wrapped functions
from school_report_gen_tool.src.main import run_school_app
from village_report_gen_tool.app import run_village_app

st.set_page_config(page_title="Data Generation Portal", layout="wide")

def clear_tool_state():
    """Cleans up leftover data from the previous tool before returning home."""
    for key in list(st.session_state.keys()):
        # Delete everything EXCEPT the current_tool tracker
        if key != 'current_tool':
            del st.session_state[key]

def main():
    if 'current_tool' not in st.session_state:
        st.session_state.current_tool = 'home'

    # --- HOME PAGE ---
    if st.session_state.current_tool == 'home':
        st.title("📊 Master Data Generation Portal")
        st.write("Welcome! Please select the tool you want to use today:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("### 🏫 School Status Report")
            st.write("Generate interactive and bilingual reports for schools.")
            if st.button("Open School Tool", use_container_width=True):
                st.session_state.current_tool = 'school'
                st.rerun()
                
        with col2:
            st.success("### 🏘️ Village Report")
            st.write("Generate demographic and infrastructure reports for villages.")
            if st.button("Open Village Tool", use_container_width=True):
                st.session_state.current_tool = 'village'
                st.rerun()

    # --- SCHOOL TOOL ---
    elif st.session_state.current_tool == 'school':
        if st.sidebar.button("🔙 Back to Home Portal"):
            clear_tool_state()  # ⬅️ Added the cleaner function here!
            st.session_state.current_tool = 'home'
            st.rerun()
            
        run_school_app()

    # --- VILLAGE TOOL ---
    elif st.session_state.current_tool == 'village':
        if st.sidebar.button("🔙 Back to Home Portal"):
            clear_tool_state()  # ⬅️ Added the cleaner function here!
            st.session_state.current_tool = 'home'
            st.rerun()
            
        run_village_app()

if __name__ == "__main__":
    main()