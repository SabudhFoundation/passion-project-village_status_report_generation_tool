import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from src import utils, llm, database, prompts
from config import settings
from deep_translator import GoogleTranslator

# --- 1. CACHING DATA CALLS ---
# This prevents querying MongoDB multiple times for the same village during reruns
@st.cache_data(ttl=3600) # Caches for 1 hour
def fetch_village_data(village_name: str):
    return database.get_village_by_name(village_name)

@st.cache_data(ttl=3600)
def search_villages(village_name: str):
    return database.search_villages_for_grid(village_name)

# --- 2. MODULAR SESSION STATE ---
def initialize_session_state():
    """Initializes all required session state variables."""
    defaults = {
        'messages': [{"role": "assistant", "content": prompts.WELCOME_PROMPT}],
        'detected_lang': 'en',
        'extracted_candidates': [],
        'confirmed': False,
        'selected_village_name': None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# --- 3. MAIN APP STRUCTURE ---
def main():
    st.set_page_config(page_title=settings.PAGE_TITLE, layout=settings.PAGE_LAYOUT)
    st.title("🏡 Village Status Report Generation")

    initialize_session_state()

    # Render Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- 3. Handle User Input ---
    # Dynamically translate the placeholder based on current session language
    input_placeholder = "Enter village name or ask a question..."
    if st.session_state['detected_lang'] == 'pa':
        input_placeholder = "ਪਿੰਡ ਦਾ ਨਾਮ ਦਰਜ ਕਰੋ ਜਾਂ ਸਵਾਲ ਪੁੱਛੋ..."

    if prompt := st.chat_input(input_placeholder):
        
        # ⬅️ NEW: Reset the report state so the old report disappears!
        st.session_state['confirmed'] = False
        st.session_state['selected_village_name'] = None
        st.session_state['extracted_candidates'] = None
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): 
            st.markdown(prompt)

        with st.spinner("Analyzing..."):
            # Detect language and update the GLOBAL session state immediately
            detected_input_lang = utils.detect_lang(prompt)
            st.session_state['detected_lang'] = detected_input_lang
            lang = st.session_state['detected_lang']

            # Classify Intent using the LLM
            classification = llm.classify_and_extract(prompt)
            intent = classification.get("intent")
            village_name = classification.get("village_name")
