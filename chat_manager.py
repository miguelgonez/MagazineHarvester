import os
from openai import OpenAI
import streamlit as st
from typing import List, Dict

class ChatManager:
    def __init__(self):
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
    def chat_with_pdf(self, pdf_text: str, user_message: str) -> str:
        try:
            messages = [
                {"role": "system", "content": "You are a helpful academic assistant analyzing research papers. "
                 "Provide clear and concise responses about the paper's content."},
                {"role": "user", "content": f"Paper content: {pdf_text}\n\nUser question: {user_message}"}
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"Error in chat processing: {str(e)}")
            return "Sorry, I encountered an error while processing your request."
