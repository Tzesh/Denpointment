from flask import Flask, render_template, flash, redirect, url_for, session, request
from flask_mysqldb import MySQL
from passlib.handlers.sha2_crypt import sha256_crypt
from forms import LoginForm, RegistrationForm, PhoneForm, AddressForm, ChangePasswordForm, ChangeEmailForm, \
    ChronicDiseaseForm, BookAppointmentForm, AddHolidayForm, TreatmentForm, MedicineForm, SearchTreatmentForm
from utils import login_required, check_is_patient, check_is_dentist
from datetime import datetime

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

    query = "SELECT * FROM chronic_diseases WHERE chronic_ssn = %s"
    cursor.execute(query, (session["ssn"],))
    chronic_diseases = cursor.fetchall()

    if is_address_exist and is_phone_exist and not session["is_patient"]:
        query = "INSERT INTO patients(patient_ssn) VALUES (%s)"
        cursor.execute(query, (session["ssn"],))
        mysql.connection.commit()
        session["is_patient"] = True
        cursor.close()
        flash("You have successfully activated your account. Now you can use Denpointment system.", category="success")
        return render_template("profile.html", person=person, addresses=addresses, phones=phones)

    cursor.close()
    return render_template("profile.html", person=person, addresses=addresses, phones=phones,
                           chronic_diseases=chronic_diseases)


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


# Profile -> Addresses -> Delete
@app.route('/delete-chronic-disease/<string:chronic_disease>')
@login_required
def delete_chronic_disease(chronic_disease):
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM chronic_diseases WHERE chronic_ssn = %s and chronic_disease = %s"
    result = cursor.execute(query, (session["ssn"], chronic_disease))
    if result:
        query = "DELETE FROM chronic_diseases WHERE chronic_ssn = %s and chronic_disease = %s"
        cursor.execute(query, (session["ssn"], chronic_disease))
        mysql.connection.commit()
        flash(message="Chronic disease information has been deleted from your profile successfully.",
              category="success")
        return redirect(url_for("profile"))
    else:
        flash(message="There's not such chronic disease stored in your profile.", category="danger")
        return redirect(url_for("profile"))


# Profile -> Addresses -> Add
@app.route('/add-chronic-disease', methods=["GET", "POST"])
@login_required
def add_chronic_disease():
    form = ChronicDiseaseForm(request.form)
    if request.method == "POST" and form.validate():
        chronic_disease = form.chronic_disease.data
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM chronic_diseases WHERE chronic_ssn = %s"
        is_registered = cursor.execute(query, (session["ssn"],)) > 0
        if is_registered:
            flash(message="This chronic disease has been already associated with your profile.", category="danger")
            return render_template("add-chronic-disease.html", form=form)
        else:
            query = "INSERT INTO chronic_diseases(chronic_disease, chronic_ssn) VALUES (%s, %s)"
            cursor.execute(query, (chronic_disease, session["ssn"]))
            mysql.connection.commit()
            flash(message="Chronic disease information has been registered successfully.", category="success")
            return redirect(url_for("profile"))
    return render_template("add-chronic-disease.html", form=form)


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


# Appointments -> My Appointments
@app.route('/appointments')
@login_required
def my_appointments():
    if not session["is_patient"]:
        flash("You are not authorized!", "danger")
        return redirect(url_for("index"))
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM patients WHERE patient_ssn = %s"
    cursor.execute(query, (session["ssn"],))
    person = cursor.fetchone()
    patient_id = person["patient_id"]

    month = datetime.today().month
    day = datetime.today().day
    year = datetime.today().year

    query = """ SELECT * FROM appointments
                LEFT OUTER JOIN dentists
                ON appointments.d_id = dentists.dentist_id
                LEFT OUTER JOIN persons
                ON persons.ssn = dentists.dentist_ssn
                LEFT OUTER JOIN treatments
                ON appointments.appointment_id = treatments.a_id
                LEFT OUTER JOIN medicines
                ON medicines.t_id = treatments.treatment_id
                WHERE (p_id = %s AND `month` = %s AND `day` <= %s AND `year` = %s)
                OR (p_id = %s AND `month` < %s AND `year` = %s)
                OR (p_id = %s AND `year` < %s)"""
    cursor.execute(query, (patient_id, month, day, year, patient_id, month, year, patient_id, year))
    past_appointments = cursor.fetchall()

    query = """ SELECT * FROM appointments
                LEFT OUTER JOIN dentists
                ON appointments.d_id = dentists.dentist_id
                LEFT OUTER JOIN persons
                ON persons.ssn = dentists.dentist_ssn
                WHERE (p_id = %s AND `month` = %s AND `day` > %s AND `year` = %s)
                OR (p_id = %s AND `month` > %s AND `year` = %s)
                OR (p_id = %s AND `year` > %s)"""
    cursor.execute(query, (patient_id, month, day, year, patient_id, month, year, patient_id, year))
    upcoming_appointments = cursor.fetchall()

    cursor.close()
    return render_template("appointments.html", past_appointments=past_appointments,
                           upcoming_appointments=upcoming_appointments)


