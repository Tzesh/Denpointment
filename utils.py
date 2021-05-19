# Denpointment System - Utils
# github.com/Tzesh/Denpointment

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
    query = "SELECT * FROM dentists WHERE dentist_ssn = %s"
    result_set = cursor.execute(query, (ssn,))
    cursor.close()
    return True if result_set else False


# Check if the user is a patient
def check_is_patient(ssn, mysql):
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM patients WHERE patient_ssn = %s"
    result_set = cursor.execute(query, (ssn,))
    cursor.close()
    return True if result_set else False