#newwwwwwwww
            

            # ⬅️ Translate village name to English for MongoDB search if detected as Punjabi
            if village_name and lang == 'pa':
                try:
                    from deep_translator import GoogleTranslator
                    village_name = GoogleTranslator(source='pa', target='en').translate(village_name)
                except:
                    pass

            # Handle different user intents
            if intent == "help_request":
                msg = "I can help you generate status reports for villages. Just type the name of the village, e.g., 'Show me the report for Baluana'."
                if lang == 'pa': msg = utils.get_translation(msg)
                with st.chat_message("assistant"): st.info(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})

            elif intent == "salutation":
                msg = "Hello! How can I assist you with village reports today?"
                if lang == 'pa': msg = utils.get_translation(msg)
                with st.chat_message("assistant"): st.success(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})

            elif intent == "status_report" and village_name:
                candidates = search_villages(village_name)
                
                if candidates:
                    st.session_state['extracted_candidates'] = candidates
                    msg = f"Found matches for '{village_name}'. Please select one from the table below."
                    if lang == 'pa': msg = utils.get_translation(msg)
                    with st.chat_message("assistant"): st.success(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})
                else:
                    msg = f"Sorry, I couldn't find a village named '{village_name}'. Please check the spelling."
                    if lang == 'pa': msg = utils.get_translation(msg)
                    with st.chat_message("assistant"): st.error(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})
                
                # --- The Fallback Block ---
            else:
                msg = "I'm not sure I understood that. Could you please provide the name of the village you're looking for?"
                if lang == 'pa': 
                    msg = "ਮੈਨੂੰ ਇਹ ਸਮਝ ਨਹੀਂ ਆਇਆ। ਕੀ ਤੁਸੀਂ ਉਸ ਪਿੰਡ ਦਾ ਨਾਮ ਦੱਸ ਸਕਦੇ ਹੋ ਜਿਸਦੀ ਤੁਸੀਂ ਰਿਪੋਰਟ ਦੇਖਣਾ ਚਾਹੁੰਦੇ ਹੋ?"
                
                with st.chat_message("assistant"): 
                    st.warning(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})

    # --- 4. AgGrid Selection Block ---
    # --- 4. Selection & Settings UI Block ---
    if st.session_state.get('extracted_candidates') and not st.session_state['confirmed']:
        st.markdown("### 📍 Select a Village")
        
        df = pd.DataFrame(st.session_state['extracted_candidates'])
        display_df = df.rename(columns={
            "village_name": "Village Name",
            "gp_name": "Gram Panchayat",
            "block_name": "Block"
        })
        
        # UI Polish: Remove checkboxes for a cleaner look, enable full-row clicking
        gb = GridOptionsBuilder.from_dataframe(display_df)
        gb.configure_selection('single', use_checkbox=False) 
        grid_options = gb.build()

        grid_response = AgGrid(
            display_df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=True,
            theme='streamlit',
            height=200, # Constrain height so the user doesn't have to scroll on large results
            key="village_grid"
        )

        selected = grid_response.get('selected_rows')
        
        # Show Settings only if a row is actively selected
        if selected is not None and len(selected) > 0:
            st.divider()
            
            # UX Polish: Stacked layout
            default_idx = 1 if st.session_state['detected_lang'] == 'pa' else 0
            report_lang = st.radio(
                "📄 Select Report Language:", 
                options=["English", "Punjabi (ਪੰਜਾਬੀ)"], 
                index=default_idx,
                horizontal=True
            )

            st.write("") # Add a little vertical breathing room
            
            # Button is now below the radio selection
            if st.button("✅ Generate Report", type="primary"):
                
                # Save language choice
                st.session_state['detected_lang'] = 'pa' if report_lang == "Punjabi (ਪੰਜਾਬੀ)" else 'en'

                # Extract name safely
                if isinstance(selected, pd.DataFrame):
                    st.session_state['selected_village_name'] = selected.iloc[0]['Village Name']
                else:
                    st.session_state['selected_village_name'] = selected[0]['Village Name']
                
                st.session_state['confirmed'] = True
                st.rerun()

    # --- 5. Render Final Report ---
    if st.session_state['confirmed'] and st.session_state['selected_village_name']:
        
        with st.spinner("Fetching data from database..."):
            village_data = fetch_village_data(st.session_state['selected_village_name'])
        
        if village_data:
            # Render the UI (Text + Charts inside expanders)
            utils.render_latest_view(village_data, st.session_state['detected_lang'])
            
            # --- AI Insights Section (with Error Handling) ---
            st.divider() 
            insight_header = "🧠 AI-Generated Insights & Recommendations"
            if st.session_state['detected_lang'] == 'pa':
                insight_header = "🧠 AI-ਦੁਆਰਾ ਤਿਆਰ ਕੀਤੀਆਂ ਗਈਆਂ ਜਾਣਕਾਰੀਆਂ ਅਤੇ ਸਿਫ਼ਾਰਸ਼ਾਂ"
            st.subheader(insight_header)
            
            cache_key = f"insights_{st.session_state['selected_village_name']}_{st.session_state['detected_lang']}"
            
            if cache_key not in st.session_state:
                with st.spinner("Analyzing village data for insights..."):
                    try:
                        # Attempt to get insights
                        insights = llm.analyze_village_data(
                            village_data=village_data, 
                            lang=st.session_state['detected_lang']
                        )
                        st.session_state[cache_key] = insights
                    except Exception as e:
                        # Fallback if the API fails (e.g., Quota hit, network error)
                        error_msg = "⚠️ Could not generate insights at this time due to high traffic. Please try again later."
                        st.session_state[cache_key] = error_msg
                        print(f"LLM Error: {e}") # Log to terminal for the dev
            
            # Display Insights
            if "⚠️" in st.session_state[cache_key]:
                st.warning(st.session_state[cache_key])
            else:
                st.markdown(st.session_state[cache_key])
            
            # --- PDF Download Button (with Error Handling) ---
            st.divider()
            
            try:
                # We wrap the PDF generation in a try/except because ReportLab 
                # can crash if it encounters unexpected nulls or missing fonts
                pdf_bytes = utils.generate_pdf_report(
                    village_data, 
                    st.session_state['detected_lang'], 
                    st.session_state[cache_key] 
                )
                
                btn_label = "📥 Download Complete PDF Report" if st.session_state['detected_lang'] != 'pa' else "📥 ਪੂਰੀ ਪੀਡੀਐਫ ਰਿਪੋਰਟ ਡਾਊਨਲੋਡ ਕਰੋ"
                
                # UI Polish: Center the download button
                col_spacer1, col_btn, col_spacer2 = st.columns([1, 2, 1])
                with col_btn:
                    st.download_button(
                        label=btn_label, 
                        data=pdf_bytes, 
                        file_name=f"{village_data['village_name']}_report.pdf", 
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary"
                    )
            except Exception as e:
                st.error("🚨 An error occurred while compiling the PDF. The data may be incomplete.")
                print(f"PDF Generation Error: {e}")
                
        else:
            st.error(f"Failed to load data for {st.session_state['selected_village_name']}. The database might be unreachable.")

if __name__ == "__main__":
    main()