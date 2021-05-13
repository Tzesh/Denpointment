from flask import Flask, render_template, flash, redirect, url_for, session, request
from flask_mysqldb import MySQL
from passlib.handlers.sha2_crypt import sha256_crypt
from forms import LoginForm, RegistrationForm, PhoneForm, AddressForm, ChangePasswordForm, ChangeEmailForm
from utils import login_required, check_is_patient, check_is_dentist, check_dentist, check_patient

app = Flask(__name__)
app.secret_key = "too_secret_to_reveal"
app.static_folder = 'static'

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "dentist_management_system"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)


# Login page
@app.route('/', methods=["GET", "POST"])
def index():
    form = LoginForm(request.form)
    if "logged_in" in session:
        return redirect(url_for("member_area"))
    if request.method == "POST":
        email = form.email.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        query = "SELECT * FROM Persons WHERE email = %s"
        result_set = cursor.execute(query, (email,))
        if result_set > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered, real_password):
                ssn = data["ssn"]
                full_name = data["first_name"] + " " + data["last_name"]

                session["logged_in"] = True
                session["full_name"] = full_name
                session["email"] = email
                session["ssn"] = ssn
                session["is_patient"] = check_is_patient(ssn, mysql)
                session["is_dentist"] = check_is_dentist(ssn, mysql)

                flash("You have successfully logged in.", "success")
                return redirect(url_for("member_area"))
            else:
                flash("Your password is wrong.", "danger")
                return redirect(url_for("index"))
        else:
            flash("There is no such email has been registered.", "danger")
            return redirect(url_for("index"))
    return render_template("login.html", form=form)


# Register page
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegistrationForm(request.form)
    if "logged_in" in session:
        return redirect(url_for("member_area"))
    if request.method == "POST" and form.validate():
        ssn = form.ssn.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        gender = form.gender.data
        birth_date = form.birth_date.data
        password = sha256_crypt.hash(form.password.data)

        cursor = mysql.connection.cursor()

        query = "SELECT * FROM persons WHERE ssn = %s"
        same_ssn = cursor.execute(query, (ssn,)) > 0

        query = "SELECT * FROM persons WHERE email = %s"
        same_email = cursor.execute(query, (email,)) > 0
        if same_ssn:
            flash(message="This SSN has been registered, if you think there was a mistake then contact 'Tzesh'",
                  category="danger")
            cursor.close()
            return redirect(url_for("index"))

        if same_email:
            flash(message="This email has been registered, if you think there was a mistake then contact 'Tzesh'",
                  category="danger")
            cursor.close()
            return redirect(url_for("index"))

        query = "INSERT INTO persons(ssn, email, password, first_name, last_name, gender, birth_date) VALUES(%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (ssn, email, password, first_name, last_name, gender, birth_date))
        mysql.connection.commit()

        cursor.close()
        flash(message="You have been successfully registered. You may login now.", category="success")
        return redirect(url_for("index"))
    else:
        return render_template("register.html", form=form)


# Member area page
@app.route('/member-area', methods=["GET", "POST"])
@login_required
def member_area():
    return render_template("welcome.html")


# Profile page
@app.route('/profile', methods=["GET", "POST"])
@login_required
def profile():
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM persons WHERE ssn = %s"
    cursor.execute(query, (session["ssn"],))
    person = cursor.fetchone()

    query = "SELECT * FROM addresses WHERE p_ssn = %s"
    is_address_exist = cursor.execute(query, (session["ssn"],))
    addresses = cursor.fetchall()

    query = "SELECT * FROM person_contact_numbers WHERE contact_ssn = %s"
    is_phone_exist = cursor.execute(query, (session["ssn"],))
    phones = cursor.fetchall()

    if is_address_exist and is_phone_exist and not session["is_patient"]:
        query = "INSERT INTO patients(patient_ssn) VALUES (%s)"
        cursor.execute(query, (session["ssn"],))
        mysql.connection.commit()
        session["is_patient"] = True
        cursor.close()
        flash("You have successfully activated your account. Now you can use Denpointment system.", category="success")
        return render_template("profile.html", person=person, addresses=addresses, phones=phones)

    cursor.close()
    return render_template("profile.html", person=person, addresses=addresses, phones=phones)


