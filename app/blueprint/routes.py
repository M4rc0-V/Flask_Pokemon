from flask import render_template, request, flash, redirect, url_for
from ...forms import LoginForm, RegisterForm, EditProfileForm
from ... import bp as auth
from ..models import User
from flask_login import login_user, login_required, logout_user, current_user
from . import app



@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        # LOGIN THE USER HERE
        email = form.email.data.lower()
        password = form.password.data
        if email in app.config.get('REGISTERED_USERS') and \
            password == app.config.get('REGISTERED_USERS').get(email).get('password'):
            #Login Success!!!
            return f"Login Success Welcome { app.config.get('REGISTERED_USERS').get(email).get('name') }"
        error_string = "Incorrect Email/Password Combo"
        return render_template('login.html.j2', loginerror=error_string, form=form)
    return render_template('login.html.j2', form=form)
@app.route('/register', methods=["GET","POST"])
def register():
    form = RegisterForm()
    if request.method == 'POST' and form.validate_on_submit():
        return "Welcome To our App... Thanks for registering"
    return render_template('register.html.j2', form=form)
@auth.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    form = EditProfileForm()
    if request.method == 'POST' and form.validate_on_submit():
        edited_user_data = {
            "first_name": form.first_name.data.title(),
            "last_name": form.last_name.data.title(),
            "email": form.email.data.lower(),
            "password": form.password.data,
            "icon": form.icon.data
        }
        user = User.query.filter_by(email = edited_user_data["email"].first())
        if user and user.email != current_user.email:
            flash('Email is already in use', 'danger')
            return redirect('/edit_profile')
        current_user.from_dict(edited_user_data)
        current_user.save()
        flash("Profile updated", 'success')
    return render_template('register.html.j2',form=form)