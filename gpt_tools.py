import os
from openai import OpenAI

# Initialize the OpenAI client
client = OpenAI(api_key="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")

def generate_supplier_summary(supplier_info):
    try:
        prompt = f"""Summarise the following supplier profile in a professional business tone, and highlight any risks or negotiation opportunities:\n\n{supplier_info}\n"""
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful procurement assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating supplier summary: {e}")
        return "Unable to generate summary."

def generate_negotiation_email(supplier_name, goal):
    try:
        prompt = f"""Write a persuasive and professional procurement email to {supplier_name}, with the following goal: {goal}. Use a formal and respectful tone."""
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a skilled procurement officer drafting emails."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=250,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating negotiation email: {e}")
        return "Unable to generate email."

def generate_strategy_tips(deal_type):
    try:
        prompt = f"""Give 5 smart negotiation strategies for a procurement deal focused on {deal_type}. Provide them as bullet points."""
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a procurement strategist."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating strategy tips: {e}")
        return "Unable to generate strategy tips."

def extract_supplier_info_structured(supplier_text):
    """
    Extract structured information from supplier profile using LLM.
    Returns a dictionary with fields suitable for comparison table.
    """
    try:
        prompt = f"""
From the supplier profile below, extract the following information in structured JSON format with the exact keys:
- Supplier
- Price per Unit
- Total Price
- Delivery Fee
- Perks
- Discounts
- Delivery Time
- Sustainability Index
- Company Email

Ensure values are concise and return a valid JSON object only.

Supplier Profile:
\"\"\"{supplier_text}\"\"\"
"""
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful AI procurement assistant who returns structured JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=400
        )
        content = response.choices[0].message.content.strip()

        # Try parsing the result as a dictionary
        import json
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Sometimes GPT returns text-wrapped JSON → try extracting the JSON from it
            import re
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            else:
                return {}
    except Exception as e:
        print(f"Error extracting structured supplier info: {e}")
        return {}

