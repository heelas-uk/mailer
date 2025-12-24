import streamlit as st
import smtplib
import csv
import io
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email.utils
from datetime import datetime
from client_timezone import client_timezone
from zoneinfo import ZoneInfo
import requests
timezone = client_timezone(key="client-timezone")

def login_screen():
    st.subheader("Please log in.")
    st.button("Log in with Microsoft Org account", on_click=st.login)

smtp_server = st.secrets['smtp_server']
from_email = st.secrets['from']
user = st.secrets['smtp_user']
password = st.secrets['password']

st.title("Fancy email sending system")
st.write("Because **why** manually type out email addresses when you can spend 5 hours writing an app to use a .csv file?")
if not st.user.is_logged_in:
    login_screen()
else:
    behalf_of_name = st.text_input("Your name", value=st.user.name)
    behalf_of_email = st.text_input("Your email", value=st.user.email)

    mail_list = st.file_uploader("Upload email csv here", accept_multiple_files=False, type="csv")
    with st.form("email"):
        if mail_list is not None:
            mail_data = mail_list.read().decode("utf-8")
            # Parse the CSV once, then derive emails and names from the same rows
            rows = list(csv.DictReader(io.StringIO(mail_data)))
            emails = [r.get('email') for r in rows if r.get('email')]
            names = [(r.get('names') or r.get('name') or "").strip() for r in rows if (r.get('email'))]
            scheduled = st.datetime_input(label="When would you like to schedule the email? To send ASAP leave blank", min_value=None, value=None, format="DD/MM/YYYY")
            if scheduled is not None:
                try:
                    tz = ZoneInfo(timezone) if not isinstance(timezone, ZoneInfo) else timezone
                except Exception:
                    tz = ZoneInfo("UTC")
                local = scheduled if scheduled.tzinfo else scheduled.replace(tzinfo=tz)
                utc_schedule = local.astimezone(ZoneInfo("UTC")).isoformat()
            st.write("Emails to be sent to:")
            for i in emails:
                st.code(i, language=None)

            st.write("## Compose your email")
            subject = st.text_input("Subject")
            body = st.text_area("Body text", help="You should not enter any custom names")
            submitted = st.form_submit_button("Send")
            if submitted == True:
                with open("email.html", "r", encoding="utf-8") as f:
                    html_template = f.read()

                # EMAIL TIME
                try: 
                    if not emails:
                        st.warning("No recipients found in CSV.")
                    else:
                        # Constant HTTP headers for Brevo API
                        http_headers = {
                            "api-key": st.secrets['brevo_api'],
                            "accept": "application/json",
                            "content-type": "application/json"
                        }
                        sent = 0
                        for i, n in zip(emails, names):
                            # Replace placeholders in HTML
                            message = html_template.replace("[body]", body)
                            message = message.replace("[behalf_of_name]", str(behalf_of_name))
                            message = message.replace("[behalf_of_email]", str(behalf_of_email))
                            message = message.replace("[name]", n or "")

                            # Brevo API payload
                            payload = {
                                "replyTo": {"email": "21heelasa@sta.cc", "name": "Alfred Heelas"},
                                "tags": ["hackclub", "hc", "Hack Club", str(behalf_of_email), str(behalf_of_name)],
                                "sender": {"email": "void@sta.hackclub.uk", "name": f"STA Hack Club {behalf_of_name}"},
                                "to": [{"email": i, "name": n}],
                                "subject": subject,
                                "htmlContent": message
                            }
                            if scheduled is not None:
                                payload["scheduledAt"] = utc_schedule  # ISO-8601 UTC string

                            resp = requests.post("https://api.brevo.com/v3/smtp/email", json=payload, headers=http_headers, timeout=15)
                            resp.raise_for_status()
                            sent += 1

                        st.success(f"Email queued to {sent} recipient(s)")
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to send email: {str(e)}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")
