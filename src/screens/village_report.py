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
        'v_year_confirmed': False,
        'v_selected_names': [],
        'v_selected_year': None,
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
    chat_prompt = st.chat_input(input_placeholder)

    # --- 🤖 THE AI CHATBOX TRIGGER ---
    if chat_prompt:
        # Reset all confirmation states on new search (Forces them through the grid checkpoint)
        st.session_state['v_confirmed'] = False
        st.session_state['v_year_confirmed'] = False
        st.session_state['v_selected_names'] = []
        st.session_state['v_selected_year'] = None
        st.session_state['v_candidates'] = []
        
        st.session_state['v_messages'].append({"role": "user", "content": chat_prompt})
        with st.chat_message("user"): st.markdown(chat_prompt)

        with st.spinner("Analyzing..."):
            is_punjabi = bool(re.search(r'[\u0A00-\u0A7F]', chat_prompt))
            lang = 'pa' if is_punjabi else 'en'
            st.session_state['v_lang'] = lang
            
            # --- 🚀 UPGRADED FAST-PATH (TEXT NORMALIZATION) ---
            prompt_clean = chat_prompt.strip()
            normalized_prompt = re.sub(r'\s+(and|&|ਅਤੇ)\s+', ',', prompt_clean, flags=re.IGNORECASE)
            word_count = len(normalized_prompt.replace(',', ' ').split())
            
            if word_count <= 2 and normalized_prompt.lower() not in ['hi', 'hello', 'help']:
                intent = "status_report"
                village_names = [v.strip() for v in normalized_prompt.split(',') if v.strip()]
            else:
                classification = llm.classify_village_intent(chat_prompt)
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
                        closest_lower = difflib.get_close_matches(v_name.lower().strip(), db_names_lower_map.keys(), n=1, cutoff=0.8)
                        if closest_lower:
                            for match in [db_names_lower_map[m] for m in closest_lower]:
                                match_cands = database.search_villages_for_grid(match)
                                if match_cands: all_candidates.extend(match_cands)
                        else:
                            missing_villages.append(v_name)

                # --- 🌐 TAVILY WEB FALLBACK FOR MISSING VILLAGES ---
                for missing_v in missing_villages:
                    if len(missing_v) <= 2:
                        msg = f"⚠️ Please enter a more complete village name than '{missing_v}' to search the live web."
                        if lang == 'pa': msg = utils.get_translation(msg)
                        with st.chat_message("assistant"): st.warning(msg)
                        st.session_state['v_messages'].append({"role": "assistant", "content": msg})
                        continue

                    with st.spinner(f"🔍 '{missing_v}' not in local database. Searching web records..."):
                        web_context = llm.get_external_village_data(missing_v)
                        
                    if web_context:
                        with st.spinner(f"🧠 Synthesizing live web insights for '{missing_v}'..."):
                            web_report = llm.generate_report_from_web(missing_v, web_context, lang)
                            
                        msg = f"🌐 Note: '{missing_v}' is missing from our local dataset. Here is a live summary compiled from web sources:"
                        if lang == 'pa': msg = f"🌐 ਨੋਟ: '{missing_v}' ਸਥਾਨਕ ਡੇਟਾਬੇਸ ਵਿੱਚ ਨਹੀਂ ਹੈ, ਪਰ ਵੈੱਬ ਸਰੋਤਾਂ ਤੋਂ ਲਾਈਵ ਰਿਪੋਰਟ ਤਿਆਰ ਕੀਤੀ ਗਈ ਹੈ:"
                        
                        with st.chat_message("assistant"):
                            st.info(msg)
                            try:
                                import json
                                clean_json = web_report.replace('```json', '').replace('```', '').strip()
                                data = json.loads(clean_json)
                                
                                st.markdown(f"### 🏡 {missing_v.title()} - Web Intelligence Report")
                                st.write(data.get("summary", ""))
                                
                                col1, col2 = st.columns(2)
                                col1.metric("👥 Estimated Population", data.get("population", "Data Unavailable"))
                                col2.metric("📚 Literacy Rate", data.get("literacy_rate", "Data Unavailable"))
                                
                                st.divider()
                                for domain, points in data.get("domains", {}).items():
                                    with st.expander(f"📌 {domain}", expanded=False):
                                        for point in points:
                                            st.markdown(f"- {point}")
                            except Exception as e:
                                st.markdown(web_report)
                                print(f"JSON Parsing Error: {e}")
                                
                        st.session_state['v_messages'].append({"role": "assistant", "content": f"{msg}\n\n[Structured Web Dashboard Displayed for {missing_v}]"})
                    else:
                        msg = f"Sorry, I couldn't find any local records or web data for '{missing_v}'."
                        if lang == 'pa': msg = utils.get_translation(msg)
                        with st.chat_message("assistant"): st.error(msg)
                        st.session_state['v_messages'].append({"role": "assistant", "content": msg})

                # --- 🗄️ LOCAL DATABASE RESULTS UI ---
                if all_candidates:
                    unique_candidates = {c['village_name']: c for c in all_candidates}
                    st.session_state['v_candidates'] = list(unique_candidates.values())
                    
                    msg = "Found local matches. Please select your village(s) from the table below to generate the official report."
                    if lang == 'pa': msg = utils.get_translation(msg)
                    with st.chat_message("assistant"): 
                        st.success(msg)
                        if missing_villages:
                            warn_msg = "Note: Because some requested villages were fetched from live web records, they cannot be compared side-by-side with official database records."
                            if lang == 'pa': warn_msg = utils.get_translation(warn_msg)
                            st.warning(warn_msg)
                            
                    st.session_state['v_messages'].append({"role": "assistant", "content": msg})

    # --- STEP 1: UI Grid Selection (Village Names) ---
    if st.session_state.get('v_candidates') and not st.session_state['v_confirmed']:
        raw_df = pd.DataFrame(st.session_state['v_candidates'])
        display_df = raw_df[["village_name", "gp_name", "block_name"]].rename(
            columns={"village_name": "Village Name", "gp_name": "Gram Panchayat", "block_name": "Block"}
        )
        
        gb = GridOptionsBuilder.from_dataframe(display_df)
        gb.configure_selection('multiple', use_checkbox=True)
        grid_response = AgGrid(display_df, gridOptions=gb.build(), update_mode=GridUpdateMode.SELECTION_CHANGED, theme='streamlit', height=200)

        selected = grid_response.get('selected_rows')
        if selected is not None and len(selected) > 0:
            st.divider()
            selected_names = list(set([row['Village Name'] for row in selected] if not isinstance(selected, pd.DataFrame) else selected['Village Name'].tolist()))
            
            if len(selected_names) > 2:
                st.error("⚠️ Please select a maximum of 2 villages to proceed." if lang == 'en' else "⚠️ ਕਿਰਪਾ ਕਰਕੇ ਅੱਗੇ ਵਧਣ ਲਈ ਵੱਧ ਤੋਂ ਵੱਧ 2 ਪਿੰਡ ਚੁਣੋ।")
            else:
                report_lang = st.radio("📄 Select Report Language:", options=["English", "Punjabi (ਪੰਜਾਬੀ)"], index=1 if lang == 'pa' else 0, horizontal=True)
                btn_text = "✅ Confirm Village Selection" if lang == 'en' else "✅ ਪਿੰਡ ਦੀ ਚੋਣ ਦੀ ਪੁਸ਼ਟੀ ਕਰੋ"
                
                if st.button(btn_text, type="primary"):
                    st.session_state['v_lang'] = 'pa' if report_lang == "Punjabi (ਪੰਜਾਬੀ)" else 'en'
                    st.session_state['v_selected_names'] = selected_names
                    st.session_state['v_confirmed'] = True
                    if st.session_state['v_lang'] == 'pa' and not settings.PUNJABI_FONT_LOADED: utils.register_fonts()
                    st.rerun()

    # --- STEP 2: Assessment Year Selection ---
    if st.session_state.get('v_confirmed') and not st.session_state.get('v_year_confirmed'):
        st.divider()
        
        years_sets = []
        with st.spinner("Loading available assessment years..."):
            for v_name in st.session_state['v_selected_names']:
                records = database.get_village_records(v_name)
                v_years = set()
                for r in records:
                    yr = r.get('Assessment_Year') or r.get('assessment_year')
                    if yr: v_years.add(str(yr).strip())
                years_sets.append(v_years)
        
        common_years = set.intersection(*years_sets) if years_sets else set()
        
        if not common_years:
            st.error("No common assessment years found for the selected village(s)." if st.session_state['v_lang'] == 'en' else "ਚੁਣੇ ਗਏ ਪਿੰਡਾਂ ਲਈ ਕੋਈ ਸਾਂਝਾ ਮੁਲਾਂਕਣ ਸਾਲ ਨਹੀਂ ਮਿਲਿਆ।")
            if st.button("⬅️ Back" if st.session_state['v_lang'] == 'en' else "⬅️ ਪਿੱਛੇ"):
                st.session_state['v_confirmed'] = False
                st.rerun()
        else:
            sorted_years = sorted(list(common_years), reverse=True)
            
            if len(st.session_state['v_selected_names']) == 2:
                st.session_state['v_selected_year'] = sorted_years[0]
                st.session_state['v_year_confirmed'] = True
                st.rerun()
            else:
                st.markdown("### 📅 Select Assessment Year" if st.session_state['v_lang'] == 'en' else "### 📅 ਮੁਲਾਂਕਣ ਸਾਲ ਚੁਣੋ")
                
                selected_year = st.radio(
                    "Available Years:" if st.session_state['v_lang'] == 'en' else "ਉਪਲਬਧ ਸਾਲ:",
                    options=sorted_years,
                    horizontal=True
                )
                
                btn_text = "📊 Generate Final Report" if st.session_state['v_lang'] == 'en' else "📊 ਅੰਤਿਮ ਰਿਪੋਰਟ ਤਿਆਰ ਕਰੋ"
                if st.button(btn_text, type="primary"):
                    st.session_state['v_selected_year'] = selected_year
                    st.session_state['v_year_confirmed'] = True
                    st.rerun()

    # --- STEP 3: Render Report ---
    if st.session_state.get('v_confirmed') and st.session_state.get('v_year_confirmed') and st.session_state.get('v_selected_names'):
        year = st.session_state['v_selected_year']
        with st.spinner("Fetching data..."):
            villages_data = [database.get_village_by_year(v, year) for v in st.session_state['v_selected_names']]
            villages_data = [v for v in villages_data if v]
        
        if not villages_data:
            st.error(f"No data available for the year {year}." if st.session_state['v_lang'] == 'en' else f"ਸਾਲ {year} ਲਈ ਕੋਈ ਡਾਟਾ ਉਪਲਬਧ ਨਹੀਂ ਹੈ।")
            if st.button("⬅️ Back to Year Selection" if st.session_state['v_lang'] == 'en' else "⬅️ ਸਾਲ ਦੀ ਚੋਣ 'ਤੇ ਵਾਪਸ ਜਾਓ"):
                st.session_state['v_year_confirmed'] = False
                st.rerun()
        else:
            utils.render_village_view(villages_data, st.session_state['v_lang'])
            
            st.divider()
            insight_header = "🧠 AI-Generated Insights" if len(villages_data) == 1 else "🧠 Comparative AI Insights"
            if st.session_state['v_lang'] == 'pa': insight_header = utils.get_translation(insight_header)
            st.subheader(insight_header)
            
            cache_key = f"v_insights_{'_'.join(st.session_state['v_selected_names'])}_{year}_{st.session_state['v_lang']}"
            if cache_key not in st.session_state:
                with st.spinner("Analyzing data..."):
                    st.session_state[cache_key] = llm.analyze_village_data(villages_data, st.session_state['v_lang'])
            
            st.markdown(st.session_state[cache_key])
            st.divider()
            
            pdf_bytes = utils.generate_village_pdf(villages_data, st.session_state['v_lang'], st.session_state[cache_key])
            f_name = f"{villages_data[0]['village_name']}_{year}_report.pdf" if len(villages_data) == 1 else f"Comparison_Report_{year}.pdf"
            btn_label = "📥 Download PDF" if st.session_state['v_lang'] == 'en' else "📥 ਪੀਡੀਐਫ ਡਾਊਨਲੋਡ ਕਰੋ"
            st.download_button(label=btn_label, data=pdf_bytes, file_name=f_name, mime="application/pdf", type="primary")