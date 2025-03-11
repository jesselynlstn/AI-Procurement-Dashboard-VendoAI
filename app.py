import streamlit as st
from gpt_tools import generate_supplier_summary, generate_negotiation_email, extract_supplier_info_structured
from elevenlabs_tools import generate_voice
import PyPDF2
import pandas as pd
import re
import os
import time

# Set page layout
st.set_page_config(page_title="VendoAI Dashboard", layout="wide")

# Create outputs folder
os.makedirs("outputs", exist_ok=True)

# Add centered and enlarged logo at the top
st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
st.image("logo.png", width=180)
st.markdown("</div>", unsafe_allow_html=True)

# Title heading with logo color
st.markdown("<h1 style='text-align: center; font-size: 42px; font-weight: bold; color: #007B7A;'>VendoAI: AI Procurement Assistant Dashboard</h1>", unsafe_allow_html=True)





# Upload Section
st.markdown("<h2 style='margin-top: 40px; color: #007B7A;'>Upload Supplier PDFs</h2>", unsafe_allow_html=True)
uploaded_files = st.file_uploader("Upload up to 3 supplier profiles or contract PDFs", type=["pdf"], accept_multiple_files=True)

supplier_texts = {}
supplier_names = []

if uploaded_files:
    for uploaded_pdf in uploaded_files:
        supplier_name = uploaded_pdf.name.replace(".pdf", "")
        supplier_names.append(supplier_name)
        pdf_reader = PyPDF2.PdfReader(uploaded_pdf)
        extracted_text = ""
        for page in pdf_reader.pages:
            extracted_text += page.extract_text()
        supplier_texts[supplier_name] = extracted_text

# Supplier Summary
if supplier_names:
    st.markdown("<h2 style='margin-top: 40px; color: #007B7A;'>Select a Supplier to View Summary</h2>", unsafe_allow_html=True)
    selected_supplier = st.selectbox("Choose supplier", supplier_names)

    if selected_supplier:
        summary = generate_supplier_summary(supplier_texts[selected_supplier])
        st.markdown("<h3 style='margin-top: 30px; color: #007B7A;'>AI Summary</h3>", unsafe_allow_html=True)
        st.write(summary)

        audio_path = f"outputs/{selected_supplier}_summary.mp3"
        generate_voice(summary, filename=audio_path)
        time.sleep(1)

        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000:
            st.success("Audio summary generated successfully.")
            st.audio(audio_path, format="audio/mp3")
        else:
            st.warning("Audio file not ready or is empty. Please refresh or retry.")

# Comparison Table (HTML wrapped)
if supplier_names:
    st.markdown("<h2 style='margin-top: 40px; color: #007B7A;'>Compare Supplier Details</h2>", unsafe_allow_html=True)
    table_data = []

    for name in supplier_names:
        text = supplier_texts[name]
        structured_output = extract_supplier_info_structured(text)

        def clean_field(val):
            if isinstance(val, dict):
                return ", ".join([f"{k}: {v}" for k, v in val.items()])
            elif isinstance(val, list):
                return ", ".join(str(item) for item in val)
            elif isinstance(val, str):
                return val.replace("{", "").replace("}", "").replace("[", "").replace("]", "").strip()
            else:
                return str(val)

        row = {
            "Supplier": name,
            "Price per Unit": structured_output.get("Price per Unit", "N/A"),
            "Total Price": structured_output.get("Total Price", "N/A"),
            "Delivery Fee": structured_output.get("Delivery Fee", "N/A"),
            "Perks": clean_field(structured_output.get("Perks", "N/A")),
            "Discounts": clean_field(structured_output.get("Discounts", "N/A")),
            "Delivery Time": structured_output.get("Delivery Time", "N/A"),
            "Sustainability Index": structured_output.get("Sustainability Index", "N/A"),
            "Company Email": structured_output.get("Company Email", "N/A")
        }
        table_data.append(row)

    df = pd.DataFrame(table_data)

    def generate_wrapped_html_table(dataframe):
        html = """
        <style>
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid #ccc;
            padding: 8px;
            text-align: left;
            vertical-align: top;
            white-space: normal;
            word-wrap: break-word;
            max-width: 200px;
        }
        th {
            background-color: #f2f2f2;
            color: #007B7A;
        }
        </style>
        <table>
        <thead><tr>""" + "".join([f"<th>{col}</th>" for col in dataframe.columns]) + "</tr></thead><tbody>"

        for _, row in dataframe.iterrows():
            html += "<tr>" + "".join([f"<td>{cell}</td>" for cell in row]) + "</tr>"
        html += "</tbody></table>"
        return html

    st.markdown(generate_wrapped_html_table(df), unsafe_allow_html=True)

# Negotiation Strategy
if supplier_names:
    st.markdown("<h2 style='margin-top: 40px; color: #007B7A;'>Negotiation Strategy and Recommendation</h2>", unsafe_allow_html=True)
    goal = st.text_input("What is your negotiation goal (e.g. cheapest price, longest contract, better delivery time)?")

    if st.button("Suggest Strategy and Recommend Supplier"):
        strategy_prompt = f"""
Given this goal: {goal}

Based on the supplier data below, suggest a negotiation strategy and recommend the best supplier:
"""
        for name in supplier_names:
            strategy_prompt += f"{name}: {supplier_texts[name]}\n"

        strategy_recommendation = generate_supplier_summary(strategy_prompt)
        st.markdown("<h3 style='margin-top: 30px; color: #007B7A;'>AI Recommendation</h3>", unsafe_allow_html=True)
        st.write(strategy_recommendation)

        strategy_audio_path = "outputs/strategy_recommendation.mp3"
        generate_voice(strategy_recommendation, filename=strategy_audio_path)
        time.sleep(1)

        if os.path.exists(strategy_audio_path) and os.path.getsize(strategy_audio_path) > 1000:
            st.success("Strategy audio generated successfully.")
            st.audio(strategy_audio_path, format="audio/mp3")
        else:
            st.warning("Strategy audio file not ready or is empty.")

# Negotiation Email
if supplier_names:
    st.markdown("<h2 style='margin-top: 40px; color: #007B7A;'>Generate Negotiation Email</h2>", unsafe_allow_html=True)
    selected_supplier_email = st.selectbox("Select supplier for email", supplier_names)
    email_goal = st.text_area("What is your email goal?")

    if st.button("Generate Email"):
        email_text = generate_negotiation_email(selected_supplier_email, email_goal)
        st.markdown("<h3 style='margin-top: 30px; color: #007B7A;'>AI Generated Email</h3>", unsafe_allow_html=True)
        st.write(email_text)

        email_audio_path = "outputs/email.mp3"
        generate_voice(email_text, filename=email_audio_path)
        time.sleep(1)

        if os.path.exists(email_audio_path) and os.path.getsize(email_audio_path) > 1000:
            st.success("Email audio generated successfully.")
            st.audio(email_audio_path, format="audio/mp3")
        else:
            st.warning("Email audio file not ready or is empty.")

