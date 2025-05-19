from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from models import db, PDF, ChatSession, PDFChatSession, ChatMessage
from utils.pdf_processor import process_pdf
from utils.groq_api import ask_question, summarize_text, chat_with_pdfs
import os
import json
import re

bp = Blueprint('chat', __name__, url_prefix='/chat')

# Maximum number of chunks to process per PDF
MAX_CHUNKS_PER_PDF = 5

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_chat():
    if request.method == 'POST':
        pdf_ids = request.form.getlist('pdf_ids')
        
        if not pdf_ids:
            flash('Please select at least one PDF to chat with.', 'danger')
            return redirect(url_for('chat.new_chat'))
        
        # Create a new chat session
        chat_session = ChatSession(
            user_id=current_user.id,
            title="New Chat"
        )
        db.session.add(chat_session)
        db.session.flush()  # This gets the chat_session.id
        
        # Link the chat session with selected PDFs
        for pdf_id in pdf_ids:
            pdf = PDF.query.filter_by(id=pdf_id, user_id=current_user.id).first()
            if pdf:
                pdf_chat = PDFChatSession(
                    pdf_id=pdf.id,
                    chat_session_id=chat_session.id
                )
                db.session.add(pdf_chat)
        
        db.session.commit()
        return redirect(url_for('chat.view_chat', chat_id=chat_session.id))
    
    pdfs = PDF.query.filter_by(user_id=current_user.id, is_processed=True).all()
    return render_template('chat/new_chat.html', pdfs=pdfs)

@bp.route('/<int:chat_id>')
@login_required
def view_chat(chat_id):
    chat_session = ChatSession.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    pdf_sessions = PDFChatSession.query.filter_by(chat_session_id=chat_id).all()
    pdfs = [ps.pdf for ps in pdf_sessions]
    messages = ChatMessage.query.filter_by(session_id=chat_id).order_by(ChatMessage.timestamp).all()
    
    return render_template('chat/view_chat.html', 
                          chat_session=chat_session, 
                          pdfs=pdfs, 
                          messages=messages)

@bp.route('/<int:chat_id>/message', methods=['POST'])
@login_required
def send_message(chat_id):
    chat_session = ChatSession.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    message_content = request.form.get('message')
    
    if not message_content:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    # Save user message
    user_message = ChatMessage(
        content=message_content,
        is_user=True,
        session_id=chat_id
    )
    db.session.add(user_message)
    db.session.commit()
    
    # Get PDFs associated with this chat
    pdf_sessions = PDFChatSession.query.filter_by(chat_session_id=chat_id).all()
    pdfs = [ps.pdf for ps in pdf_sessions]
    
    if not pdfs:
        ai_response = "No PDFs associated with this chat. Please restart with selected PDFs."
    else:
        # Get recent chat history (last 10 messages)
        history = ChatMessage.query.filter_by(session_id=chat_id).order_by(
            ChatMessage.timestamp.desc()).limit(10).all()
        history.reverse()  # Chronological order
        
        chat_history = [{'is_user': msg.is_user, 'content': msg.content} for msg in history]
        
        # Get PDF contents
        pdf_contents = []
        pdf_sources = []  # Track which PDF each chunk belongs to
        
        for i, pdf in enumerate(pdfs):
            # Process the PDF if it hasn't been processed yet
            if not pdf.is_processed:
                try:
                    process_pdf(pdf.file_path)
                    pdf.is_processed = True
                    db.session.commit()
                except Exception as e:
                    return jsonify({'error': f'Error processing PDF: {str(e)}'}), 500
            
            # Extract text
            chunks = process_pdf(pdf.file_path)
            if chunks:
                # Limit to a reasonable number of chunks per PDF to avoid overloading the API
                limited_chunks = chunks[:MAX_CHUNKS_PER_PDF]
                pdf_contents.extend(limited_chunks)
                # Track the source PDF index for each chunk
                pdf_sources.extend([i] * len(limited_chunks))
        
        # Get AI response
        try:
            ai_response = chat_with_pdfs(message_content, pdf_contents, chat_history, pdf_sources)
        except Exception as e:
            ai_response = f"I encountered an error while processing your request: {str(e)}"
    
    # Process markdown in AI response
    processed_response = process_markdown(ai_response)
    
    # Save AI response
    ai_message = ChatMessage(
        content=processed_response,
        is_user=False,
        session_id=chat_id
    )
    db.session.add(ai_message)
    db.session.commit()
    
    # If this is the first message, update the chat title
    if ChatMessage.query.filter_by(session_id=chat_id).count() <= 2:  # Just the first Q&A
        chat_session.title = message_content[:50] + ('...' if len(message_content) > 50 else '')
        db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': processed_response
    })

