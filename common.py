import boto3
import os
import warnings

# Filter out specific warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="colbert.utils.amp")
warnings.filterwarnings("ignore", category=UserWarning, message="User provided device_type of 'cuda'")

# S3 configuration
S3_BUCKET_NAME = "canvas-files-autodoc"
S3_INDEX_KEY = "rag-index"  # Directory in S3 where index files will be stored
INDEX_NAME = "s3-rag-index"  # Name of the index

# Set API keys
os.environ["OPENAI_API_KEY"] = input("Enter your OpenAI API key: ")
os.environ["LANGCHAIN_API_KEY"] = input("Enter your LangChain API key: ")

s3 = boto3.client("s3")

def check_if_index_exists():
    """Check if the RAG index already exists in S3"""
    try:
        # Look for the existence of a marker file that indicates a complete index
        response = s3.head_object(
            Bucket=S3_BUCKET_NAME,
            Key=f"{S3_INDEX_KEY}/index_complete.marker"
        )
        return True
    except Exception:
        return False

def download_index_from_s3():
    """Download the RAG index from S3"""
    import os
    from pathlib import Path
    
    curr_dir = os.getcwd()
    index_dir = os.path.join(curr_dir, ".ragatouille", "colbert", "indexes", INDEX_NAME)
    
    # Create the directory if it doesn't exist
    os.makedirs(index_dir, exist_ok=True)
    
    # List all objects with the index prefix
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(
        Bucket=S3_BUCKET_NAME, 
        Prefix=S3_INDEX_KEY
    )
    
    for page in pages:
        if 'Contents' not in page:
            continue
            
        for obj in page['Contents']:
            s3_path = obj['Key']
            # Skip the marker file
            if s3_path.endswith("index_complete.marker"):
                continue
                
            # Calculate the local path
            relative_path = os.path.relpath(s3_path, S3_INDEX_KEY)
            local_path = os.path.join(index_dir, relative_path)
            
            # Create directory structure if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            print(f"Downloading s3://{S3_BUCKET_NAME}/{s3_path} to {local_path}")
            
            try:
                s3.download_file(S3_BUCKET_NAME, s3_path, local_path)
            except Exception as e:
                print(f"Error downloading {s3_path}: {e}")
                return False
    
    return True

def list_pdf_files():
    """Fetch all PDF files from the S3 bucket."""
    response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME)

    if "Contents" not in response:
        print("No files found in the bucket.")
        return []

    # Extract full S3 keys (paths) of the PDF files
    pdf_files = [obj["Key"] for obj in response["Contents"]]
    print(f"✅ Found {len(pdf_files)} PDF files.")
    return pdf_files