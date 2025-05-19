import os
import PyPDF2
import nltk
from nltk.tokenize import sent_tokenize

# Download necessary NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file
    """
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None
    
    return text

def preprocess_text(text):
    """
    Clean and preprocess the extracted text
    """
    if not text:
        return ""
    
    # Basic preprocessing
    text = text.replace('\n', ' ')
    text = ' '.join(text.split())
    
    return text

def chunk_text(text, max_chunk_size=2000):
    """
    Split text into manageable chunks for AI processing
    """
    if not text:
        return []
    
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # If adding this sentence would exceed the limit, save the current chunk and start a new one
        if len(current_chunk) + len(sentence) < max_chunk_size:
            current_chunk += sentence + " "
        else:
            # If the current chunk is not empty, add it to the list
            if current_chunk:
                chunks.append(current_chunk.strip())
                
            # If the sentence itself is longer than max_chunk_size, split it
            if len(sentence) > max_chunk_size:
                # Split long sentence into parts (by words)
                words = sentence.split()
                part = ""
                for word in words:
                    if len(part) + len(word) + 1 < max_chunk_size:
                        part += word + " "
                    else:
                        chunks.append(part.strip())
                        part = word + " "
                
                if part:
                    current_chunk = part
                else:
                    current_chunk = ""
            else:
                # Start new chunk with this sentence
                current_chunk = sentence + " "
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def process_pdf(pdf_path):
    """
    Process a PDF file: extract text, preprocess, and chunk
    """
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return []
    
    processed_text = preprocess_text(text)
    text_chunks = chunk_text(processed_text)
    
    return text_chunks 