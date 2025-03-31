import datetime
from app import db, Reminder, send_email


def check_reminders():
    """
    Check the reminders in the database and send emails for any that are due today.
    Also update the reminder date for any recurring reminders.

    Parameters:
    None

    Returns:
    None
    """
    
    # Get all reminders that are due today
    now = datetime.datetime.now()

    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + datetime.timedelta(days=1)

    reminders = Reminder.query.filter(
        db.func.date(Reminder.date_time) >= start_of_day,
        db.func.date(Reminder.date_time) < end_of_day
    ).all()

    # If there are no reminders, send an email and return
    if not reminders or reminders.count() == 0:
        subject = "No reminders today"
        body = "No reminders today. Check back tomorrow!"
        send_email(subject, body)
        return

    # Send an email for each reminder and update the reminder date based on recurring frequency
    for reminder in reminders:
        subject = f"Reminder: {reminder.type} for {reminder.title}"
        body = (
            f"Hey, don't forget! Today is \n"
            f"Event Type: {reminder.type}:\n"
            f"Title: {reminder.title}\n"
            f"Description: {reminder.description}"
        )
        send_email(subject, body)

        # Update reminder based on frequency
        if reminder.frequency == "daily":
            reminder.date_time += datetime.timedelta(days=1)
        elif reminder.frequency == "weekly":
            reminder.date_time += datetime.timedelta(weeks=1)
        elif reminder.frequency == "monthly":
            reminder.date_time += datetime.timedelta(days=30)
        elif reminder.frequency == "yearly":
            reminder.date_time += datetime.timedelta(days=365)
        else:
            db.session.delete(reminder)

    db.session.commit()


if __name__ == "__main__":
    with db.session.begin():
        check_reminders()