# Appointments -> Book An Appointment
@app.route('/book-an-appointment', methods=["GET", "POST"])
@login_required
def book_an_appointment():
    if not session["is_patient"]:
        flash("You are not authorized!", "danger")
        return redirect(url_for("index"))
    if request.method == "GET":
        form = BookAppointmentForm(request.form)
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM patients WHERE patient_ssn = %s"
        cursor.execute(query, (session["ssn"],))
        person = cursor.fetchone()
        patient_id = person["patient_id"]

        month = datetime.today().month
        day = datetime.today().day
        year = datetime.today().year

        query = """ SELECT * FROM appointments
                        LEFT OUTER JOIN dentists
                        ON appointments.d_id = dentists.dentist_id
                        LEFT OUTER JOIN persons
                        ON persons.ssn = dentists.dentist_ssn
                        WHERE (p_id = %s AND `month` = %s AND `day` > %s AND `year` = %s)
                        OR (p_id = %s AND `month` > %s AND `year` = %s)
                        OR (p_id = %s AND `year` > %s)"""
        cursor.execute(query, (patient_id, month, day, year, patient_id, month, year, patient_id, year))
        upcoming_appointments = cursor.fetchall()

        if upcoming_appointments:
            flash(message="You have an upcoming appointment, you can get another appointment after that one.",
                  category="danger")
            cursor.close()
            return redirect(url_for("book_an_appointment"))

        query = """
        SELECT dentists.dentist_id, dentists.room_number, persons.first_name, persons.last_name
        FROM dentists
        LEFT OUTER JOIN persons
        ON persons.ssn = dentists.dentist_ssn
        """
        cursor.execute(query)
        dentists = cursor.fetchall()

        form.dentist.choices = [(dentist["dentist_id"], dentist["first_name"] + " " + dentist["last_name"]) for dentist
                                in
                                dentists]
        form.hour.choices = [(8, 8), (9, 9), (10, 10), (11, 11), (12, 12), (15, 15), (16, 16)]

        return render_template("book-an-appointment.html", form=form)
    else:
        form = BookAppointmentForm(request.form)
        if request.method == "POST":
            cursor = mysql.connection.cursor()
            dentist_id = form.dentist.data
            date = form.date.data
            today = datetime.today()
            if today.year != date.year or today.month != date.month or today.day > date.day:
                flash(message="You only can get appointment for this month.", category="danger")
                return redirect(url_for("book_an_appointment"))
            day = str(date.day).zfill(2)
            month = str(date.month).zfill(2)
            year = date.year
            hour = form.hour.data

            query = """
                    SELECT dentists.dentist_id, dentists.room_number, persons.first_name, persons.last_name
                    FROM dentists
                    LEFT OUTER JOIN persons
                    ON persons.ssn = dentists.dentist_ssn
                    WHERE dentists.dentist_id = %s
                    """
            cursor.execute(query, (dentist_id,))
            dentist = cursor.fetchone()
            dentist_name = dentist["first_name"] + " " + dentist["last_name"]

            query = "SELECT * FROM holiday_dates WHERE resting_id = %s and rest_date = %s"
            result = cursor.execute(query, (dentist_id, date))
            if result:
                flash(
                    message=dentist_name + " is going to be on vacation on that date, please select another date to book an appointment",
                    category="warning")
                return redirect(url_for("my_appointments"))
            query = "SELECT * FROM appointments WHERE d_id = %s and `year` = %s and `month` = %s and `day` = %s and `hour` = %s"
            result = cursor.execute(query, (dentist_name, year, month, day, hour))
            if result:
                flash(message=dentist_name + " has already has an appointment on " + date + " " + hour,
                      category="danger")
                return render_template("book-an-appointment.html", form=form)
            query = "SELECT * FROM dentists WHERE dentist_id = %s"
            cursor.execute(query, (dentist_id,))
            dentist = cursor.fetchone()
            room = dentist["room_number"]
            query = "SELECT * FROM patients WHERE patient_ssn = %s"
            cursor.execute(query, (session["ssn"],))
            patient = cursor.fetchone()
            patient_id = patient["patient_id"]
            query = "INSERT INTO appointments(d_id, p_id, room, `hour`, `month`, `day`, `year`) VALUES(%s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (dentist_id, patient_id, room, hour, month, day, year))
            mysql.connection.commit()
            cursor.close()
            flash(message="Your appointment has been successfully booked", category="success")
            return redirect(url_for("my_appointments"))
        else:
            flash(message="Please fulfill the form", category="danger")
            return render_template("book-an-appointment.html", form=form)


