import requests
import json
from config import Config

# Configure Hugging Face API key and endpoint
API_URL = "https://router.huggingface.co/cohere/compatibility/v1/chat/completions"
HF_API_KEY = Config.HF_API_KEY
MODEL = "command-a-03-2025"  # Using the specified model from Hugging Face


def get_headers():
    """Return the headers needed for Huggingface API requests"""
    return {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }
def query(payload):
    """
    Send a query to the Hugging Face API and return the response
    
    Args:
        payload (dict): The payload containing the messages, model, and other parameters
    
    Returns:
        dict: The raw JSON response from the API
    """
    try:
        response = requests.post(API_URL, headers=get_headers(), json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error in query: {e}")
        return {"error": str(e)}

def ask_question(question, context):
    """
    Ask a question to the Hugging Face API and return the response
    
    Args:
        question (str): The question to ask
        context (str): The context to consider when answering the question
    
    Returns:
        str: The answer from the Hugging Face API
    """
    messages = [
        {
            "role": "system",
            "content": """You are a document assistant that ONLY answers questions based on the provided context. 
If the question is not directly answerable from the document, respond with: 
"I can only answer questions related to the document content. This question cannot be answered based on the provided document."
Never use external knowledge or make assumptions beyond what's explicitly stated in the document."""
        },
        {
            "role": "user",
            "content": f"Context from document:\n{context}\n\nQuestion: {question}"
        }
    ]
    
    payload = {
        "messages": messages,
        "max_tokens": 1024,
        "model": MODEL,
        "temperature": 0.0  # Lower temperature for more deterministic responses
    }
    
    try:
        response = requests.post(API_URL, headers=get_headers(), json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error in ask_question: {e}")
        return f"I encountered an error while trying to answer your question: {str(e)}"

# Example usage
if __name__ == "__main__":
    context = "France is a country in Africa. Its capital city is Nairobi."
    question = "What is the capital of France?"
    answer = ask_question(question, context)
    print(answer)


def summarize_text(text):
    """
    Generate a summary of the provided text
    
    Args:
        text (str): The text to summarize
    
    Returns:
        str: The summary from the Groq API
    """
    messages = [
        {"role": "system", "content": "You are a document summarization assistant. Provide a concise but comprehensive summary of the text provided, focusing ONLY on information explicitly stated in the document."},
        {"role": "user", "content": f"Please summarize the following document:\n\n{text}"}
    ]
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.1,  # Low temperature for more consistent summaries
        "max_tokens": 1024
    }
    
    try:
        response = requests.post(API_URL, headers=get_headers(), json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error in summarize_text: {e}")
        return f"I encountered an error while trying to summarize the text: {str(e)}"

def chat_with_pdfs(message, pdf_contents, chat_history=None, pdf_sources=None):
    """
    Generate a response based on PDF contents and chat history
    
    Args:
        message (str): The user's message
        pdf_contents (list): List of PDF contents
        chat_history (list, optional): Chat history. Defaults to None.
        pdf_sources (list, optional): List indicating which PDF each chunk belongs to. Defaults to None.
    
    Returns:
        str: The response from the Groq API
    """
    if chat_history is None:
        chat_history = []
    
    if pdf_sources is None:
        # If no sources provided, assume one chunk per PDF
        pdf_sources = list(range(len(pdf_contents)))
    
    # Prepare system message with strict instructions
    system_message = """You are a document assistant that ONLY answers questions based on the provided document content.
Follow these strict rules:
1. ONLY answer questions that can be directly answered from the document content provided.
2. If a question cannot be answered with information from the documents, respond with: 
   "I can only answer questions related to the document content. Your question cannot be answered based on the documents provided."
3. Do not use any external knowledge beyond what's in the documents.
4. Do not make assumptions or inferences beyond what is explicitly stated.
5. If asked for opinions, judgments, advice, or anything outside the document scope, politely redirect to document content only.
6. Refuse to engage with any requests that are not about understanding or extracting information from the documents.
7. When referencing the documents, be clear about the true number of source PDFs - there are only as many actual documents as there are unique document numbers in the context.
8. If asked about the number of documents, always count the number of unique document numbers, not the number of content chunks.
"""
    
    # Limit the total content to avoid request size issues
    MAX_CONTENT_LENGTH = 12000  # Characters (significantly reduced to avoid 413 errors)
    MAX_HISTORY_ITEMS = 4      # Limit chat history to most recent exchanges
    
    # Format PDF contents for the API
    limited_pdf_contents = []
    total_length = 0
    pdf_tracking = []  # Keep track of which PDF each chunk belongs to
    
    # Sort chunks by potential relevance (could be improved with embeddings/semantic search)
    # For now, just use basic keyword matching
    keywords = message.lower().split()
    scored_chunks = []
    
    # Score each chunk for relevance to the query
    for i, chunk in enumerate(pdf_contents):
        chunk_lower = chunk.lower()
        score = sum(1 for keyword in keywords if keyword in chunk_lower)
        pdf_index = pdf_sources[i]  # Get the source PDF for this chunk
        scored_chunks.append((score, chunk, pdf_index, i))
    
    # Sort by score, highest first
    scored_chunks.sort(reverse=True)
    
    # Take most relevant chunks until we hit the limit
    for _, chunk, pdf_idx, _ in scored_chunks:
        if total_length + len(chunk) > MAX_CONTENT_LENGTH:
            # If even the first chunk is too big, truncate it
            if not limited_pdf_contents:
                truncated = chunk[:MAX_CONTENT_LENGTH]
                limited_pdf_contents.append(truncated)
                pdf_tracking.append(pdf_idx)
                total_length = len(truncated)
            break
        
        limited_pdf_contents.append(chunk)
        pdf_tracking.append(pdf_idx)
        total_length += len(chunk)
    
    # Format PDF contents for the API
    if limited_pdf_contents:
        # Group chunks by PDF source
        pdf_contents_grouped = {}
        for i, (content, pdf_idx) in enumerate(zip(limited_pdf_contents, pdf_tracking)):
            if pdf_idx not in pdf_contents_grouped:
                pdf_contents_grouped[pdf_idx] = []
            pdf_contents_grouped[pdf_idx].append(content)
        
        # Format grouped content
        pdf_sections = []
        num_pdfs = len(pdf_contents_grouped)
        
        # Add metadata about the total number of documents
        pdf_content_text = f"IMPORTANT NOTE: There are {num_pdfs} documents (PDFs) in total.\n\n"
        
        for pdf_idx, contents in pdf_contents_grouped.items():
            section = f"Document {pdf_idx + 1} (PDF):\n" + "\n\n".join(contents)
            pdf_sections.append(section)
        
        pdf_content_text += "\n\n---\n\n".join(pdf_sections)
    else:
        pdf_content_text = "No relevant document content found."
    
    # Limit chat history to most recent exchanges
    limited_history = chat_history[-MAX_HISTORY_ITEMS:] if len(chat_history) > MAX_HISTORY_ITEMS else chat_history
    
    # Format the messages for the API
    messages = [
        {"role": "system", "content": system_message}
    ]
    
    # Add context
    messages.append({"role": "user", "content": f"Here are the document contents to reference:\n\n{pdf_content_text}"})
    messages.append({"role": "assistant", "content": "I'll help you with questions about these documents, but I can only respond based on their content."})
    
    # Add limited chat history
    for entry in limited_history:
        if entry.get('is_user', False):
            messages.append({"role": "user", "content": entry["content"]})
        else:
            messages.append({"role": "assistant", "content": entry["content"]})
    
    # Add current message
    messages.append({"role": "user", "content": message})
    
    # Prepare the API request
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.0,  # Zero temperature for more deterministic responses
        "max_tokens": 1024
    }
    
    try:
        response = requests.post(API_URL, headers=get_headers(), json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error in chat_with_pdfs: {e}")
        return f"I encountered an error while processing your request: {str(e)}" 
