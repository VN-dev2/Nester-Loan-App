import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://nester_loan_db_user:peAO61bW2DK2LFizOyJWBHgyb4MIAeCM@dpg-d7kq4o5ckfvc73f4i3vg-a.frankfurt-postgres.render.com/nester_loan_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'nester2026secretkey'
db = SQLAlchemy(app)

# Admin credentials
ADMIN_USERNAME = "nester"
ADMIN_PASSWORD = "loan2026"

# Database Model


class Applicant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    occupation = db.Column(db.String(100))
    income = db.Column(db.Float)
    loan = db.Column(db.Float)
    total = db.Column(db.Float)
    monthly = db.Column(db.Float)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    house_number = db.Column(db.String(50))
    marital_status = db.Column(db.String(20))
    agreed = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='Pending')
    date_applied = db.Column(db.DateTime, default=datetime.utcnow)


# Create database
with app.app_context():
    db.create_all()

# Login required decorator


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/calculate", methods=["POST"])
def calculate():
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    year_of_birth = int(request.form["year_of_birth"])
    age = 2026 - year_of_birth

    if age < 18:
        return render_template("index.html", error=f"Sorry {first_name}, you are {age} years old and ineligible.")

    occupation = request.form["occupation"]
    income = float(request.form["income"])
    loan = float(request.form["loan"])
    phone = request.form["phone"]
    address = request.form["address"]
    house_number = request.form["house_number"]
    marital_status = request.form["marital_status"]
    agreed = request.form.get("agreed") == "on"
    rate = request.form["rate"]

    if rate != "yes":
        return render_template("index.html", error="Sorry, we lost a member. We hope to see you again!")

    if not agreed:
        return render_template("index.html", error="You must agree to the repayment oath to proceed.")

    existing = Applicant.query.filter_by(phone=phone).first()
    if existing:
        return render_template("index.html", error=f"Sorry {first_name}, an application with this phone number already exists.")

    money = loan * (21/100)
    total = money + loan
    monthly = total / 12

    applicant = Applicant(
        first_name=first_name,
        last_name=last_name,
        age=age,
        occupation=occupation,
        income=income,
        loan=loan,
        total=total,
        monthly=monthly,
        phone=phone,
        address=address,
        house_number=house_number,
        marital_status=marital_status,
        agreed=agreed
    )
    db.session.add(applicant)
    db.session.commit()

    schedule = []
    for week in range(1, 13):
        schedule.append(f"Week {week} - Pay GHS {monthly:.2f}")

    pickup_date = datetime.now() + timedelta(days=7)
    pickup_date_str = pickup_date.strftime("%A, %d %B %Y")

    return render_template("index.html",
                           first_name=first_name,
                           loan=loan,
                           total=f"{total:.2f}",
                           monthly=f"{monthly:.2f}",
                           schedule=schedule,
                           pickup_date=pickup_date_str
                           )


@app.route("/admin/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = "Invalid username or password"
    return render_template("login.html", error=error)


@app.route("/admin/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route("/admin")
@login_required
def admin():
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')

    query = Applicant.query

    if search:
        query = query.filter(
            (Applicant.first_name.ilike(f'%{search}%')) |
            (Applicant.last_name.ilike(f'%{search}%')) |
            (Applicant.phone.ilike(f'%{search}%'))
        )

    if status_filter:
        query = query.filter_by(status=status_filter)

    applicants = query.all()

    total_applicants = Applicant.query.count()
    total_approved = Applicant.query.filter_by(status='Approved').count()
    total_declined = Applicant.query.filter_by(status='Declined').count()
    total_pending = Applicant.query.filter_by(status='Pending').count()
    total_loans = db.session.query(db.func.sum(Applicant.loan)).filter_by(
        status='Approved').scalar() or 0
    total_return = db.session.query(db.func.sum(Applicant.total)).filter_by(
        status='Approved').scalar() or 0

    return render_template("admin.html",
                           applicants=applicants,
                           total_applicants=total_applicants,
                           total_approved=total_approved,
                           total_declined=total_declined,
                           total_pending=total_pending,
                           total_loans=total_loans,
                           total_return=total_return,
                           search=search,
                           status_filter=status_filter
                           )


@app.route("/admin/approve/<int:id>")
@login_required
def approve(id):
    applicant = Applicant.query.get(id)
    applicant.status = "Approved"
    db.session.commit()
    return redirect(url_for('admin'))


@app.route("/admin/decline/<int:id>")
@login_required
def decline(id):
    applicant = Applicant.query.get(id)
    applicant.status = "Declined"
    db.session.commit()
    return redirect(url_for('admin'))


@app.route("/admin/delete/<int:id>")
@login_required
def delete(id):
    applicant = Applicant.query.get(id)
    db.session.delete(applicant)
    db.session.commit()
    return redirect(url_for('admin'))


if __name__ == "__main__":
    app.run(debug=True)