# Holidays
@app.route('/holidays', methods=["GET", "POST"])
@login_required
def holidays():
    if not session["is_dentist"]:
        flash("You are not authorized!", "danger")
        return redirect(url_for("index"))
    cursor = mysql.connection.cursor()
    date = datetime.today()
    day = str(date.day).zfill(2)
    month = str(date.month).zfill(2)
    year = str(date.year)
    query = """SELECT *
               FROM dentists
               LEFT OUTER JOIN holiday_dates
               ON holiday_dates.resting_id = dentists.dentist_id and rest_date < %s
               WHERE dentist_ssn = %s"""
    cursor.execute(query, (date, session["ssn"]))
    past_holidays = cursor.fetchall()
    query = """SELECT *
               FROM dentists
               LEFT OUTER JOIN holiday_dates
               ON holiday_dates.resting_id = dentists.dentist_id and rest_date > %s
               WHERE dentist_ssn = %s"""
    cursor.execute(query, (date, session["ssn"]))
    upcoming_holidays = cursor.fetchall()
    cursor.close()
    return render_template("holidays.html", past_holidays=past_holidays, upcoming_holidays=upcoming_holidays)


# Holidays -> Add Holiday
@app.route('/add-holiday', methods=["GET", "POST"])
@login_required
def add_holiday():
    if not session["is_dentist"]:
        flash("You are not authorized!", "danger")
        return redirect(url_for("index"))
    form = AddHolidayForm(request.form)
    if request.method == "POST" and form.validate():
        rest_date = form.date.data
        reason = form.reason.data
        if datetime.today().year != rest_date.year or datetime.today().month + 1 != rest_date.month:
            flash(message="Holiday date must be in the next month", category="danger")
            return redirect(url_for("holidays"))
        cursor = mysql.connection.cursor()
        query = """SELECT *
               FROM dentists
               LEFT OUTER JOIN holiday_dates
               ON holiday_dates.resting_id = dentists.dentist_id and rest_date = %s
               WHERE dentist_ssn = %s"""
        holiday_date = cursor.execute(query, (session["ssn"], rest_date))
        if holiday_date:
            cursor.close()
            flash(message="This holiday is already been registered.", category="danger")
            return redirect(url_for("holidays"))
        query = """SELECT *
                       FROM dentists
                       LEFT OUTER JOIN holiday_dates
                       ON holiday_dates.resting_id = dentists.dentist_id and rest_date < %s-%s-%s
                       WHERE dentist_ssn = %s"""
        date = datetime.today()
        day = str(date.day).zfill(2)
        month = str(date.month).zfill(2)
        year = str(date.year)
        upcoming_holidays = cursor.execute(query, (year, month, day, session["ssn"]))
        if upcoming_holidays >= 3:
            cursor.close()
            flash(message="You can only rest at most 3 days in a month.", category="warning")
            return redirect(url_for("holidays"))
        else:
            query = "SELECT * FROM dentists WHERE dentist_ssn = %s"
            cursor.execute(query, (session["ssn"],))
            dentist = cursor.fetchone()
            query = "INSERT INTO holiday_dates(resting_id, reason, rest_date) VALUES (%s, %s, %s)"
            cursor.execute(query, (dentist["dentist_id"], reason, rest_date))
            mysql.connection.commit()
            cursor.close()
            flash(message="Holiday date has been added successfully.", category="success")
            return redirect(url_for("holidays"))
    return render_template("add-holiday.html", form=form)


# Holidays -> Delete Holiday
@app.route('/delete-holiday/<string:holiday_id>')
@login_required
def delete_holiday(holiday_id):
    if not session["is_dentist"]:
        flash("You are not authorized!", "danger")
        return redirect(url_for("index"))
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM dentists WHERE dentist_ssn = %s"
    cursor.execute(query, (session["ssn"],))
    dentist = cursor.fetchone()
    query = "SELECT * FROM holiday_dates WHERE holiday_id = %s and resting_id = %s"
    result = cursor.execute(query, (holiday_id, dentist["dentist_id"]))
    if result:
        holiday = cursor.fetchone()
        if datetime.today().month == holiday["rest_date"].month:
            flash(message="You cannot delete this holiday since it's in this month.", category="danger")
            return redirect(url_for("holidays"))
        query = "DELETE FROM holiday_dates WHERE holiday_id = %s and resting_id = %s"
        cursor.execute(query, (holiday_id, dentist["dentist_id"]))
        mysql.connection.commit()
        cursor.close()
        flash(message="Holiday information has been deleted successfully.", category="success")
        return redirect(url_for("holidays"))
    else:
        cursor.close()
        flash(message="There's not such holiday information stored in your profile.", category="danger")
        return redirect(url_for("holidays"))


