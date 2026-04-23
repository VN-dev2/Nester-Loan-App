from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nester_loan.db'
db = SQLAlchemy(app)

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
    date_applied = db.Column(db.DateTime, default=datetime.utcnow)


# Create database
with app.app_context():
    db.create_all()


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

    money = loan * (21/100)
    total = money + loan
    monthly = total / 12

    # Save to database
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

    return render_template("index.html",
                           first_name=first_name,
                           loan=loan,
                           total=f"{total:.2f}",
                           monthly=f"{monthly:.2f}",
                           schedule=schedule
                           )


@app.route("/admin")
def admin():
    applicants = Applicant.query.all()
    return render_template("admin.html", applicants=applicants)


if __name__ == "__main__":
    app.run(debug=True)
