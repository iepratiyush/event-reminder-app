import os
import datetime
import smtplib
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

def check_and_send_reminders():
    """
    Check the reminders in the database and send emails for any that are due today.
    Also update the reminder date for any recurring reminders.

    Parameters:
    None

    Returns:
    None
    """
    # Get all reminders that are due today
    today = datetime.date.today()

    reminders = Reminder.query.filter(
        db.func.date(Reminder.date_time) == today
    ).all()

    # If there are no reminders, send an email and return
    if not reminders or len(reminders) == 0:
        subject = "No reminders today"
        body = """
        <html>
        <body>
            <h1 style="color: #007bff;">No Reminders Today</h1>
            <p style="font-size: 16px;">You have no reminders due today. Check back tomorrow for new reminders.</p>
        </body>
        </html>
        """
        send_email(subject, body)
        return

    # Send an email for each reminder and update the reminder date based on recurring frequency
    # Combine all reminders and send one email
    if len(reminders) > 1:
        subject = "Reminders for today"
        reminders_html = ""
        for reminder in reminders:
            reminders_html += """
            <div style="background-color: #f0f0f0; padding: 10px; border-bottom: 1px solid #ccc;">
                <h2 style="margin-top: 0;">{}</h2>
                <p style="font-size: 16px;">Event Type: {}</p>
                <p style="font-size: 16px;">Description: {}</p>
                <p style="font-size: 16px;">Date and Time: {}</p>
            </div>
            """.format(reminder.title, reminder.type, reminder.description, reminder.date_time.strftime("%Y-%m-%d %H:%M:%S"))
        body = """
        <html>
        <body>
            <h1 style="color: #007bff;">Reminders for Today</h1>
            {}
        </body>
        </html>
        """.format(reminders_html)
    else:
        subject = f"Reminder: {reminders[0].type} for {reminders[0].title}"
        body = """
        <html>
        <body>
            <h1 style="color: #007bff;">{}</h1>
            <p style="font-size: 16px;">Event Type: {}</p>
            <p style="font-size: 16px;">Description: {}</p>
            <p style="font-size: 16px;">Date and Time: {}</p>
        </body>
        </html>
        """.format(reminders[0].title, reminders[0].type, reminders[0].description, reminders[0].date_time.strftime("%Y-%m-%d %H:%M:%S"))
    send_email(subject, body)

    # Update the reminder date based on recurring frequency
    for reminder in reminders:
        # Update reminder based on frequency
        if reminder.frequency == "daily":
            reminder.date_time += datetime.timedelta(days=1)
        elif reminder.frequency == "weekly":
            reminder.date_time += datetime.timedelta(weeks=1)
        elif reminder.frequency == "monthly":
            reminder.date_time += datetime.timedelta(days=30)  # Approximate month
        elif reminder.frequency == "yearly":
            reminder.date_time += datetime.timedelta(days=365)  # Approximate year
        elif reminder.frequency == "once":
            db.session.delete(reminder)
        else:
            pass

    db.session.commit()

def send_email(subject, body):
    email_username = os.environ.get('EMAIL_USERNAME')
    email_password = os.environ.get('EMAIL_PASSWORD')
    email_to_address = os.environ.get('EMAIL_TO_ADDRESS')
    email_from_address = os.environ.get('EMAIL_FROM_ADDRESS')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['To'] = email_to_address
    msg['From'] = email_from_address

    msg.attach(MIMEText(body, 'html'))

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

        new_reminder = Reminder(title, description, date_time, type, frequency.lower())
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

# API to force sending of reminders
@app.route('/reminders/send', methods=['GET'])
def send_reminders():
    check_and_send_reminders()
    return jsonify({'message': 'Reminders sent successfully'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