# Treatments -> Upcoming Appointments
@app.route('/upcoming-appointments')
@login_required
def upcoming_appointments():
    if not session["is_dentist"]:
        flash("You are not authorized!", "danger")
        return redirect(url_for("index"))
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM dentists WHERE dentist_ssn = %s"
    cursor.execute(query, (session["ssn"],))
    dentist = cursor.fetchone()
    dentist_id = dentist["dentist_id"]
    query = """ SELECT * 
                FROM appointments
                LEFT OUTER JOIN patients
                ON patients.patient_id = appointments.p_id
                LEFT OUTER JOIN persons
                ON persons.ssn = patients.patient_ssn
                WHERE (d_id = %s AND `month` = %s AND `day` > %s AND `year` = %s)
                OR (d_id = %s AND `month` > %s AND `year` = %s)
                OR (d_id = %s AND `year` > %s)"""
    month = datetime.today().month
    day = datetime.today().day
    year = datetime.today().year
    cursor.execute(query, (dentist_id, month, day, year, dentist_id, month, year, dentist_id, year))
    upcoming_appointments = cursor.fetchall()
    return render_template("upcoming-appointments.html", upcoming_appointments=upcoming_appointments)


# Treatments -> Past Treatments
@app.route('/past-treatments')
@login_required
def past_treatments():
    if not session["is_dentist"]:
        flash("You are not authorized!", "danger")
        return redirect(url_for("index"))
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM dentists WHERE dentist_ssn = %s"
    cursor.execute(query, (session["ssn"],))
    dentist = cursor.fetchone()
    dentist_id = dentist["dentist_id"]
    query = """ SELECT * 
                FROM appointments
                LEFT OUTER JOIN patients
                ON patients.patient_id = appointments.p_id
                LEFT OUTER JOIN persons
                ON persons.ssn = patients.patient_ssn
                LEFT OUTER JOIN treatments
                ON treatments.a_id = appointments.appointment_id
                LEFT OUTER JOIN medicines
                ON medicines.t_id = treatments.treatment_id
                WHERE (d_id = %s AND `month` = %s AND `day` < %s AND `year` = %s)
                OR (d_id = %s AND `month` < %s AND `year` = %s)
                OR (d_id = %s AND `year` < %s)"""
    month = datetime.today().month
    day = datetime.today().day
    year = datetime.today().year
    cursor.execute(query, (dentist_id, month, day, year, dentist_id, month, year, dentist_id, year))
    past_treatments = cursor.fetchall()
    return render_template("past-treatments.html", past_treatments=past_treatments)


# Treatments -> Today's Appointments
@app.route('/todays-appointments')
@login_required
def todays_appointments():
    if not session["is_dentist"]:
        flash("You are not authorized!", "danger")
        return redirect(url_for("index"))
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM dentists WHERE dentist_ssn = %s"
    cursor.execute(query, (session["ssn"],))
    dentist = cursor.fetchone()
    dentist_id = dentist["dentist_id"]
    query = """     SELECT * 
                    FROM appointments
                    LEFT OUTER JOIN patients
                    ON patients.patient_id = appointments.p_id
                    LEFT OUTER JOIN persons
                    ON persons.ssn = patients.patient_ssn
                    LEFT OUTER JOIN treatments
                    ON treatments.a_id = appointments.appointment_id
                    LEFT OUTER JOIN medicines
                    ON medicines.t_id = treatments.treatment_id
                    WHERE (d_id = %s AND `month` = %s AND `day` = %s AND `year` = %s)"""
    month = datetime.today().month
    day = datetime.today().day
    year = datetime.today().year
    cursor.execute(query, (dentist_id, month, day, year))
    appointments_of_today = cursor.fetchall()
    return render_template("todays-appointments.html", appointments=appointments_of_today)


