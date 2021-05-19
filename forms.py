# Denpointment System - Forms
# github.com/Tzesh/Denpointment

from datetime import date

from wtforms import Form, StringField, PasswordField, SelectField, DateField, validators


# User Registration Form
class RegistrationForm(Form):
    ssn = StringField("SSN", validators=[validators.length(min=10, max=15),
                                         validators.data_required(message="Please enter your SSN"),
                                         validators.Regexp(regex='[0-9]',
                                                           message="Invalid input please enter only digits")])
    email = StringField("Email", validators=[validators.length(min=8, max=50),
                                             validators.Email(message="Please enter a valid email")])
    first_name = StringField("First name", validators=[validators.length(min=4, max=50), validators.data_required(
        message="Please enter your first name")])
    last_name = StringField("Last name", validators=[validators.length(min=4, max=50),
                                                     validators.data_required(message="Please enter your last name")])
    gender = SelectField("Gender", choices=[('female', 'Female'), ('male', 'Male')],
                         validators=[validators.data_required(message="Please select your gender")])
    birth_date = DateField("Birth date", format='%Y-%m-%d',
                           validators=[validators.data_required(message="Please enter your birth date")])
    password = PasswordField("Password", validators=[
        validators.data_required(message="Please type a password"),
        validators.equal_to(fieldname="confirm", message="Passwords not matching")])
    confirm = PasswordField("Re-enter your password")


# User Login Form
class LoginForm(Form):
    email = StringField("Email", validators=[validators.length(min=8, max=50),
                                             validators.Email(message="Please enter a valid email")])
    password = PasswordField("Password", validators=[
        validators.data_required(message="Please type a password")])


# Phone Form
class PhoneForm(Form):
    contact_number = StringField("Phone", validators=[validators.data_required(message="Please enter a phone number"),
                                                      validators.length(min=10, max=15),
                                                      validators.Regexp(regex='[0-9]',
                                                                        message="Invalid input please enter only digits")])


# Address Form
class AddressForm(Form):
    city = StringField("City", validators=[validators.length(min=3, max=20),
                                           validators.data_required(message="Please enter your city")])
    street = StringField("Street", validators=[validators.length(min=3, max=20),
                                               validators.data_required(message="Please enter your street")])
    zip_code = StringField("ZIP Code", validators=[validators.length(min=3, max=10),
                                                   validators.data_required(message="Please enter your zip code"),
                                                   validators.Regexp(regex='[0-9]',
                                                                     message="Invalid input please enter only digits")])


# Chronic Disease Form
class ChronicDiseaseForm(Form):
    chronic_disease = StringField("Chronic disease", validators=[validators.length(min=3, max=50),
                                                                 validators.data_required(
                                                                     message="Please enter your chronic disease"),
                                                                 validators.Regexp(r'^[\w.@+-]+$',
                                                                                   message="Please do not use spaces")])


# Change Password Form
class ChangePasswordForm(Form):
    old_password = PasswordField("Password", validators=[
        validators.data_required(message="Please enter your current password")])
    password = PasswordField("Password", validators=[
        validators.data_required(message="Please type a password"),
        validators.equal_to(fieldname="confirm", message="Passwords not matching")])
    confirm = PasswordField("Re-enter your password")


# Change Email Form
class ChangeEmailForm(Form):
    email = StringField("Email", validators=[
        validators.length(min=8, max=50, message="Email must be at least 8 characters and at most 50 characters"),
        validators.Email(message="Please enter a valid email")])
    password = PasswordField("Password", validators=[
        validators.data_required(message="Please type a password"),
        validators.equal_to(fieldname="confirm", message="Passwords not matching")])
    confirm = PasswordField("Re-enter your password")


# Book Appointment Form
class BookAppointmentForm(Form):
    dentist = SelectField("Dentist", validators=[validators.data_required(message="Please select a dentist")])
    date = DateField("Date", format='%Y-%m-%d', default=date.today,
                     validators=[
                         validators.data_required(
                             message="Please enter a starting date to look for an appointment")])
    hour = SelectField("Hour", validators=[validators.data_required(message="Please select an hour")])


# Add Holiday Form
class AddHolidayForm(Form):
    date = DateField("Date", format='%Y-%m-%d', default=date.today,
                     validators=[
                         validators.data_required(
                             message="Please enter a starting date to look for an appointment")])
    reason = StringField("Reason (not mandatory)",
                         validators=[validators.length(max=25, message="Reason must be at most 25 characters")])


# Treatment Form
class TreatmentForm(Form):
    action = StringField("Action", validators=[validators.data_required(message="Please type the action"),
                                               validators.length(max=25, min=5)])
    complaint = StringField("Complaint", validators=[validators.data_required(message="Please type the complaint"),
                                                     validators.length(max=25, min=5)])
    charge = StringField("Charge", validators=[validators.data_required(message="Please enter the charge"),
                                               validators.length(min=2, max=11,
                                                                 message="Charge must be at least 2 characters and at most 11 characters"),
                                               validators.Regexp(regex='[0-9]',
                                                                 message="Invalid input please enter only numbers")])
    description = StringField("Description (Not mandatory)", validators=[
        validators.length(max=25, message="Description must be at most 25 characters")])


# Medicine Form
class MedicineForm(Form):
    medicine_name = StringField("Medicine",
                                validators=[validators.data_required(message="Please type name of the medicine"),
                                            validators.length(max=50, min=5,
                                                              message="Medicine name must be at least 5 characters and at most 50 characters")])


# Search Treatment Form
class SearchTreatmentForm(Form):
    date = DateField("Date", format='%Y-%m-%d', default=date.today,
                     validators=[
                         validators.data_required(
                             message="Please enter a starting date to look for treatments")])
