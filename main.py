import streamlit as st
import smtplib
import csv
import io
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email.utils

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
    behalf_of_name = st.text_input("Your name", value=st.user.name, editable=False)
    behalf_of_email = st.text_input("Your email", value=st.user.email, editable=False)

    mail_list = st.file_uploader("Upload email csv here", accept_multiple_files=False, type="csv")
    with st.form("email"):
        if mail_list is not None:
            mail_data = mail_list.read().decode("utf-8")
            csv_reader = csv.DictReader(io.StringIO(mail_data))
            emails = [row['email'] for row in csv_reader if 'email' in row and row['email']]
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
                    for i in emails:
                        msg = MIMEMultipart()
                        msg['From'] = from_email
                        msg['To'] = i
                        msg['Subject'] = subject
                        msg['Message-ID'] = email.utils.make_msgid(domain="heelas.uk")
                        msg['Reply-To'] = behalf_of_email
                        msg['Keywords'] = "hackclub, hc, Hack Club, "+behalf_of_name+", "+behalf_of_name
                        msg["Comments"] = "This email was sent by a third party please do no reply here"
                        # Replace placeholders in HTML
                        message = html_template.replace("[body]", body)
                        message = message.replace("[behalf_of_name]", behalf_of_name)
                        message = message.replace("[behalf_of_email]", behalf_of_email)

                        msg.attach(MIMEText(message, "html"))
                        mailer= smtplib.SMTP(smtp_server, 587)
                        mailer.ehlo()
                        mailer.starttls()
                        mailer.login(user, password)
                        mailer.sendmail(from_email, i, msg.as_string() )
                    st.success("Email sent")
                except Exception as e:
                    st.error(f"Mail failed: {e}")
    st.button("Log out", on_click=st.logout)