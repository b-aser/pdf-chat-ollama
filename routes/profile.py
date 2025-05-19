from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from forms.auth_forms import ProfileForm
from functools import wraps

bp = Blueprint('profile', __name__, url_prefix='/profile')

@bp.route('/view')
@login_required
def view_profile():
    return render_template('profile/view.html')

@bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileForm(
        original_username=current_user.username,
        original_email=current_user.email
    )
    
    if request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    if form.validate_on_submit():
        # Verify current password
        if not form.current_password.data:
            flash('Current password is required to update profile.', 'danger')
            return render_template('profile/edit.html', form=form)
            
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return render_template('profile/edit.html', form=form)
        
        # Update user information
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        # Update password if provided
        if form.new_password.data:
            current_user.set_password(form.new_password.data)
            
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('profile.view_profile'))
        
    return render_template('profile/edit.html', form=form)

@bp.route('/admin/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    # Only admins can access this route
    if not current_user.is_admin:
        flash('You do not have permission to edit other user profiles.', 'danger')
        return redirect(url_for('profile.view_profile'))
    
    user = User.query.get_or_404(user_id)
    form = ProfileForm(
        original_username=user.username,
        original_email=user.email
    )
    
    if request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
    
    if form.validate_on_submit():
        # Update user information
        user.username = form.username.data
        user.email = form.email.data
        
        # Update password if provided
        if form.new_password.data:
            user.set_password(form.new_password.data)
            
        db.session.commit()
        flash(f'Profile for {user.username} has been updated.', 'success')
        return redirect(url_for('admin.users'))
        
    return render_template('profile/admin_edit.html', form=form, user=user) 