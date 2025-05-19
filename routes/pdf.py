import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, PDF, ChatSession, PDFChatSession
from utils.pdf_processor import process_pdf

bp = Blueprint('pdf', __name__, url_prefix='/pdf')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@bp.route('/dashboard')
@login_required
def dashboard():
    pdfs = PDF.query.filter_by(user_id=current_user.id).all()
    chat_sessions = ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.created_at.desc()).all()
    return render_template('pdf/dashboard.html', pdfs=pdfs, chat_sessions=chat_sessions)

@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'files[]' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        files = request.files.getlist('files[]')
        
        uploaded_files = []
        for file in files:
            if file.filename == '':
                continue
                
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Generate a unique filename to prevent collisions
                unique_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                
                file.save(file_path)
                
                # Create PDF record in the database
                new_pdf = PDF(
                    filename=unique_filename,
                    original_filename=filename,
                    file_path=file_path,
                    user_id=current_user.id,
                    is_processed=False
                )
                
                db.session.add(new_pdf)
                uploaded_files.append(new_pdf)
            else:
                flash(f'Invalid file type for {file.filename}. Only PDF files are allowed.', 'danger')
        
        if uploaded_files:
            db.session.commit()
            # Process PDFs in background (in a real app, this would be a celery task)
            for pdf in uploaded_files:
                try:
                    # Process the PDF
                    process_pdf(pdf.file_path)
                    pdf.is_processed = True
                    db.session.commit()
                except Exception as e:
                    flash(f'Error processing {pdf.original_filename}: {str(e)}', 'danger')
            
            flash(f'Successfully uploaded {len(uploaded_files)} PDF files.', 'success')
            
        return redirect(url_for('pdf.dashboard'))
        
    return render_template('pdf/upload.html')

@bp.route('/delete/<int:pdf_id>', methods=['POST'])
@login_required
def delete_pdf(pdf_id):
    pdf = PDF.query.filter_by(id=pdf_id, user_id=current_user.id).first_or_404()
    
    # Delete related PDFChatSession records first
    PDFChatSession.query.filter_by(pdf_id=pdf_id).delete()
    
    # Delete the file from storage
    try:
        os.remove(pdf.file_path)
    except OSError:
        pass
    
    # Remove from database
    db.session.delete(pdf)
    db.session.commit()
    
    flash('PDF deleted successfully.', 'success')
    return redirect(url_for('pdf.dashboard'))

@bp.route('/view/<int:pdf_id>')
@login_required
def view_pdf(pdf_id):
    pdf = PDF.query.filter_by(id=pdf_id, user_id=current_user.id).first_or_404()
    return render_template('pdf/view.html', pdf=pdf)

@bp.route('/download/<int:pdf_id>')
@login_required
def download_pdf(pdf_id):
    pdf = PDF.query.filter_by(id=pdf_id, user_id=current_user.id).first_or_404()
    return send_from_directory(os.path.dirname(pdf.file_path), 
                               os.path.basename(pdf.file_path),
                               as_attachment=True,
                               download_name=pdf.original_filename) 