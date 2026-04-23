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
    rate = request.form["rate"]

    if rate != "yes":
        return render_template("index.html", error="Sorry, we lost a member. We hope to see you again!")

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
        monthly=monthly
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
