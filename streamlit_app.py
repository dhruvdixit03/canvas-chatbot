import streamlit as st
from chat_interface import create_rag_chat_bot

st.title("RAG Chatbot")

# Initialize session state for chat history, input, and RAG model
if "history" not in st.session_state:
    st.session_state.history = []
if "input_key" not in st.session_state:
    st.session_state.input_key = "input_0"
if "rag_model" not in st.session_state:
    # Load the RAG model only once and store it in session state
    st.session_state.rag_model = create_rag_chat_bot()

# Display chat history
for chat in st.session_state.history:
    st.write(f"**You:** {chat['question']}")
    st.write(f"**Bot:** {chat['answer']}")
    st.write("---")

# User input
user_input = st.text_input("You: ", key=st.session_state.input_key)

# Handle user input
if user_input:
    if user_input.lower() in ["exit", "quit"]:
        st.write("Goodbye!")
    else:
        # Invoke the RAG chatbot
        result = st.session_state.rag_model.invoke({"question": user_input, "history": st.session_state.history})
        
        # Update chat history
        st.session_state.history.append({"question": user_input, "answer": result['answer']})
        
        # Display the bot's response
        st.write(f"**Bot:** {result['answer']}")
        
        # Clear the input box by updating the input key
        st.session_state.input_key = "input_" + str(len(st.session_state.history))
        st.rerun()