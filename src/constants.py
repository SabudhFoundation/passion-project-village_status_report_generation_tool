# --- Localization Dictionary (O(1) Memory Lookup) ---
PUNJABI_LABELS = {
    # Sanitation & Waste Management
    "ODF Status": "ਓਡੀਐਫ ਸਥਿਤੀ",
    "Waste Segregation Sheds": "ਕੂੜਾ ਵੱਖ ਕਰਨ ਵਾਲੇ ਸ਼ੈੱਡ",
    "Drainage Facility": "ਪਾਣੀ ਨਿਕਾਸੀ ਸਹੂਲਤ",
    "Community Compost Pits": "ਸਾਂਝੇ ਖਾਦ ਟੋਏ",
    
    # Governance & LSDG Performance
    "Overall Category": "ਕੁੱਲ ਸ਼੍ਰੇਣੀ",
    "Poverty Free Score": "ਗਰੀਬੀ ਮੁਕਤ ਸਕੋਰ",
    "Healthy Village Score": "ਸਿਹਤਮੰਦ ਪਿੰਡ ਸਕੋਰ",
    "Child Friendly Score": "ਬਾਲ ਅਨੁਕੂਲ ਸਕੋਰ",
    "Socially Just Score": "ਸਮਾਜਿਕ ਨਿਆਂ ਸਕੋਰ",
    
    # Water Security (JJM)
    "JJM Certification Status": "JJM ਪ੍ਰਮਾਣੀਕਰਨ ਸਥਿਤੀ",
    "PWS Available": "PWS ਉਪਲਬਧ ਹੈ",
    "Total Households": "ਕੁੱਲ ਘਰ",
    "Total Tap Connections": "ਕੁੱਲ ਟੂਟੀ ਕਨੈਕਸ਼ਨ",
    
    # Employment (MGNREGA)
    "Total Registered HH": "ਕੁੱਲ ਰਜਿਸਟਰਡ ਘਰ",
    "Total Registered Persons": "ਕੁੱਲ ਰਜਿਸਟਰਡ ਵਿਅਕਤੀ",
    "SC Persons Employed": "ਰੁਜ਼ਗਾਰ ਪ੍ਰਾਪਤ SC ਵਿਅਕਤੀ",
    "Female Persons Employed": "ਰੁਜ਼ਗਾਰ ਪ੍ਰਾਪਤ ਔਰਤਾਂ",
    
    # UI Domains
    "Sanitation & Waste Management": "ਸੈਨੀਟੇਸ਼ਨ ਅਤੇ ਰਹਿੰਦ-ਖੂੰਹਦ ਪ੍ਰਬੰਧਨ",
    "Governance & LSDG Performance": "ਗਵਰਨੈਂਸ ਅਤੇ LSDG ਪ੍ਰਦਰਸ਼ਨ",
    "Water Security (JJM)": "ਪਾਣੀ ਦੀ ਸੁਰੱਖਿਆ (JJM)",
    "Employment (MGNREGA)": "ਰੁਜ਼ਗਾਰ (MGNREGA)",
}

# Maps (Domain_Index, Domain_Title, Main_Score_Key, [ (Metric_Label, JSON_Path) ])
domains = [
    (1, "Sanitation & Waste Management", "sanitation.odf_declaration_status", [
        ("ODF Status", "sanitation.odf_declaration_status"),
        ("Waste Segregation Sheds", "sanitation.waste_collection_and_segregation_sheds_in_the_village"),
        ("Drainage Facility", "sanitation.drainage_facility_available_in_village"),
        ("Community Compost Pits", "sanitation.community_compost_pits")
    ]),
    (2, "Governance & LSDG Performance", "governance.overall_score", [
        ("Overall Category", "governance.overall_category"),
        ("Poverty Free Score", "governance.t1_poverty_free_score"),
        ("Healthy Village Score", "governance.t2_healthy_score"),
        ("Child Friendly Score", "governance.t3_child_friendly_score"),
        ("Socially Just Score", "governance.t7_socially_just_score")
    ]),
    (3, "Water Security (JJM)", "water_security.jjm_status", [
        ("JJM Certification Status", "water_security.jjm_status"),
        ("PWS Available", "water_security.is_pws_available"),
        ("Total Households", "water_security.total_households"),
        ("Total Tap Connections", "water_security.total_tap_connections")
    ]),
    (4, "Employment (MGNREGA)", "employment.total_registered_hh", [
        ("Total Registered HH", "employment.total_registered_hh"),
        ("Total Registered Persons", "employment.total_registered_persons"),
        ("SC Persons Employed", "employment.sc_persons"),
        ("Female Persons Employed", "employment.female_persons")
    ]),
]