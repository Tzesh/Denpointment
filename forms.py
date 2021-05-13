from wtforms import Form, StringField, PasswordField, SelectField, DateField, validators


# User Registration Form
class RegistrationForm(Form):
    ssn = StringField("SSN", validators=[validators.length(min=10, max=15),
                                         validators.data_required(message="Please enter your SSN")])
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
    email = StringField("Email", validators=[validators.length(min=8, max=50),
                                             validators.Email(message="Please enter a valid email")])
    password = PasswordField("Password", validators=[
        validators.data_required(message="Please type a password"),
        validators.equal_to(fieldname="confirm", message="Passwords not matching")])
    confirm = PasswordField("Re-enter your password")
