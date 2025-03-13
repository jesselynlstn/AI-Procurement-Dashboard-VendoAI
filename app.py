import streamlit as st
from gpt_tools import generate_supplier_summary, generate_negotiation_email, extract_supplier_info_structured
from elevenlabs_tools import generate_voice
import PyPDF2
import pandas as pd
import re
import os
import time
import urllib.parse

# Set page layout
st.set_page_config(page_title="VendoAI Dashboard", layout="wide")

# Create outputs folder
os.makedirs("outputs", exist_ok=True)

# Add centered and enlarged logo at the top
col1, col2, col3 = st.columns([3, 1, 3])
with col2:
    st.image("logo.png", width=180)


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
            
        def extract_numeric_value(value_str):
            if value_str == "N/A" or not value_str:
                return 0
            import re
            # Find all numbers with optional currency symbols
            matches = re.findall(r'(?:£|\$)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', str(value_str))
            if matches:
                # Remove commas and convert to float
                return float(matches[0].replace(',', ''))
            return 0
            
        def extract_discount_percentage(text):
            if text == "N/A" or not text:
                return 0
            import re
            
            future_keywords = ["next order", "future purchase", "loyalty discount"]
            if any(keyword in text.lower() for keyword in future_keywords):
                return 0
            # Look for patterns like "5%" or "5 percent"
            matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', str(text))
            if matches:
                return float(matches[0]) / 100
            return 0
        
        # Get basic values
        total_price_str = structured_output.get("Total Price", "N/A")
        delivery_fee_str = structured_output.get("Delivery Fee", "N/A")
        discount_text = clean_field(structured_output.get("Discounts", "N/A"))
        
        # Extract numeric values and calculate
        total_price = extract_numeric_value(total_price_str)
        
        # Check if delivery is free
        if isinstance(delivery_fee_str, str) and "free" in delivery_fee_str.lower():
            delivery_fee = 0
        else:
            delivery_fee = extract_numeric_value(delivery_fee_str)
            
        # Check if the discount applies to a future order
        future_keywords = ["next order", "future purchase", "loyalty discount"]
        if any(keyword in discount_text.lower() for keyword in future_keywords):
            discount_percentage = 0  # Set to 0 since it's a future discount
            discount_text = "0"  # Display "0" in the Discounts column
        else:
            discount_percentage = extract_discount_percentage(discount_text)
            
        discount_percentage = extract_discount_percentage(discount_text)
        discount_amount = total_price * discount_percentage
        
        # Calculate final price
        final_price = total_price - discount_amount + delivery_fee
        
        # Format with the proper currency symbol
        currency_symbol = "£" if "£" in str(total_price_str) else "$" if "$" in str(total_price_str) else ""
        formatted_final_price = f"{currency_symbol}{final_price:,.2f}"

        row = {
            "Supplier": name,
            "Price per Unit": structured_output.get("Price per Unit", "N/A"),
            "Total Price": structured_output.get("Total Price", "N/A"),
            "Delivery Fee": structured_output.get("Delivery Fee", "N/A"),
            "Discounts": discount_text,
            "Final Price (After Discount + Delivery)": formatted_final_price,
            "Perks": clean_field(structured_output.get("Perks", "N/A")),
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
        .highlight {
            background-color: #e6f7f7;
            font-weight: bold;
        }
        </style>
        <table>
        <thead><tr>""" + "".join([f"<th {'class=\"highlight\"' if col == 'Final Price (After Discount + Delivery)' else ''}>{col}</th>" for col in dataframe.columns]) + "</tr></thead><tbody>"

        for _, row in dataframe.iterrows():
            html += "<tr>" + "".join([f"<td {'class=\"highlight\"' if col == 'Final Price (After Discount + Delivery)' else ''}>{cell}</td>" for col, cell in zip(dataframe.columns, row)]) + "</tr>"
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
        # Create a short strategic voice summary
        # Use LLM to generate strategic voice summary instead of slicing sentences
        voice_summary_prompt = f"""
        Based on the supplier analysis and strategy recommendation above, generate a short voice summary (2-3 sentences) summarising the best supplier to choose and what action the procurement manager should take next. Keep it conversational and useful for audio playback.

        Strategy Recommendation:
        {strategy_recommendation}
        """
        from gpt_tools import generate_supplier_summary
        voice_summary = generate_supplier_summary(voice_summary_prompt)
        generate_voice(voice_summary, filename=strategy_audio_path)
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
        
        import urllib.parse

        # Ensure table_data is defined before accessing it
        if 'table_data' in locals():
            # Extract supplier email from the comparison table data
            supplier_email = None
            for supplier in table_data:
                if supplier["Supplier"] == selected_supplier_email:
                    supplier_email = supplier["Company Email"]
                    break

            if supplier_email and supplier_email != "N/A":
                # Encode email subject and body to be URL safe
                subject = "Negotiation Discussion"
                body = f"Dear Supplier,\n\n{email_text}\n\nBest Regards,\n[Your Name]"
                mailto_link = f"mailto:{supplier_email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"

                # Button to open email client
                st.markdown(f'<a href="{mailto_link}" target="_blank"><button style="background-color:#007B7A; color:white; padding:10px; border:none; border-radius:5px;">Send Email</button></a>', unsafe_allow_html=True)
            else:
                st.warning("Supplier email not available.")
        else:
            st.error("Supplier comparison data is missing. Please ensure suppliers are uploaded.")


