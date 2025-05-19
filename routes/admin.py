from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, PDF, ChatSession, PDFChatSession
from datetime import datetime, timedelta

bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin-only decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    total_pdfs = PDF.query.count()
    total_chats = ChatSession.query.count()
    
    # Get recent users (last 7 days)
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    recent_users = User.query.filter(User.created_at >= one_week_ago).count()
    
    # Get users list
    users = User.query.order_by(User.created_at.desc()).all()
    
    return render_template('admin/dashboard.html', 
                          total_users=total_users,
                          total_pdfs=total_pdfs,
                          total_chats=total_chats,
                          recent_users=recent_users,
                          users=users)

@bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@bp.route('/toggle_admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    # Admin cannot remove their own admin rights
    if user_id == current_user.id:
        flash('You cannot remove your own admin privileges.', 'danger')
        return redirect(url_for('admin.users'))
    
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    
    flash(f'Admin status for {user.username} has been {"granted" if user.is_admin else "revoked"}.', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    # Admin cannot delete themselves
    if user_id == current_user.id:
        flash('You cannot delete your own account through the admin panel.', 'danger')
        return redirect(url_for('admin.users'))
    
    user = User.query.get_or_404(user_id)
    
    # First, delete all chat sessions associated with the user 
    # (this will cascade delete messages due to relationship definition)
    chat_sessions = ChatSession.query.filter_by(user_id=user_id).all()
    for chat in chat_sessions:
        # Delete PDFChatSession records
        PDFChatSession.query.filter_by(chat_session_id=chat.id).delete()
        # Delete the chat session itself
        db.session.delete(chat)
    
    # Delete user's PDFs from storage
    pdfs = PDF.query.filter_by(user_id=user_id).all()
    for pdf in pdfs:
        try:
            import os
            os.remove(pdf.file_path)
        except (OSError, FileNotFoundError):
            pass
        # Delete the PDF record
        db.session.delete(pdf)
    
    # Commit changes to delete related records first
    db.session.commit()
    
    # Now delete the user
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.username} has been deleted.', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/stats')
@login_required
@admin_required
def stats():
    # Total documents by user
    user_docs = db.session.query(
        User.username, 
        db.func.count(PDF.id)
    ).join(PDF, User.id == PDF.user_id, isouter=True).group_by(User.id).all()
    
    # Total chats by user
    user_chats = db.session.query(
        User.username, 
        db.func.count(ChatSession.id)
    ).join(ChatSession, User.id == ChatSession.user_id, isouter=True).group_by(User.id).all()
    
    return render_template('admin/stats.html', 
                           user_docs=user_docs,
                           user_chats=user_chats) 