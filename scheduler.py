from app import db, check_and_send_reminders

if __name__ == "__main__":
    with db.session.begin():
        check_and_send_reminders()