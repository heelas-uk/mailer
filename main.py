import streamlit as st
import smtplib
import csv
import io
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

smtp_server = st.secrets['smtp_server']
from_email = st.secrets['from']
user = st.secrets['smtp_user']
password = st.secrets['bloody_python']

st.title("Fancy email sending system")
st.write("Because **why** manually type out email addresses when you can spend 5 hours writing an app to use a .csv file?")
mail_list = st.file_uploader("Upload email csv here", accept_multiple_files=False, type="csv")
with st.form("email"):
    if mail_list is not None:
        mail_data = mail_list.read().decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(mail_data))
        emails = [row['email'] for row in csv_reader if 'email' in row and row['email']]
        st.write(emails)

        st.write("## Compose your email")
        subject = st.text_input("Subject")
        body = st.text_area("Body text", help="You can add a custom name by typing [name]")
        submitted = st.form_submit_button("Send")
        if submitted == True:
            # EMAIL TIME
            try: 
                for i in emails:
                    msg = MIMEMultipart()
                    msg['From'] = from_email
                    msg['To'] = i
                    msg['Subject'] = subject
                    message = body
                    msg.attach(MIMEText(message))
                    mailer= smtplib.SMTP(smtp_server, 587)
                    mailer.ehlo()
                    mailer.starttls()
                    mailer.login(user, password)
                    mailer.sendmail(from_email, i, msg.as_string() )
            except:
                st.error("Mail failed")