# Treatments -> Today's Appointments -> Add Treatment
@app.route('/add-treatment/<string:appointment_id>', methods=["GET", "POST"])
@login_required
def add_treatment(appointment_id):
    if request.method == "GET":
        if not session["is_dentist"]:
            flash("You are not authorized!", "danger")
            return redirect(url_for("index"))

        cursor = mysql.connection.cursor()
        query = "SELECT * FROM treatments WHERE a_id = %s"
        result = cursor.execute(query, (appointment_id,))
        if result:
            cursor.close()
            flash(message="Treatment has already exists.", category="danger")
            return redirect(url_for("todays_appointments"))
        query = "SELECT * FROM dentists WHERE dentist_ssn = %s"
        cursor.execute(query, (session["ssn"],))
        dentist = cursor.fetchone()
        dentist_id = dentist["dentist_id"]
        query = "SELECT * FROM appointments WHERE d_id = %s and `month` = %s and `day` = %s and `year` = %s and appointment_id = %s"
        month = datetime.today().month
        day = datetime.today().day
        year = datetime.today().year
        result = cursor.execute(query, (dentist_id, month, day, year, appointment_id))
        if not result:
            cursor.close()
            flash(message="There is not such appointment in today.", category="danger")
            return redirect(url_for("todays_appointments"))
        form = TreatmentForm()
        cursor.close()
        return render_template("add-treatment.html", form=form)
    else:
        form = TreatmentForm(request.form)
        if request.method == "POST" and form.validate():
            cursor = mysql.connection.cursor()
            query = "SELECT * FROM dentists WHERE dentist_ssn = %s"
            cursor.execute(query, (session["ssn"],))
            dentist = cursor.fetchone()
            dentist_id = dentist["dentist_id"]
            action = form.action.data
            complaint = form.complaint.data
            charge = form.charge.data
            description = form.description.data
            query = "INSERT INTO treatments(description, charge, `action`, complaint, a_id, treator_id) VALUES(%s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (description, charge, action, complaint, appointment_id, dentist_id))
            mysql.connection.commit()
            cursor.close()
            flash(message="Treatment has been added successfully.", category="success")
            return redirect(url_for("todays_appointments"))
    return render_template("add-treatment.html", form=form)


# Treatments -> Today's Appointments -> Modify Treatment
@app.route('/modify-treatment/<string:treatment_id>', methods=["GET", "POST"])
@login_required
def modify_treatment(treatment_id):
    if not session["is_dentist"]:
        flash("You are not authorized!", "danger")
        return redirect(url_for("index"))

    if request.method == "GET":
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM dentists WHERE dentist_ssn = %s"
        cursor.execute(query, (session["ssn"],))
        dentist = cursor.fetchone()
        dentist_id = dentist["dentist_id"]
        query = "SELECT * FROM treatments WHERE treatment_id = %s and treator_id = %s"
        result = cursor.execute(query, (treatment_id, dentist_id))
        if not result:
            cursor.close()
            flash(message="Treatment don't exist.", category="danger")
            return redirect(url_for("todays_appointments"))
        treatment = cursor.fetchone()
        form = TreatmentForm()
        form.action.data = treatment["action"]
        form.charge.data = treatment["charge"]
        form.complaint.data = treatment["complaint"]
        form.description.data = treatment["description"]
        cursor.close()
        return render_template("modify-treatment.html", form=form)
    else:
        form = TreatmentForm(request.form)
        if request.method == "POST" and form.validate():
            cursor = mysql.connection.cursor()
            query = "SELECT * FROM dentists WHERE dentist_ssn = %s"
            cursor.execute(query, (session["ssn"],))
            dentist = cursor.fetchone()
            dentist_id = dentist["dentist_id"]
            action = form.action.data
            complaint = form.complaint.data
            charge = form.charge.data
            description = form.description.data
            query = "UPDATE treatments SET description = %s, charge = %s, `action` = %s, complaint = %s WHERE treatment_id = %s and dentist_id = %s"
            cursor.execute(query, (description, charge, action, complaint, treatment_id, dentist_id))
            mysql.connection.commit()
            cursor.close()
            flash(message="Treatment has been modified successfully.", category="success")
            return redirect(url_for("todays_appointments"))
    return render_template("modify-treatment.html", form=form)


