#!/usr/bin/env python

import os
import sys
from getpass import getpass
from app import create_app
from models import db, User

def create_admin_user(username, email, password):
    """
    Create a new admin user
    """
    # Check if user already exists
    user = User.query.filter_by(username=username).first()
    if user:
        print(f"Error: Username '{username}' already exists.")
        return False
        
    email_user = User.query.filter_by(email=email).first()
    if email_user:
        print(f"Error: Email '{email}' already registered.")
        return False
    
    # Create new admin user
    new_user = User(
        username=username,
        email=email,
        is_admin=True
    )
    new_user.set_password(password)
    
    db.session.add(new_user)
    db.session.commit()
    
    print(f"Admin user '{username}' created successfully!")
    return True

def main():
    """
    Main function to create an admin user from the command line
    """
    print("=== Create Admin User ===")
    
    # Initialize the Flask app context
    app = create_app()
    with app.app_context():
        # Check if there are any admin users
        admin_count = User.query.filter_by(is_admin=True).count()
        if admin_count > 0:
            print(f"There are already {admin_count} admin users in the database.")
            proceed = input("Do you want to create another admin user? (y/n): ")
            if proceed.lower() != 'y':
                print("Operation cancelled.")
                return
        
        # Get user information
        username = input("Username: ")
        email = input("Email: ")
        password = getpass("Password: ")
        confirm_password = getpass("Confirm password: ")
        
        # Validate inputs
        if not username or not email or not password:
            print("Error: All fields are required.")
            return
        
        if password != confirm_password:
            print("Error: Passwords do not match.")
            return
        
        # Create the admin user
        create_admin_user(username, email, password)

if __name__ == "__main__":
    main() 