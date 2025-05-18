from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length, Email, Optional, EqualTo

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    current_password = PasswordField('Current Password')
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[Optional(), EqualTo('new_password', message='Passwords must match')])

    def validate_current_password(self, field):
        if self.new_password.data and not field.data:
            raise ValidationError('Current password is required to set a new password') 