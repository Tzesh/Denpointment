from flask import redirect, url_for, flash, session
from functools import wraps


# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("You are not authorized!", "danger")
            return redirect(url_for("index"))

    return decorated_function

# Check if the user is a dentist
def check_is_dentist(ssn, mysql):
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM Dentists WHERE dentist_ssn = %s"
    result_set = cursor.execute(query, (ssn,))
    cursor.close()
    return True if result_set > 0 else False


# Check if the user is a patient
def check_is_patient(ssn, mysql):
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM Patients WHERE patient_ssn = %s"
    result_set = cursor.execute(query, (ssn,))
    cursor.close()
    return True if result_set > 0 else False


# Check if the user is patient in session
def check_patient(session):
    if "is_patient" not in session:
        flash(message="You are not authorized, you are not a patient!", category="danger")
        return redirect(url_for("member_area"))


# Check if the user is dentist in session
def check_dentist(session):
    if "is_dentist" not in session:
        flash(message="You are not authorized, you are not a dentist!", category="danger")
        return redirect(url_for("member_area"))
