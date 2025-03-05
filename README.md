# Canvas Files Auto-Documentation RAG

A system that automatically downloads, classifies, and indexes files from Canvas LMS courses to create a searchable document repository with an intelligent chatbot interface.

## Overview

This project automates the process of retrieving course files from Canvas, intelligently classifying important documents (such as syllabi and schedules), indexing them using RAG (Retrieval-Augmented Generation), and providing a natural language chat interface for retrieving information from course materials.

## Features

- **Canvas API Integration**: Automatically fetches files from your enrolled Canvas courses
- **Intelligent Document Classification**: Uses LLMs to identify critical course documents like syllabi and schedules
- **Document Processing**: Parses PDFs with high-quality extraction via LlamaParse
- **RAG Indexing**: Creates and maintains a searchable index of all course documents
- **S3 Storage**: Stores documents and indexes in Amazon S3 for persistence
- **Chat Interface**: Provides a natural language interface to query course information
- **Streamlit Web App**: Offers a user-friendly web interface for the chat functionality

## Prerequisites

- Python 3.8+
- AWS account with S3 access
- Canvas LMS API key
- OpenAI API key
- LangChain API key
- LlamaParse API key

## Setup

1. Clone this repository
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Configure your AWS credentials:
   ```
   aws configure
   ```
4. Set your API keys when prompted during execution

## Project Structure

- **canvas_api.py**: Connects to Canvas LMS and downloads course files to S3
- **document_classifier.py**: Classifies course documents by type (syllabus, schedule)
- **rag_indexer.py**: Processes documents and creates a searchable RAG index
- **chat_interface.py**: Provides a CLI chat interface to query course documents
- **streamlit_app.py**: Provides a web-based chat interface
- **common.py**: Shared utilities and configuration

## Usage

### 1. Download Course Files

```
python canvas_api.py
```
This will connect to Canvas, download files from your enrolled courses, and store them in S3.

### 2. Build the RAG Index

```
python rag_indexer.py
```
This will:
- Classify important documents (syllabi and schedules)
- Use LlamaParse for high-quality extraction of these documents
- Process all other documents with standard extraction
- Create a searchable RAG index
- Upload the index to S3 for persistence

### 3. Start the Chat Interface

#### Command Line Interface
```
python chat_interface.py
```

#### Web Interface
```
streamlit run streamlit_app.py
```

## System Architecture

1. **File Acquisition**: 
   - Connect to Canvas API
   - Download files from enrolled courses
   - Store in S3 bucket

2. **Document Classification**:
   - Use LLMs to identify syllabi and schedules
   - Apply premium parsing to important documents
   - Apply standard parsing to other documents

3. **RAG Indexing**:
   - Index documents using ColBERT retrieval model
   - Store index in S3 for persistence

4. **Query Interface**:
   - Load index for retrieval
   - Use LLM to generate answers from retrieved contexts
   - Provide chat history for conversational context

## Additional Information

### S3 Structure
- `canvas-files-autodoc/[course_name]/[module_name]/[file_name]`: Course files
- `canvas-files-autodoc/rag-index/`: RAG index files

### Technical Components
- **Retrieval**: RAGatouilleModel with ColBERT indexing
- **Generation**: GPT-4o-mini for chat responses
- **File Processing**: LlamaParse for premium document processing
- **Web Interface**: Streamlit for user interaction

## Troubleshooting

- **Missing Index**: If the chat interface fails to start, ensure you've run `rag_indexer.py` first
- **API Key Issues**: Make sure all required API keys are entered correctly
- **S3 Access**: Verify your AWS credentials have proper S3 bucket access

## Future Improvements

- Document update detection to refresh the index
- Multi-user support for different Canvas accounts
- Enhanced document classification for more document types
- Performance optimizations for larger document collections
