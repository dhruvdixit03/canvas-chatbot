import os
from langchain_community.document_loaders import S3FileLoader
from ragatouille import RAGPretrainedModel
from common import s3, S3_BUCKET_NAME, S3_INDEX_KEY, INDEX_NAME, check_if_index_exists, download_index_from_s3, list_pdf_files
from llama_parse import LlamaParse
import tempfile
from document_classifer import CourseFileClassifier

parser = LlamaParse(
    result_type="markdown",
    api_key=input("Enter your llamaParse API key: "),
    premium_mode=False
)

doc_classifier = CourseFileClassifier()

# index created and uploaded
def upload_index_to_s3():
    """Upload the RAG index to S3"""
    curr_dir = os.getcwd()
    index_dir = os.path.join(curr_dir, ".ragatouille", "colbert", "indexes", INDEX_NAME)
    
    if not os.path.exists(index_dir):
        print(f"Error: Index directory {index_dir} does not exist.")
        return False

    # Upload all files from the index directory
    for root, dirs, files in os.walk(index_dir):
        for file in files:
            local_path = os.path.join(root, file)
            # Calculate relative path from the index_dir
            relative_path = os.path.relpath(local_path, index_dir)
            s3_path = f"{S3_INDEX_KEY}/{relative_path}"
            
            print(f"Uploading {local_path} to s3://{S3_BUCKET_NAME}/{s3_path}")
            
            try:
                s3.upload_file(local_path, S3_BUCKET_NAME, s3_path)
            except Exception as e:
                print(f"Error uploading {local_path}: {e}")
                return False
    
    # Create a marker file to indicate the index is complete
    s3.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=f"{S3_INDEX_KEY}/index_complete.marker",
        Body="Index upload completed"
    )
    
    return True

# index exists so downloading
def download_and_process_pdfs(pdf_files):
    """Download PDFs from S3, process them, and return document texts."""
    all_docs = []
    important_files = doc_classifier.get_classified_set()
    for pdf_file in pdf_files:
        try:
            if str(pdf_file) in important_files:
                print(f"LLAMA PARSE! - {str(pdf_file)}")
                # llama parse it
                # Create a temporary file to store the downloaded PDF
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    # Download the file from S3
                    s3.download_fileobj(S3_BUCKET_NAME, pdf_file, temp_file)
                    temp_file_path = temp_file.name
                
                docs = parser.load_data(temp_file_path)
                # print(docs)
                # put all document texts into one big text so it matches regular parse output
                # texts = ""
                all_docs.extend(docs)
                # for doc in docs:
                #     print(doc.text)
                os.remove(temp_file_path)
                # return
            else:  
                # print(f"Processing {pdf_file}")
                print(f"Regular Parse - {str(pdf_file)}")
                loader = S3FileLoader(S3_BUCKET_NAME, pdf_file)
                docs = loader.load()
                # for doc in docs:
                #     all_docs.extend(doc.page_content)
                all_docs.extend(docs)
                        
            # add regular + llama texts to all_docs
            
            
        except:
            print(f"Could not load {pdf_file}")
    return all_docs

def ingest_pdfs_into_rag():
    """Fetch PDFs, process them, and ingest into RAG model."""
    pdf_files = list_pdf_files()
    if not pdf_files:
        print("No PDFs found in S3.")
        return None

    docs = download_and_process_pdfs(pdf_files)
    
    doc_texts = []
    for doc in docs:
        try:
            doc_texts.append(f"Document: {doc.page_content}")
        except:
            doc_texts.append(f"Document: {doc.text}")
    # doc_texts = [
    # f"Document: {doc.metadata['source']} | {doc.page_content}"
    # for doc in docs
    # ]
    
    # put them in as texts in download_and_process_pdfs
    # doc_texts = docs
    
    # Initialize a new RAG model for indexing
    rag = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")

    # Index into RAG
    # Note: ragatouille will save the index in ~/.ragatouille/colbert/indexes/INDEX_NAME
    rag.index(
        collection=doc_texts,
        index_name=INDEX_NAME,
        split_documents=True,
        use_faiss=True,
    )
    
    # After successful indexing, upload to S3
    if upload_index_to_s3():
        print("🚀 PDF documents successfully indexed into RAG and saved to S3!")
        return rag
    else:
        print("⚠️ Failed to upload index to S3.")
        return None

def initialize_rag():
    """Initialize the RAG model by either loading the existing index or creating a new one."""
    # Check if the index already exists in S3
    if check_if_index_exists():
        print("Existing RAG index found in S3. Downloading...")
        
        # Download the index from S3
        if download_index_from_s3():
            print("🔄 Downloaded existing RAG index from S3!")
            
            # Get the path to the downloaded index
            curr_dir = os.getcwd()
            index_path = os.path.join(curr_dir, ".ragatouille", "colbert", "indexes", INDEX_NAME)
            
            # Load the index using from_index class method
            rag = RAGPretrainedModel.from_index(index_path)
            print("✅ Loaded existing RAG index!")
            return rag
        else:
            print("⚠️ Failed to download index from S3. Creating a new index...")
            return ingest_pdfs_into_rag()
    else:
        print("No existing RAG index found in S3. Creating a new index...")
        return ingest_pdfs_into_rag()

if __name__ == "__main__":
    print("Starting PDF ingestion and RAG index creation...")
    rag = initialize_rag()
    if rag:
        print("Index creation complete! You can now run the chat interface.")
    else:
        print("Failed to create or download the index.")