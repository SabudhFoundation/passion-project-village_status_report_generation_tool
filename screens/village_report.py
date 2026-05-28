import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import re
import difflib

from src import utils, llm, database, prompts
from src.config import settings

def init_village_session_states():
    defaults = {
        'v_messages': [{"role": "assistant", "content": prompts.VILLAGE_WELCOME_PROMPT}],
        'v_candidates': [],
        'v_confirmed': False,
        'v_selected_names': [],
        'v_lang': 'en'
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def village_report_app():
    st.title("🏡 Village Status Report Generation")
    init_village_session_states()

    lang = st.session_state['v_lang']
    for message in st.session_state['v_messages'][-20:]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    input_placeholder = "Enter village name(s) or ask a question..." if lang == 'en' else "ਪਿੰਡਾਂ ਦੇ ਨਾਮ ਦਰਜ ਕਰੋ ਜਾਂ ਸਵਾਲ ਪੁੱਛੋ..."

    if prompt := st.chat_input(input_placeholder):
        st.session_state['v_confirmed'] = False
        st.session_state['v_selected_names'] = []
        st.session_state['v_candidates'] = []
        
        st.session_state['v_messages'].append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.spinner("Analyzing..."):
            # --- BULLETPROOF PUNJABI DETECTION ---
            # langdetect fails on single words. Checking for Gurmukhi characters is 100% accurate.
            is_punjabi = bool(re.search(r'[\u0A00-\u0A7F]', prompt))
            lang = 'pa' if is_punjabi else 'en'
            st.session_state['v_lang'] = lang
            
            # --- PASS DIRECTLY TO GEMINI ---
            # Gemini reads Punjabi natively and is prompted to extract English names.
            classification = llm.classify_village_intent(prompt)
            intent = classification.get("intent")
            village_names = classification.get("village_names", [])

            if intent == "help_request":
                msg = "I can help you generate status reports for villages or compare them. Type names like 'Baluana'."
                if lang == 'pa': msg = utils.get_translation(msg)
                with st.chat_message("assistant"): st.info(msg)
                st.session_state['v_messages'].append({"role": "assistant", "content": msg})

            elif intent == "salutation":
                msg = "Hello! How can I assist you with village reports today?"
                if lang == 'pa': msg = "ਜੀ ਆਇਆਂ ਨੂੰ! ਅੱਜ ਮੈਂ ਪਿੰਡ ਦੀਆਂ ਰਿਪੋਰਟਾਂ ਵਿੱਚ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?"
                with st.chat_message("assistant"): st.success(msg)
                st.session_state['v_messages'].append({"role": "assistant", "content": msg})

            elif intent == "status_report" and village_names:
                all_candidates = []
                missing_villages = []
                all_village_names_db = database.get_all_villages_list()
                db_names_lower_map = {name.lower(): name for name in all_village_names_db if name}

                for v_name in village_names:
                    candidates = database.search_villages_for_grid(v_name)
                    if candidates:
                        all_candidates.extend(candidates)
                    else:
                        closest_lower = difflib.get_close_matches(v_name.lower().strip(), db_names_lower_map.keys(), n=2, cutoff=0.65)
                        if closest_lower:
                            for match in [db_names_lower_map[m] for m in closest_lower]:
                                match_cands = database.search_villages_for_grid(match)
                                if match_cands: all_candidates.extend(match_cands)
                        else:
                            missing_villages.append(v_name)

                if all_candidates:
                    st.session_state['v_candidates'] = list({c['village_name']: c for c in all_candidates}.values())
                    msg = "Found matches. Please select 1 or 2 villages from the table below."
                    if lang == 'pa': msg = utils.get_translation(msg)
                    with st.chat_message("assistant"): st.success(msg)
                    st.session_state['v_messages'].append({"role": "assistant", "content": msg})
                else:
                    msg = "Sorry, I couldn't find matches for the requested villages. Please check spelling."
                    if lang == 'pa': msg = utils.get_translation(msg)
                    with st.chat_message("assistant"): st.error(msg)
                    st.session_state['v_messages'].append({"role": "assistant", "content": msg})
            else:
                msg = "I'm not sure I understood. Could you provide the village name?"
                if lang == 'pa': msg = utils.get_translation(msg)
                with st.chat_message("assistant"): st.warning(msg)
                st.session_state['v_messages'].append({"role": "assistant", "content": msg})

    # --- UI Grid Selection ---
    if st.session_state.get('v_candidates') and not st.session_state['v_confirmed']:
        df = pd.DataFrame(st.session_state['v_candidates']).rename(columns={"village_name": "Village Name", "gp_name": "Gram Panchayat", "block_name": "Block"})
        
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_selection('multiple', use_checkbox=True)
        grid_response = AgGrid(df, gridOptions=gb.build(), update_mode=GridUpdateMode.SELECTION_CHANGED, theme='streamlit', height=200)

        selected = grid_response.get('selected_rows')
        if selected is not None and len(selected) > 0:
            st.divider()
            if len(selected) > 2:
                st.error("⚠️ Please select a maximum of 2 villages to proceed." if lang == 'en' else "⚠️ ਕਿਰਪਾ ਕਰਕੇ ਅੱਗੇ ਵਧਣ ਲਈ ਵੱਧ ਤੋਂ ਵੱਧ 2 ਪਿੰਡ ਚੁਣੋ।")
            else:
                report_lang = st.radio("📄 Select Report Language:", options=["English", "Punjabi (ਪੰਜਾਬੀ)"], index=1 if lang == 'pa' else 0, horizontal=True)
                btn_text = "✅ Generate Report" if len(selected) == 1 else "📊 Compare Villages"
                
                if st.button(btn_text, type="primary"):
                    st.session_state['v_lang'] = 'pa' if report_lang == "Punjabi (ਪੰਜਾਬੀ)" else 'en'
                    st.session_state['v_selected_names'] = selected['Village Name'].tolist() if isinstance(selected, pd.DataFrame) else [row['Village Name'] for row in selected]
                    st.session_state['v_confirmed'] = True
                    if st.session_state['v_lang'] == 'pa' and not settings.PUNJABI_FONT_LOADED: utils.register_fonts()
                    st.rerun()

    # --- Render Report ---
    if st.session_state['v_confirmed'] and st.session_state.get('v_selected_names'):
        with st.spinner("Fetching data..."):
            villages_data = [database.get_village_by_name(v) for v in st.session_state['v_selected_names'] if database.get_village_by_name(v)]
        
        if villages_data:
            utils.render_village_view(villages_data, st.session_state['v_lang'])
            
            st.divider()
            insight_header = "🧠 AI-Generated Insights" if len(villages_data) == 1 else "🧠 Comparative AI Insights"
            if st.session_state['v_lang'] == 'pa': insight_header = utils.get_translation(insight_header)
            st.subheader(insight_header)
            
            cache_key = f"v_insights_{'_'.join(st.session_state['v_selected_names'])}_{st.session_state['v_lang']}"
            if cache_key not in st.session_state:
                with st.spinner("Analyzing data..."):
                    st.session_state[cache_key] = llm.analyze_village_data(villages_data, st.session_state['v_lang'])
            
            st.markdown(st.session_state[cache_key])
            st.divider()
            
            # 2. PDF Generation perfectly mapped to utils.py
            pdf_bytes = utils.generate_village_pdf(villages_data, st.session_state['v_lang'], st.session_state[cache_key])
            f_name = f"{villages_data[0]['village_name']}_report.pdf" if len(villages_data) == 1 else "Comparison_Report.pdf"
            btn_label = "📥 Download PDF" if st.session_state['v_lang'] == 'en' else "📥 ਪੀਡੀਐਫ ਡਾਊਨਲੋਡ ਕਰੋ"
            st.download_button(label=btn_label, data=pdf_bytes, file_name=f_name, mime="application/pdf", type="primary")