def process_markdown(text):
    """Process markdown text to HTML"""
    if not text:
        return ''
    
    # Handle bold text
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Handle italic text
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    
    # Handle code blocks
    text = re.sub(r'```(.*?)```', r'<pre class="bg-gray-100 p-2 rounded my-2"><code>\1</code></pre>', text, flags=re.DOTALL)
    
    # Handle inline code
    text = re.sub(r'`(.*?)`', r'<code class="bg-gray-100 px-1 rounded">\1</code>', text)
    
    # Handle line breaks
    text = text.replace('\n', '<br>')
    
    return text

@bp.route('/<int:chat_id>/delete', methods=['POST', 'GET'])
@login_required
def delete_chat(chat_id):
    chat_session = ChatSession.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    
    # First remove the PDFChatSession associations
    PDFChatSession.query.filter_by(chat_session_id=chat_id).delete()
    
    # Then delete the chat messages
    ChatMessage.query.filter_by(session_id=chat_id).delete()
    
    # Finally delete the chat session
    db.session.delete(chat_session)
    
    db.session.commit()
    
    flash('Chat deleted successfully.', 'success')
    return redirect(url_for('pdf.dashboard'))

@bp.route('/summarize/<int:pdf_id>')
@login_required
def summarize_pdf(pdf_id):
    pdf = PDF.query.filter_by(id=pdf_id, user_id=current_user.id).first_or_404()
    
    try:
        chunks = process_pdf(pdf.file_path)
        if not chunks:
            flash("Could not extract text from the PDF.", "danger")
            return redirect(url_for('pdf.view_pdf', pdf_id=pdf_id))
        
        text = " ".join(chunks)
        summary = summarize_text(text)
        
        # Process markdown in summary to render bold text properly
        processed_summary = process_markdown(summary)
        
        return render_template('pdf/summary.html', pdf=pdf, summary=processed_summary)
    except Exception as e:
        flash(f"Error generating summary: {str(e)}", "danger")
        return redirect(url_for('pdf.view_pdf', pdf_id=pdf_id))

@bp.route('/question/<int:pdf_id>', methods=['GET', 'POST'])
@login_required
def ask_pdf_question(pdf_id):
    pdf = PDF.query.filter_by(id=pdf_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        question = request.form.get('question')
        if not question:
            flash("Please enter a question.", "danger")
            return redirect(url_for('chat.ask_pdf_question', pdf_id=pdf_id))
        
        try:
            chunks = process_pdf(pdf.file_path)
            if not chunks:
                flash("Could not extract text from the PDF.", "danger")
                return redirect(url_for('chat.ask_pdf_question', pdf_id=pdf_id))
            
            text = " ".join(chunks)
            answer = ask_question(question, text)
            
            # Process markdown in answer to render bold text properly
            processed_answer = process_markdown(answer)
            
            return render_template('pdf/question_answer.html', 
                                   pdf=pdf, 
                                   question=question, 
                                   answer=processed_answer)
        except Exception as e:
            flash(f"Error processing question: {str(e)}", "danger")
            return redirect(url_for('chat.ask_pdf_question', pdf_id=pdf_id))
    
    return render_template('pdf/ask_question.html', pdf=pdf) 