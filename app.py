import os
import datetime
import smtplib
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from email.mime.text import MIMEText

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

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['To'] = email_to_address
    msg['From'] = email_from_address

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(email_username, email_password)
            server.sendmail(email_from_address, email_to_address, msg.as_string())
        print("Email sent to {}".format(email_to_address))
    except Exception as e:
        print("Error sending email: {}".format(e))

# API endpoint to add new reminders
@app.route('/reminder', methods=['POST'])
def add_reminder():
    data = request.get_json()
    try:
        title = data['title']
        description = data['description']
        date_time = datetime.datetime.strptime(data['date_time'], "%Y-%m-%dT%H:%M:%S.%fZ")
        type = data['type']
        frequency = data['frequency']

        new_reminder = Reminder(title, description, date_time, type, frequency)
        db.session.add(new_reminder)
        db.session.commit()

        return jsonify({'message': 'Reminder added successfully'}), 200
    except Exception as e:
        return jsonify({'message': 'Error adding reminder: {}'.format(e)}), 400

# API endpoint to get all reminders
@app.route('/reminders', methods=['GET'])
def get_reminders():
    reminders = Reminder.query.all()
    return jsonify([r.to_dict() for r in reminders]), 200

# API to test email sending
@app.route('/send/email/test', methods=['GET'])
def send_email_test():
    send_email("Test Email", "This is a test email.")
    return jsonify({'message': 'Email sent successfully'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=10000)