# Patient Profile
@app.route('/patient-profile-<string:patient_id>')
@login_required
def patient_profile(patient_id):
    if not session["is_dentist"]:
        flash("You are not authorized!", "danger")
        return redirect(url_for("index"))

    cursor = mysql.connection.cursor()
    query = """SELECT * FROM patients
                JOIN persons
                ON patients.patient_ssn = persons.ssn
                WHERE patient_id = %s"""
    result = cursor.execute(query, (patient_id,))
    if not result:
        cursor.close()
        flash(message="Patient does not exist.", category="danger")
        return url_for("profile")
    patient = cursor.fetchone()
    query = "SELECT * FROM addresses WHERE p_ssn = %s"
    is_address_exist = cursor.execute(query, (patient["ssn"],))
    addresses = cursor.fetchall()

    query = "SELECT * FROM person_contact_numbers WHERE contact_ssn = %s"
    is_phone_exist = cursor.execute(query, (patient["ssn"],))
    phones = cursor.fetchall()

    query = "SELECT * FROM chronic_diseases WHERE chronic_ssn = %s"
    cursor.execute(query, (patient["ssn"],))
    chronic_diseases = cursor.fetchall()
    cursor.close()
    return render_template("patient-profile.html", patient=patient, addresses=addresses, phones=phones,
                           chronic_diseases=chronic_diseases)


# Medicines
@app.route('/treatment-medicines-<string:treatment_id>')
@login_required
def medicines(treatment_id):
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM treatments WHERE treatment_id = %s"
    result = cursor.execute(query, (treatment_id,))
    if not result:
        flash(message="There's not such a treatment.", category="danger")
        cursor.close()
        return redirect(url_for("profile"))
    treatment = cursor.fetchone()
    appointment_id = treatment["a_id"]
    query = "SELECT * FROM appointments WHERE appointment_id = %s"
    cursor.execute(query, (appointment_id,))
    appointment = cursor.fetchone()
    is_dentist = False
    if session["is_dentist"]:
        query = "SELECT * FROM dentists WHERE dentist_ssn = %s"
        cursor.execute(query, (session["ssn"],))
        dentist = cursor.fetchone()
        if not appointment["d_id"] == dentist["dentist_id"]:
            flash(message="There's not such a treatment.", category="danger")
            cursor.close()
            return redirect(url_for("profile"))
        is_dentist = True
    if session["is_patient"] and not is_dentist:
        query = "SELECT * FROM patients WHERE patient_ssn = %s"
        cursor.execute(query, (session["ssn"],))
        patient = cursor.fetchone()
        patient_id = patient["patient_id"]
        if appointment["p_id"] != patient_id:
            flash(message="There's not such a treatment.", category="danger")
            cursor.close()
            return url_for("profile")
    query = "SELECT * FROM medicines WHERE t_id = %s"
    cursor.execute(query, (treatment_id,))
    medicine_names = cursor.fetchall()
    return render_template("medicines.html", medicine_names=medicine_names, treatment_id=treatment_id)


# Add Medicine
@app.route('/add-medicine-<string:treatment_id>', methods=["GET", "POST"])
@login_required
def add_medicine(treatment_id):
    if not session["is_dentist"]:
        flash("You are not authorized!", "danger")
        return redirect(url_for("index"))
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM treatments WHERE treatment_id = %s"
        result = cursor.execute(query, (treatment_id,))
        if not result:
            flash(message="There's not such a treatment.", category="danger")
            cursor.close()
            return redirect(url_for("todays_appointments"))
        treatment = cursor.fetchone()
        appointment_id = treatment["a_id"]
        query = "SELECT * FROM appointments WHERE appointment_id = %s"
        cursor.execute(query, (appointment_id,))
        appointment = cursor.fetchone()
        query = "SELECT * FROM dentists WHERE dentist_ssn = %s"
        cursor.execute(query, (session["ssn"],))
        dentist = cursor.fetchone()
        if not appointment["d_id"] == dentist["dentist_id"]:
            flash(message="There's not such a treatment.", category="danger")
            cursor.close()
            return redirect(url_for("todays_appointments"))
        form = MedicineForm()
        return render_template("add-medicine.html", form=form)
    else:
        form = MedicineForm(request.form)
        if request.method == "POST" and form.validate():
            cursor = mysql.connection.cursor()
            medicine_name = form.medicine_name.data
            query = "INSERT INTO medicines(t_id, medicine_name) VALUES(%s, %s)"
            cursor.execute(query, (treatment_id, medicine_name))
            mysql.connection.commit()
            flash(message="Medicine has been added successfully.", category="success")
            return redirect(url_for("todays_appointments"))
        else:
            form = MedicineForm()
            flash(message="Please re-check your medicine name.", category="danger")
            return render_template("add-medicine.html", form=form)


