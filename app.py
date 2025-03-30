import datetime
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import smtplib
from email.mime.text import MIMEText

# Define the Flask application
# Setting up SQLIte database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reminders.db'
db = SQLAlchemy(app)

# Define the Reminder database model
class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(120), nullable=False)
    date_time = db.Column(db.DateTime, nullable=False)
    type = db.Column(db.String(80), nullable=False)
    frequency = db.Column(db.String(80), nullable=False)

    def __init__(self, title, description, date_time, type, frequency):
        self.title = title
        self.description = description
        self.date_time = date_time
        self.type = type
        self.frequency = frequency

# Function to send email
def send_email(subject, body):
    # Get email credentials from environment variable
    email_username = os.environ.get('EMAIL_USERNAME')
    email_password = os.environ.get('EMAIL_PASSWORD')
    email_to_address = os.environ.get('EMAIL_TO_ADDRESS')
    email_from_address = os.environ.get('EMAIL_FROM_ADDRESS')


    # Create email message
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['To'] = email_to_address
    msg['From'] = email_from_address

    # Send email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(email_username, email_password)
            server.sendmail(email_from_address, email_to_address, msg.as_string())
        print("Email sent to {}".format(email_to_address))
    except Exception as e:
        print("Error sending email to {} : {}".format(email_to_address, e))

# Function to check for today's reminders
def check_reminders():
    today = datetime.datetime.now().date()

    reminders = Reminder.query.filter(db.func.date(Reminder.date_time) == today).all()
    for reminder in reminders:
        subject = f"Reminder: {reminder.type} for {reminder.title}"
        body = f"Hey, don't forget! Today is \nEvent Type: {reminder.type}:\nTitle: {reminder.title}\nDescription: {reminder.description}"
        send_email(subject, body)

        # Based on event frequency 
        match reminder.frequency:
            case "daily":
                reminder.date_time += datetime.timedelta(days=1)
            case "weekly":
                reminder.date_time += datetime.timedelta(weeks=1)
            case "monthly":
                reminder.date_time += datetime.timedelta(months=1)
            case "yearly":
                reminder.date_time += datetime.timedelta(years=1)
            case "once":
                db.session.delete(reminder)
                db.session.commit()
            case _:
                pass

# Schedule daily job
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_reminders, trigger="interval", days=1)
scheduler.start()

# API endpoint to add new reminders
@app.route('/reminder', methods=['POST'])
def add_reminder():
    title = request.json['title']
    description = request.json['description']
    date_time = datetime.datetime.strptime(request.json['date_time'], "%Y-%m-%dT%H:%M:%S.%fZ")
    type = request.json['type']
    frequency = request.json['frequency']

    new_reminder = Reminder(title, description, date_time, type, frequency)
    db.session.add(new_reminder)
    db.session.commit()

    return jsonify({'message': 'Reminder added successfully'}), 200

# API endpoint to get all reminders
@app.route('/reminders', methods=['GET'])
def get_reminders():
    reminders = Reminder.query.all()
    return jsonify([reminder.to_dict() for reminder in reminders]), 200

@app.route('/send/email/test', methods=['GET'])
def send_email_test():
    subject = "Test email"
    body = "This is a test email"
    send_email(subject, body)
    return jsonify({'message': 'Email sent successfully'}), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

