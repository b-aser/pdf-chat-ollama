import os
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, current_user
from models import db, User
from config import Config
import routes.auth
import routes.pdf
import routes.chat
import routes.admin
import routes.profile
from datetime import datetime

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    app.register_blueprint(routes.auth.bp)
    app.register_blueprint(routes.pdf.bp)
    app.register_blueprint(routes.chat.bp)
    app.register_blueprint(routes.admin.bp)
    app.register_blueprint(routes.profile.bp)
    
    # Context processor for templates
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('pdf.dashboard'))
        return render_template('index.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True) 