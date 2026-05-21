import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from deep_translator import GoogleTranslator
import difflib

# --- 1. UPDATED PACKAGE IMPORTS ---
from village_report_gen_tool.src import utils, llm, database, prompts
from village_report_gen_tool.config import settings

# --- 2. CACHING DATA CALLS ---
# This prevents querying MongoDB multiple times for the same village during reruns
@st.cache_data(ttl=3600) # Caches for 1 hour
def fetch_village_data(village_name: str):
    return database.get_village_by_name(village_name)

@st.cache_data(ttl=3600)
def search_villages(village_name: str):
    return database.search_villages_for_grid(village_name)

# --- 3. MODULAR SESSION STATE ---
def initialize_session_state():
    """Initializes all required session state variables."""
    defaults = {
        'messages': [{"role": "assistant", "content": prompts.WELCOME_PROMPT}],
        'detected_lang': 'en',
        'extracted_candidates': [],
        'confirmed': False,
        'selected_villages': [] # Now a list to hold 1 or 2 villages
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# --- 4. MAIN APP STRUCTURE (RENAMED) ---
def run_village_app():
    # REMOVED st.set_page_config() - Handled by Master Router
    
    st.title("🏡 Village Status Report Generation")

    initialize_session_state()

    # Render Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- Handle User Input ---
    # Dynamically translate the placeholder based on current session language
    input_placeholder = "Enter village name or ask a question..."
    if st.session_state['detected_lang'] == 'pa':
        input_placeholder = "ਪਿੰਡ ਦਾ ਨਾਮ ਦਰਜ ਕਰੋ ਜਾਂ ਸਵਾਲ ਪੁੱਛੋ..."

    if prompt := st.chat_input(input_placeholder):
        
        # Reset the new selected_villages list
        st.session_state['confirmed'] = False
        st.session_state['selected_villages'] = [] 
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
            try:
                classification = llm.classify_and_extract(prompt)
            except Exception as e:
                st.error("⚠️ Network connection lost while contacting the AI. Please check your internet and try again.")
                print(f"API Connection Error: {e}")
                st.stop() # Stops the rest of the app from running and crashing
            intent = classification.get("intent")
            village_name = classification.get("village_name")
            
            # Translate village name to English for MongoDB search if detected as Punjabi
            if village_name and lang == 'pa':
                try:
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
                    # --- Smart Spell Checker ---
                    try:
                        all_village_names = database.get_all_villages_list()
                        # Find top 2 closest matches (cutoff=0.5 means at least 50% similar)
                        closest_matches = difflib.get_close_matches(village_name, all_village_names, n=2, cutoff=0.5)
                        
                        if closest_matches:
                            suggestions = " or ".join(f"**{match}**" for match in closest_matches)
                            msg = f"I couldn't find '{village_name}' village. Did you mean {suggestions}?"
                            # Add manual Punjabi translation for the suggestion feature
                            if lang == 'pa': 
                                msg = f"ਮੈਨੂੰ '{village_name}' ਨਹੀਂ ਮਿਲਿਆ। ਕੀ ਤੁਹਾਡਾ ਮਤਲਬ {suggestions} ਸੀ?"
                                
                            with st.chat_message("assistant"): st.warning(msg)
                            st.session_state.messages.append({"role": "assistant", "content": msg})
                        else:
                            msg = f"Sorry, I couldn't find a village named '{village_name}'. Please check the spelling."
                            if lang == 'pa': msg = utils.get_translation(msg)
                            with st.chat_message("assistant"): st.error(msg)
                            st.session_state.messages.append({"role": "assistant", "content": msg})
                            
                    except Exception as e:
                        # Fallback if DB fetch fails
                        msg = f"Sorry, I couldn't find a village named '{village_name}'. Please check the spelling."
                        if lang == 'pa': msg = utils.get_translation(msg)
                        with st.chat_message("assistant"): st.error(msg)
                        st.session_state.messages.append({"role": "assistant", "content": msg})
                        print(f"Spellcheck Error: {e}")
                
            # --- The Fallback Block ---
            else:
                msg = "I'm not sure I understood that. Could you please provide the name of the village you're looking for?"
                if lang == 'pa': 
                    msg = "ਮੈਨੂੰ ਇਹ ਸਮਝ ਨਹੀਂ ਆਇਆ। ਕੀ ਤੁਸੀਂ ਉਸ ਪਿੰਡ ਦਾ ਨਾਮ ਦੱਸ ਸਕਦੇ ਹੋ ਜਿਸਦੀ ਤੁਸੀਂ ਰਿਪੋਰਟ ਦੇਖਣਾ ਚਾਹੁੰਦੇ ਹੋ?"
                
                with st.chat_message("assistant"): 
                    st.warning(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})


    # --- Selection & Settings UI Block ---
    if st.session_state.get('extracted_candidates') and not st.session_state['confirmed']:
        st.markdown("### 📍 Select 1 or 2 Villages to Compare")
        
        df = pd.DataFrame(st.session_state['extracted_candidates'])
        display_df = df.rename(columns={
            "village_name": "Village Name",
            "gp_name": "Gram Panchayat",
            "block_name": "Block"
        })
        
        # Allow 'multiple' selection and bring back checkboxes for clarity
        gb = GridOptionsBuilder.from_dataframe(display_df)
        gb.configure_selection('multiple', use_checkbox=True) 
        grid_options = gb.build()

        grid_response = AgGrid(
            display_df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=True,
            theme='streamlit',
            height=200, 
            key="village_grid"
        )

        selected = grid_response.get('selected_rows')
        
        # Show Settings only if 1 or more rows are actively selected
        if selected is not None and len(selected) > 0:
            st.divider()
            
            # Graceful Truncation instead of Hard Blocking
            if len(selected) > 2:
                st.warning(f"⚠️ You selected {len(selected)} villages. To keep the dashboard visually clean, we will only compare the first two.")
                
                # Safely slice the selection down to just the first 2 items
                if isinstance(selected, pd.DataFrame):
                    selected = selected.head(2)
                else:
                    selected = selected[:2]

            # Stacked layout
            default_idx = 1 if st.session_state['detected_lang'] == 'pa' else 0
            report_lang = st.radio(
                "📄 Select Report Language:", 
                options=["English", "Punjabi (ਪੰਜਾਬੀ)"], 
                index=default_idx,
                horizontal=True
            )

            st.write("") 
            
            # Dynamic button text
            btn_text = "✅ Generate Report" if len(selected) == 1 else "📊 Compare Villages"
            
            if st.button(btn_text, type="primary"):
                
                st.session_state['detected_lang'] = 'pa' if report_lang == "Punjabi (ਪੰਜਾਬੀ)" else 'en'

                # Extract a list of village names
                selected_names = []
                if isinstance(selected, pd.DataFrame):
                    selected_names = selected['Village Name'].tolist()
                else:
                    selected_names = [row['Village Name'] for row in selected]
                    
                st.session_state['selected_villages'] = selected_names
                st.session_state['confirmed'] = True
                st.rerun()

    
    # --- Render Final Report ---
    if st.session_state['confirmed'] and st.session_state.get('selected_villages'):
        
        with st.spinner("Fetching data from database..."):
            villages_data = []
            for v_name in st.session_state['selected_villages']:
                data = fetch_village_data(v_name)
                if data:
                    villages_data.append(data)
        
        if villages_data:
            # Render the UI
            utils.render_latest_view(villages_data, st.session_state['detected_lang'])
            
            # --- Single Village Mode (LLM & PDF) ---
            if len(villages_data) == 1:
                village_data = villages_data[0]
                v_name = village_data.get('village_name', 'Unknown') # Safe name extraction
                
                # --- AI Insights Section ---
                st.divider() 
                insight_header = "🧠 AI-Generated Insights & Recommendations"
                if st.session_state['detected_lang'] == 'pa':
                    insight_header = "🧠 AI-ਦੁਆਰਾ ਤਿਆਰ ਕੀਤੀਆਂ ਗਈਆਂ ਜਾਣਕਾਰੀਆਂ ਅਤੇ ਸਿਫ਼ਾਰਸ਼ਾਂ"
                st.subheader(insight_header)
                
                # Use the safe v_name instead of the old session state variable
                cache_key = f"insights_{v_name}_{st.session_state['detected_lang']}"
                
                if cache_key not in st.session_state:
                    with st.spinner("Analyzing village data for insights..."):
                        try:
                            insights = llm.analyze_village_data(
                                village_data=village_data, 
                                lang=st.session_state['detected_lang']
                            )
                            st.session_state[cache_key] = insights
                        except Exception as e:
                            error_msg = "⚠️ Could not generate insights at this time due to high traffic. Please try again later."
                            st.session_state[cache_key] = error_msg
                            print(f"LLM Error: {e}")
                
                if "⚠️" in st.session_state[cache_key]:
                    st.warning(st.session_state[cache_key])
                else:
                    st.markdown(st.session_state[cache_key])

                
                # --- PDF Download Button ---
                st.divider()
                try:
                    pdf_bytes = utils.generate_pdf_report(
                        village_data, 
                        st.session_state['detected_lang'], 
                        st.session_state[cache_key] 
                    )
                    
                    btn_label = "📥 Download Complete PDF Report" if st.session_state['detected_lang'] != 'pa' else "📥 ਪੂਰੀ ਪੀਡੀਐਫ ਰਿਪੋਰਟ ਡਾਊਨਲੋਡ ਕਰੋ"
                    
                    col_spacer1, col_btn, col_spacer2 = st.columns([1, 2, 1])
                    with col_btn:
                        st.download_button(
                            label=btn_label, 
                            data=pdf_bytes, 
                            file_name=f"{v_name}_report.pdf", # Use safe v_name here too
                            mime="application/pdf",
                            use_container_width=True,
                            type="primary"
                        )
                except Exception as e:
                    st.error("🚨 An error occurred while compiling the PDF. The data may be incomplete.")
                    print(f"PDF Generation Error: {e}")
                
            # --- Comparison Mode (LLM) ---
            else:
                st.divider()
                insight_header = "🧠 Comparative AI Insights"
                if st.session_state['detected_lang'] == 'pa':
                    insight_header = "🧠 ਤੁਲਨਾਤਮਕ AI ਜਾਣਕਾਰੀਆਂ"
                st.subheader(insight_header)
                
                v1_name = villages_data[0].get('village_name', 'V1')
                v2_name = villages_data[1].get('village_name', 'V2')
                
                # Unique cache key for this specific pair of villages
                cache_key = f"compare_{v1_name}_{v2_name}_{st.session_state['detected_lang']}"
                
                if cache_key not in st.session_state:
                    with st.spinner(f"Analyzing {v1_name} vs {v2_name}..."):
                        try:
                            # Pass the LIST of two villages to our upgraded LLM function
                            insights = llm.analyze_village_data(
                                village_data=villages_data, 
                                lang=st.session_state['detected_lang']
                            )
                            st.session_state[cache_key] = insights
                        except Exception as e:
                            st.session_state[cache_key] = "⚠️ Could not generate comparison at this time."
                            print(f"LLM Error: {e}")
                
                if "⚠️" in st.session_state[cache_key]:
                    st.warning(st.session_state[cache_key])
                else:
                    st.markdown(st.session_state[cache_key])
                    
                # --- PDF Download Button for Comparison ---
                st.divider()
                try:
                    pdf_bytes = utils.generate_comparison_pdf_report(
                        villages_data, 
                        st.session_state['detected_lang'], 
                        st.session_state[cache_key] 
                    )
                    
                    btn_label = "📥 Download Comparison PDF" if st.session_state['detected_lang'] != 'pa' else "📥 ਤੁਲਨਾਤਮਕ ਪੀਡੀਐਫ ਡਾਊਨਲੋਡ ਕਰੋ"
                    
                    col_spacer1, col_btn, col_spacer2 = st.columns([1, 2, 1])
                    with col_btn:
                        st.download_button(
                            label=btn_label, 
                            data=pdf_bytes, 
                            file_name=f"Comparison_{v1_name}_vs_{v2_name}.pdf", 
                            mime="application/pdf",
                            use_container_width=True,
                            type="primary"
                        )
                except Exception as e:
                    st.error("🚨 An error occurred while compiling the Comparison PDF.")
                    print(f"PDF Generation Error: {e}")
                
        else:
            # Join the list of requested villages into a string for the error message
            requested = ", ".join(st.session_state['selected_villages'])
            st.error(f"Failed to load data for {requested}. The database might be unreachable.")