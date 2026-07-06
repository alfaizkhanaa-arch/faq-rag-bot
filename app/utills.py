import streamlit as st
def display_chat(messages) :
    for msg in messages:
        role = " human" if  msg['role'] == "human" else "ai"
        
        with st.chat_message(role):
            st.write(msg['content'])
            
            if msg["role"] == "ai":
                if "confidence" in msg:
                    conf   = msg["confidence"]
                    source = msg.get("source", "Unknown")

                    if conf == "High":
                        st.success(
                            f"Confidence: {conf} | "
                            f"Source: {source}"
                        )
                    elif conf == "Medium":
                        st.warning(
                            f"Confidence: {conf} | "
                            f"Source: {source}"
                        )
                    else:
                        st.error(
                            f"Confidence: {conf} | "
                            f"Source: {source}"
                        )