# Delete Medicine
@app.route('/delete-medicine-<string:treatment_id>-<string:medicine_id>')
@login_required
def delete_medicine(treatment_id, medicine_id):
    if not session["is_dentist"]:
        flash("You are not authorized!", "danger")
        return redirect(url_for("index"))
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM treatments WHERE treatment_id = %s"
    result = cursor.execute(query, (treatment_id,))
    if not result:
        flash(message="There's not such a treatment.", category="danger")
        cursor.close()
        return redirect(url_for("todays_appointments"))
    treatment = cursor.fetchone()
    appointment_id = treatment["a_id"]
    query = "SELECT * FROM appointments WHERE appointment_id = %s"
    cursor.execute(query, (appointment_id,))
    appointment = cursor.fetchone()
    query = "SELECT * FROM dentists WHERE dentist_ssn = %s"
    cursor.execute(query, (session["ssn"],))
    dentist = cursor.fetchone()
    if not appointment["d_id"] == dentist["dentist_id"]:
        flash(message="There's not such a treatment.", category="danger")
        cursor.close()
        return redirect(url_for("todays_appointments"))
    query = "SELECT * FROM medicines WHERE medicine_id = %s and t_id = %s"
    result = cursor.execute(query, (medicine_id, treatment_id))
    if not result:
        flash(message="There is not such that medicine exists.", category="danger")
        cursor.close()
        return redirect(url_for("todays_appointments"))
    today = datetime.today()
    if appointment["day"] != today.day and appointment["month"] != today.month and appointment["year"] != today.year:
        flash(message="You cannot remove medicines after treatment day.", category="danger")
        return redirect(url_for("todays_appointments"))
    query = "DELETE FROM medicines WHERE medicine_id = %s and t_id = %s"
    cursor.execute(query, (medicine_id, treatment_id))
    mysql.connection.commit()
    flash(message="Medicine has been deleted successfully.", category="success")
    cursor.close()
    return redirect(url_for("todays_appointments"))


# Delete Medicine
@app.route('/search-past-treatments', methods=["GET", "POST"])
@login_required
def search_past_treatments():
    if not session["is_dentist"]:
        flash("You are not authorized!", "danger")
        return redirect(url_for("index"))

    if request.method == "GET":
        form = SearchTreatmentForm()
        return render_template("search-treatment.html", form=form)
    else:
        form = SearchTreatmentForm(request.form)
        if request.method == "POST" and form.validate():
            date = form.date.data
            day = date.day
            month = date.month
            year = date.year
            today = datetime.today()
            cursor = mysql.connection.cursor()
            query = "SELECT * FROM dentists WHERE dentist_ssn = %s"
            cursor.execute(query, (session["ssn"],))
            dentist = cursor.fetchone()
            dentist_id = dentist["dentist_id"]
            query = """ SELECT * 
                            FROM appointments
                            LEFT OUTER JOIN patients
                            ON patients.patient_id = appointments.p_id
                            LEFT OUTER JOIN persons
                            ON persons.ssn = patients.patient_ssn
                            LEFT OUTER JOIN treatments
                            ON treatments.a_id = appointments.appointment_id
                            LEFT OUTER JOIN medicines
                            ON medicines.t_id = treatments.treatment_id
                            WHERE (d_id = %s AND `month` = %s AND `day` = %s AND `year` = %s)"""
            cursor.execute(query, (dentist_id, month, day, year))
            past_treatments = cursor.fetchall()
            return render_template("past-treatments.html", past_treatments=past_treatments)
        else:
            form = TreatmentForm()
            return render_template("add-medicine.html", form=form)