# Profile -> Change Password
@app.route('/change-password', methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm(request.form)
    if request.method == "POST" and form.validate():
        old_password = form.old_password.data
        password = form.password.data
        if old_password == password:
            flash(message="Your old password and new password cannot be the same.", category="danger")
            return render_template("change-password.html", form=form)
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM Persons WHERE ssn = %s"
        cursor.execute(query, (session["ssn"],))
        data = cursor.fetchone()
        real_password = data["password"]
        if sha256_crypt.verify(old_password, real_password):
            query = "UPDATE persons SET password = %s WHERE ssn = %s"
            hashed_password = sha256_crypt.hash(password)
            cursor.execute(query, (hashed_password, session["ssn"]))
            mysql.connection.commit()
            cursor.close()
            flash("Your password has been successfully changed", "success")
            return redirect(url_for("profile"))
        else:
            cursor.close()
            flash("Your password is wrong.", "danger")
            return redirect(url_for("profile"))
    return render_template("change-password.html", form=form)

# Profile -> Change Email
@app.route('/change-email', methods=["GET", "POST"])
@login_required
def change_email():
    form = ChangeEmailForm(request.form)
    if request.method == "POST" and form.validate():
        email = form.email.data
        password = form.password.data
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM Persons WHERE ssn = %s"
        cursor.execute(query, (session["ssn"],))
        data = cursor.fetchone()
        real_password = data["password"]
        if data["email"] == email:
            flash(message="Your old email and new email cannot be the same.", category="danger")
            return render_template("change-email.html", form=form)
        if sha256_crypt.verify(password, real_password):
            query = "UPDATE persons SET email = %s WHERE ssn = %s"
            cursor.execute(query, (email, session["ssn"]))
            mysql.connection.commit()
            session["email"] = email
            cursor.close()
            flash("Your email has been successfully changed", "success")
            return redirect(url_for("profile"))
        else:
            cursor.close()
            flash("Your password is wrong.", "danger")
            return redirect(url_for("profile"))
    return render_template("change-email.html", form=form)


# Profile -> Addresses -> Add
@app.route('/add-address', methods=["GET", "POST"])
@login_required
def add_address():
    form = AddressForm(request.form)
    if request.method == "POST" and form.validate():
        city = form.city.data
        street = form.street.data
        zip_code = form.zip_code.data

        cursor = mysql.connection.cursor()
        query = "SELECT * FROM addresses WHERE p_ssn = %s and city = %s and street = %s and zip_code = %s"
        is_registered = cursor.execute(query, (session["ssn"], city, street, zip_code)) > 0
        if is_registered:
            flash(message="This address has been already associated with your profile.", category="danger")
            return render_template("add-address.html", form=form)
        else:
            query = "INSERT INTO addresses(p_ssn, city, street, zip_code) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (session["ssn"], city, street, zip_code))
            mysql.connection.commit()
            flash(message="Address information has been registered successfully.", category="success")
            return redirect(url_for("profile"))
    return render_template("add-address.html", form=form)


# Profile -> Addresses -> Delete
@app.route('/delete-address/<string:address_id>')
@login_required
def delete_address(address_id):
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM addresses WHERE p_ssn = %s"
    result = cursor.execute(query, (session["ssn"],))
    if result > 1:
        query = "SELECT * FROM addresses WHERE p_ssn = %s and address_id = %s"
        result = cursor.execute(query, (session["ssn"], address_id))
        if result > 0:
            query = "DELETE FROM addresses WHERE address_id = %s"
            cursor.execute(query, (address_id,))
            mysql.connection.commit()
            flash(message="Address information has been deleted from your profile successfully.",
                  category="success")
            return redirect(url_for("profile"))
        else:
            flash(message="There's not such phone number stored in your profile.", category="danger")
            return redirect(url_for("profile"))
    if result == 1:
        flash(message="You have to provide at least one address information. Maybe you may edit the existing one.",
              category="danger")
        return redirect(url_for("profile"))
    else:
        flash(message="There's not such address information stored in your profile.", category="danger")
        return redirect(url_for("profile"))


# Profile -> Addresses -> Modify
@app.route('/modify-address/<string:address_id>', methods=["GET", "POST"])
@login_required
def modify_address(address_id):
    if request.method == "GET":
        form = AddressForm()
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM addresses WHERE p_ssn = %s and address_id = %s"
        result = cursor.execute(query, (session["ssn"], address_id))
        if result == 0:
            flash(message="There's not such address information stored in your profile.", category="danger")
            return redirect(url_for("profile"))
        else:
            data = cursor.fetchone()
            form.city.data = data["city"]
            form.street.data = data["street"]
            form.zip_code.data = data["zip_code"]
            return render_template("modify-address.html", form=form)
    else:
        form = AddressForm(request.form)
        if request.method == "POST" and form.validate():
            cursor = mysql.connection.cursor()
            city = form.city.data
            street = form.street.data
            zip_code = form.zip_code.data
            query = "SELECT * FROM addresses WHERE p_ssn = %s and city = %s and street = %s and zip_code = %s"
            if cursor.execute(query, (session["ssn"], city, street, zip_code)):
                cursor.close()
                flash(message="This address information has been already registered.", category="danger")
                return render_template("modify-address.html", form=form)
            else:
                query = "UPDATE addresses SET city = %s, street = %s, zip_code = %s WHERE p_ssn = %s and address_id = %s"
                cursor.execute(query, (city, street, zip_code, session["ssn"], address_id))
                mysql.connection.commit()
                cursor.close()
                flash(message="Address information has been modified successfully.", category="success")
                return redirect(url_for("profile"))
        else:
            flash(message="Please re-correct your address information.", category="danger")
            return render_template("modify-address.html", form=form)


# Profile -> Phones -> Add
@app.route('/add-phone', methods=["GET", "POST"])
@login_required
def add_phone():
    form = PhoneForm(request.form)
    if request.method == "POST" and form.validate():
        phone_number = form.contact_number.data
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM person_contact_numbers WHERE contact_number = %s"
        is_registered = cursor.execute(query, (phone_number,)) > 0
        if is_registered:
            cursor.close()
            flash(message="This phone number has been already registered.", category="danger")
            return render_template("add-phone.html", form=form)
        else:
            query = "INSERT INTO person_contact_numbers(contact_number, contact_ssn) VALUES (%s, %s)"
            cursor.execute(query, (phone_number, session["ssn"]))
            mysql.connection.commit()
            cursor.close()
            flash(message="Phone number has been registered successfully.", category="success")
            return redirect(url_for("profile"))
    return render_template("add-phone.html", form=form)


# Profile -> Phones -> Delete
@app.route('/delete-phone/<string:contact_number>')
@login_required
def delete_phone(contact_number):
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM person_contact_numbers WHERE contact_ssn = %s"
    result = cursor.execute(query, (session["ssn"],))
    if result > 1:
        query = "SELECT * FROM person_contact_numbers WHERE contact_ssn = %s and contact_number = %s"
        result = cursor.execute(query, (session["ssn"], contact_number))
        if result > 0:
            query = "DELETE FROM person_contact_numbers WHERE contact_number = %s"
            cursor.execute(query, (contact_number,))
            cursor.close()
            mysql.connection.commit()
            flash(message="Phone number information has been deleted from your profile successfully.",
                  category="success")
            return redirect(url_for("profile"))
        else:
            cursor.close()
            flash(message="There's not such phone number stored in your profile.", category="danger")
            return redirect(url_for("profile"))
    if result == 1:
        flash(message="You have to provide at least one phone number. Maybe you may edit the existing one.",
              category="danger")
        return redirect(url_for("profile"))
    else:
        flash(message="There's not such phone number stored in your profile.", category="danger")
        return redirect(url_for("profile"))


# Profile -> Phones -> Modify
@app.route('/modify-phone/<string:number>', methods=["GET", "POST"])
@login_required
def modify_phone(number):
    if request.method == "GET":
        form = PhoneForm()
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM person_contact_numbers WHERE contact_ssn = %s and contact_number = %s"
        result = cursor.execute(query, (session["ssn"], number))
        if result == 0:
            cursor.close()
            flash(message="There's not such phone number stored in your profile.", category="danger")
            return redirect(url_for("profile"))
        else:
            cursor.close()
            form.contact_number.data = number
            return render_template("modify-phone.html", form=form)
    else:
        form = PhoneForm(request.form)
        if request.method == "POST" and form.validate():
            cursor = mysql.connection.cursor()
            phone_number = form.contact_number.data
            query = "SELECT * FROM person_contact_numbers WHERE contact_number %s"
            cursor.close()
            if cursor.execute(query, (phone_number,)):
                flash(message="This phone number has been already registered.", category="danger")
                return render_template("modify-phone.html", form=form)
            else:
                query = "UPDATE person_contact_numbers SET contact_number = %s WHERE contact_number = %s"
                cursor.execute(query, (phone_number, number))
                mysql.connection.commit()
                flash(message="Phone number has been modified successfully.", category="success")
                return redirect(url_for("profile"))
        else:
            flash(message="Please re-correct your phone number.", category="danger")
            return render_template("modify-phone.html", form=form)


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == '__main__':
    app.run()
