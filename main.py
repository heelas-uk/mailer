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
    behalf_of_email = st.code(st.user.email, language="markdown")

    mail_list = st.file_uploader("Upload email csv here", accept_multiple_files=False, type="csv")
    with st.form("email"):
        if mail_list is not None:
            mail_data = mail_list.read().decode("utf-8")
            csv_reader = csv.DictReader(io.StringIO(mail_data))
            emails = [row['email'] for row in csv_reader if 'email' in row and row['email']]
            names = [row['names'] for row in csv_reader if 'names' in row and row['names']]
            scheduled = st.datetime_input(label="When would you like to schedule the email? To send ASAP leave blank", min_value="now", value=None, format="DD/MM/YYYY")
            if scheduled is not None:
                local = scheduled.replace(tzinfo=timezone)
                utc_shedule = local.astimezone(ZoneInfo("UTC"))
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
                    for i, n in zip(emails, names):
                        # Replace placeholders in HTML
                        message = html_template.replace("[body]", body)
                        message = message.replace("[behalf_of_name]", str(behalf_of_name))
                        message = message.replace("[behalf_of_email]", str(behalf_of_email))
                        message = message.replace("[name]", n)
                        if scheduled is not None:
                            headers = {
                                "api-key": st.secrets['brevo_api'],
                                "replyTo.email": "21heelasa@sta.cc",
                                "replyTo.name": "Alfred Heelas",
                                "tags": f"hackclub, hc, Hack Club, {behalf_of_email}, {behalf_of_name}",
                                "sender.email": "void@sta.hackclub.uk",
                                "sender.name": f"STA Hak Club {behalf_of_name}",
                                "to.email": i,
                                "to.name": n,
                                "subject": subject,
                                "scheduledAt": utc_shedule,
                                "htmlContent": message
                            }
                        else:
                            headers = {
                                "api-key": st.secrets['brevo_api'],
                                "replyTo.email": "21heelasa@sta.cc",
                                "replyTo.name": "Alfred Heelas",
                                "tags": f"hackclub, hc, Hack Club, {behalf_of_email}, {behalf_of_name}",
                                "sender.email": "void@sta.hackclub.uk",
                                "sender.name": f"STA Hak Club {behalf_of_name}",
                                "to.email": i,
                                "to.name": n,
                                "subject": subject,
                                "htmlContent": message
                            }
                        print(headers)
                        requests.post("https://api.brevo.com/v3/smtp/email", json=headers)
                        st.success("Email sent")
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to send email: {str(e)}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")
    if st.button("Log Out"):
        st.logout()