# Dentist Statistics
@app.route('/dentist-statistics')
@login_required
def dentist_statistics():
    if not session["is_dentist"]:
        flash("You are not authorized!", "danger")
        return redirect(url_for("index"))

    cursor = mysql.connection.cursor()
    query = """ SELECT d_id, COUNT(*) AS magnitude 
                FROM appointments
                GROUP BY d_id 
                ORDER BY magnitude DESC
                LIMIT 1"""
    cursor.execute(query)
    appointments = cursor.fetchone()
    dentist_id = appointments["d_id"]
    query = """ SELECT * FROM dentists
                LEFT OUTER JOIN persons
                ON dentists.dentist_ssn = persons.ssn
                WHERE dentist_id = %s"""
    cursor.execute(query, (dentist_id,))
    most_appointment = cursor.fetchone()

    query = """ SELECT *, COUNT(d_id) AS magnitude 
                    FROM appointments
                    LEFT OUTER JOIN dentists
                    ON dentists.dentist_id = appointments.d_id
                    LEFT OUTER JOIN persons
                    ON persons.ssn = dentists.dentist_ssn
                    GROUP BY d_id
                    ORDER BY magnitude DESC
                    LIMIT 10"""
    cursor.execute(query)
    appointment_ranking = cursor.fetchall()

    query = """ SELECT appointments.d_id, COUNT(*) AS magnitude 
                    FROM treatments
                    LEFT OUTER JOIN appointments
                    ON treatments.a_id = appointments.appointment_id
                    GROUP BY appointments.d_id 
                    ORDER BY magnitude DESC
                    LIMIT 1"""
    cursor.execute(query)
    treatments = cursor.fetchone()
    dentist_id = treatments["d_id"]
    query = """ SELECT * FROM dentists
                    LEFT OUTER JOIN persons
                    ON dentists.dentist_ssn = persons.ssn
                    WHERE dentist_id = %s"""
    cursor.execute(query, (dentist_id,))
    most_treatment = cursor.fetchone()

    query = """ SELECT *, COUNT(appointments.d_id) AS magnitude 
                        FROM treatments
                        LEFT OUTER JOIN appointments
                        ON treatments.a_id = appointments.appointment_id
                        LEFT OUTER JOIN dentists
                        ON appointments.d_id = dentists.dentist_id
                        LEFT OUTER JOIN persons
                        ON persons.ssn = dentists.dentist_ssn
                        GROUP BY appointments.d_id 
                        ORDER BY magnitude DESC
                        LIMIT 10"""
    cursor.execute(query)
    treatment_ranking = cursor.fetchall()
    cursor.close()

    return render_template("dentist-statistics.html", most_appointment=most_appointment, most_treatment=most_treatment,
                           appointment_ranking=appointment_ranking, treatment_ranking=treatment_ranking)


# Patient Statistics
@app.route('/patient-statistics')
@login_required
def patient_statistics():
    if not session["is_dentist"]:
        flash("You are not authorized!", "danger")
        return redirect(url_for("index"))

    cursor = mysql.connection.cursor()
    query = """ SELECT *, COUNT(treatments.complaint) AS magnitude 
                FROM treatments
                LEFT OUTER JOIN appointments
                ON treatments.a_id = appointments.appointment_id
                LEFT OUTER JOIN patients
                ON appointments.p_id = patients.patient_id
                LEFT OUTER JOIN persons
                ON persons.ssn = patients.patient_ssn and persons.gender = %s
                GROUP BY treatments.complaint
                ORDER BY magnitude DESC
                LIMIT 1"""
    cursor.execute(query, ("female",))
    female_complaint = cursor.fetchone()
    cursor.execute(query, ("male",))
    male_complaint = cursor.fetchone()

    query = """ SELECT *, MAX(treatments.charge)
                FROM treatments"""
    cursor.execute(query)
    most_expensive_treatment = cursor.fetchone()

    query = """ SELECT dentist.first_name as dentist_first_name, dentist.last_name as dentist_last_name, patient.first_name as patient_first_name, patient.last_name as patient_last_name, appointments.day, appointments.month, appointments.hour, appointments.year
                FROM appointments
                LEFT OUTER JOIN patients
                ON appointments.p_id = patients.patient_id
                LEFT OUTER JOIN persons as patient
                ON patient.ssn = patients.patient_ssn
                LEFT OUTER JOIN dentists
                ON dentists.dentist_id = appointments.d_id
                LEFT OUTER JOIN persons as dentist
                ON dentists.dentist_ssn = dentist.ssn
                WHERE appointment_id = %s
                """
    cursor.execute(query, (most_expensive_treatment["a_id"],))
    most_expensive_treatment_details = cursor.fetchone()

    query = """ SELECT AVG(treatments.charge) AS magnitude 
                    FROM treatments
                    WHERE `action` = 'tooth decay treatment'"""
    cursor.execute(query)
    tooth_decay_treatment_avg_cost = cursor.fetchone()

    query = """ SELECT *, COUNT(treatments.complaint) AS magnitude 
                    FROM treatments
                    WHERE a_id IN (
                    SELECT appointment_id
                    FROM appointments
                    WHERE `year` = %s and `month` = %s)
                    GROUP BY treatments.complaint
                    ORDER BY magnitude DESC
                    LIMIT 1"""
    cursor.execute(query, (datetime.today().year, datetime.today().month))
    most_common_complaint_last_month = cursor.fetchone()

    return render_template("patient-statistics.html", female_complaint=female_complaint, male_complaint=male_complaint,
                           most_expensive_treatment=most_expensive_treatment,
                           most_expensive_treatment_details=most_expensive_treatment_details,
                           tooth_decay_treatment_avg_cost=tooth_decay_treatment_avg_cost,
                           most_common_complaint_last_month=most_common_complaint_last_month)


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == '__main__':
    app.run()
