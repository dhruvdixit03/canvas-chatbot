from langchain import hub
from langchain.chat_models import init_chat_model
from langgraph.graph import START, StateGraph
from langchain_core.documents import Document
from typing_extensions import List, TypedDict
from ragatouille import RAGPretrainedModel
import os
from common import INDEX_NAME, check_if_index_exists, download_index_from_s3

# Define TypedDict for state management
class State(TypedDict):
    question: str
    context: List[Document]
    answer: str
    history: List[dict]

def load_rag_model():
    """Load the RAG model from the existing index"""
    # Check if the index exists
    if not check_if_index_exists():
        print("No RAG index found. Please run rag_indexer.py first to create an index.")
        return None
        
    # Download the index from S3 if needed
    if download_index_from_s3():
        # Get the path to the downloaded index
        curr_dir = os.getcwd()
        index_path = os.path.join(curr_dir, ".ragatouille", "colbert", "indexes", INDEX_NAME)
        
        # Load the index using from_index class method
        try:
            rag = RAGPretrainedModel.from_index(index_path)
            print("✅ Loaded RAG index!")
            return rag
        except Exception as e:
            print(f"Error loading RAG index: {e}")
            return None
    else:
        print("Failed to download index from S3.")
        return None

def create_rag_chat_bot():
    # Load the RAG model
    rag = load_rag_model()
    if not rag:
        return None
        
    # Initialize LLM
    llm = init_chat_model("gpt-4o-mini", model_provider="openai")

    # Pull base RAG prompt layout
    prompt = hub.pull("dhruvdixit/canvas-rag-1")
    print(prompt)
    
    # Define retrieve function
    def retrieve(state: State):
        retriever = rag.as_langchain_retriever(k=8)
        retrieved_docs = retriever.invoke(state["question"])  
        return {"context": retrieved_docs, "history": state["history"]}

    # Define generate function
    def generate(state: State):
        docs_content = "\n\n".join(doc.page_content for doc in state["context"])
        formatted_history = "\n".join([f"User: {turn['question']}\nBot: {turn['answer']}" for turn in state["history"]])
        messages = prompt.invoke({"question": state["question"], 
                                "context": docs_content,
                                "history": formatted_history})
        response = llm.invoke(messages)
        return {"answer": response.content}

    # Build RAG pipeline graph
    graph_builder = StateGraph(State).add_sequence([retrieve, generate])
    graph_builder.add_edge(START, "retrieve")
    graph = graph_builder.compile()
    
    return graph

def start_chat_interface():
    # Create the RAG chatbot
    graph = create_rag_chat_bot()
    if not graph:
        print("Failed to create RAG chatbot.")
        return
    
    # Interactive chat loop
    print("Welcome to the RAG chatbot! Type 'exit' to quit.\n")
    history = []
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        
        result = graph.invoke({"question": user_input, "history": history})
        
        history.append({"question": user_input, "answer": result['answer']})

        print(f"Bot: {result['answer']}\n")

if __name__ == "__main__":
    start_chat_interface()