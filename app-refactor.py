import datetime
import os
import threading
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import smtplib
from email.mime.text import MIMEText
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reminders.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'date_time': self.date_time.isoformat(),
            'type': self.type,
            'frequency': self.frequency
        }

# Function to send email
def send_email(subject, body):
    email_username = os.environ.get('EMAIL_USERNAME')
    email_password = os.environ.get('EMAIL_PASSWORD')
    email_to_address = os.environ.get('EMAIL_TO_ADDRESS')
    email_from_address = os.environ.get('EMAIL_FROM_ADDRESS')

    if not all([email_username, email_password, email_to_address, email_from_address]):
        print("Error: Missing email credentials in environment variables.")
        return

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['To'] = email_to_address
    msg['From'] = email_from_address

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(email_username, email_password)
            server.sendmail(email_from_address, email_to_address, msg.as_string())
        print(f"Email sent to {email_to_address}")
    except Exception as e:
        print(f"Error sending email: {e}")

# Function to check for today's reminders
def check_reminders():
    today = datetime.datetime.now().date()
    start_of_day = datetime.datetime.combine(today, datetime.time.min)
    end_of_day = datetime.datetime.combine(today, datetime.time.max)

    reminders = Reminder.query.filter(Reminder.date_time.between(start_of_day, end_of_day)).all()

    for reminder in reminders:
        subject = f"Reminder: {reminder.type} for {reminder.title}"
        body = f"Hey, don't forget!\nEvent Type: {reminder.type}\nTitle: {reminder.title}\nDescription: {reminder.description}"
        send_email(subject, body)

        # Adjust reminder date based on frequency
        match reminder.frequency:
            case "daily":
                reminder.date_time += datetime.timedelta(days=1)
            case "weekly":
                reminder.date_time += datetime.timedelta(weeks=1)
            case "monthly":
                reminder.date_time += relativedelta(months=1)
            case "yearly":
                reminder.date_time += relativedelta(years=1)
            case "once":
                db.session.delete(reminder)
    db.session.commit()

# Start APScheduler in a separate thread
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_reminders, trigger="interval", days=1)

def start_scheduler():
    scheduler.start()

threading.Thread(target=start_scheduler, daemon=True).start()

# API endpoint to add new reminders
@app.route('/reminder', methods=['POST'])
def add_reminder():
    data = request.json
    try:
        date_time = datetime.datetime.strptime(data['date_time'], "%Y-%m-%dT%H:%M:%S.%fZ")
        new_reminder = Reminder(
            title=data['title'],
            description=data['description'],
            date_time=date_time,
            type=data['type'],
            frequency=data['frequency']
        )
        db.session.add(new_reminder)
        db.session.commit()
        return jsonify({'message': 'Reminder added successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# API endpoint to get all reminders
@app.route('/reminders', methods=['GET'])
def get_reminders():
    reminders = Reminder.query.all()
    return jsonify([reminder.to_dict() for reminder in reminders]), 200

# API endpoint to send a test email
@app.route('/send/email/test', methods=['GET'])
def send_email_test():
    send_email("Test email", "This is a test email")
    return jsonify({'message': 'Test email sent successfully'}), 200

# Run the Flask app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
