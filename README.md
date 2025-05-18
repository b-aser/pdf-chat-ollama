# PDF Chat

An AI-powered chatbot for summarizing and interacting with multiple PDF documents.

## Features

- User Registration/Login: Secure account creation and login
- Profile Management: Users can view and edit their profile information
- Upload Multiple PDFs: Support uploading and processing multiple files at once
- Text Extraction + Preprocessing: Clean and extract text content from PDFs
- Question Answering: Ask any English question based on uploaded PDF(s)
- Document Summarization: Summarize one or more PDFs on demand
- Multi-Document Chat: Interact with all uploaded documents in a unified chat
- Chat History: View past chats/questions with responses
- Admin Dashboard: Monitor and manage users

## Tech Stack

- **Frontend**: Tailwind CSS and JavaScript
- **Backend**: Flask
- **Database**: SQLite
- **AI/Inference**: Groq API with LLaMA 3 70b model
- **PDF Processing**: PyPDF2

## Setup

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- Ollama
### Installation of Ollama jkug3-v1 model

1. Download Ollama:

2. Open cmd or powershell:
    ```
   ollama run b-aser/jkug3-v1
   ```

### Installation of the system

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/pdf-chat.git
   cd pdf-chat
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create the necessary directories:
   ```
   mkdir uploads
   ```

5. Run the application:
   ```
   python app.py
   ```

6. Open your browser and navigate to: `http://127.0.0.1:5000`

## Usage

### Registration and Login

1. Create an account using email, username, and password
2. Log in with your credentials

### Managing Your Profile

1. Click on the "Profile" link in the navigation bar
2. View your profile information
3. Click "Edit Profile" to update your username, email, or password
4. Enter your current password to confirm changes

### Uploading PDFs

1. Go to the Dashboard and click "Upload PDFs"
2. Drag and drop PDF files or use the file browser
3. Click "Upload Files" to process your documents

### Chatting with PDFs

1. On the Dashboard, click "New Chat"
2. Select one or more PDFs to include in your chat
3. Start asking questions about your documents

### Summarizing PDFs

1. From the Dashboard, select a PDF and click the summary icon
2. View the AI-generated summary of your document

### Administrative Features

1. Create an admin user by running the provided script:
   ```
   python create_admin.py
   ```
   Follow the prompts to create an administrator account.

2. Log in with your admin credentials to access the Admin Dashboard
3. Manage users and view system statistics

#### User Management for Administrators

1. From the Admin Dashboard, click "Manage Users"
2. View a list of all users in the system
3. Edit user profiles by clicking the edit icon - this allows changing usernames, emails, and passwords
4. Toggle admin status using the shield/user icon
5. Delete users using the trash icon

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
