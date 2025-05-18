import os

class Config:

    
    # Groq API Key
    GROQ_API_KEY = "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"
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///pdf_summarizer.db'
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-replace-in-production')
    
    # File upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'pdf'}
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload 
