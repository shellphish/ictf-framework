from config import config

import sendgrid
from sendgrid.helpers.mail import *
import smtplib
from email.mime.text import MIMEText

ACCT_VERIFIED_SUBJECT = "Your iCTF Team Account has been verified!"
ACCT_VERIFIED_MSG = """
Hello!
The academic status of the iCTF account for your team (%s) has been verified!

Thank you!
- The iCTF Team
"""

ACCT_DECLINED_SUBJECT = "We could not verify your iCTF account!"
ACCT_DECLINED_MSG = """
Hello!
Unfortunately, we were unable to verify the academic status iCTF account for your team, %s.
Please double-check the information you submitted, especially the academic verification information, and try again.

If you have any questions, please contact ctf-admin@lists.cs.ucsb.edu.

Thank you!
- The iCTF Team
"""

TICKET_DST = "ictf-admin@googlegroups.com"
TICKET_SUBJECT = "[ticket][#%s][%s] %s"
TICKET_MSG = """
Ticket ID: %s

Team Name: %s

Team E-mail: %s

Team ID: %s

Subject: %s

Timestamp: %s

Message: %s

"""

PASSWORD_SUBJECT = "Your iCTF Team Account Credentials"
PASSWORD_MSG = """
Hello!
Thank you for registering your team for iCTF!
Your credentials are:
E-mail: %s
Password: %s

If you filled out the academic status questionaire, your information still needs to be verified.
If this does not happen within two weeks, please contact ctf-admin@lists.cs.ucsb.edu

Thank you!
- The iCTF Team
"""


RESET_VERIFY_SUBJECT = "iCTF Password Reset Request"
RESET_VERIFY_MSG = """
Hello!
We've received a request to reset the password for your team's iCTF account.
Click this link to verify this request, and a new password will be emailed to you.

%s

If you did NOT initiate this request, you can safely ignore this message.

Thank you!
- The iCTF Team
"""

RESET_SUBJECT = "Your iCTF Password has been Reset!"
RESET_MSG = """
Hello!
We have completed your password reset request.
Your new credentials are:

E-mail: %s
Password: %s

Thank you!
- The iCTF Team
"""

def _send_msg(dsts, subject, body):
    if isinstance(dsts,str):
        dsts = [dsts]
    sg = sendgrid.SendGridAPIClient(apikey=config['SENDGRID_API_KEY'])
    msg = Content('text/plain', body)
    from_addr = Email(config['EMAIL_SENDER'])
    to_addrs =  [Email(dst) for dst in dsts]
    for t in to_addrs:
        m = Mail(from_email=Email(config['EMAIL_SENDER']), to_email=t, subject=subject, content=msg)
        print m.get()
        sg.client.mail.send.post(request_body=m.get())

def send_password_msg(dsts, email, password):
    body = PASSWORD_MSG % (email, password)
    _send_msg(dsts, PASSWORD_SUBJECT ,body)

def send_verify_msg(dst, url):
    body = RESET_VERIFY_MSG % url
    _send_msg([dst], RESET_VERIFY_SUBJECT, body)

def send_reset_msg(dst, email, password):
    body = RESET_MSG % (email, password)
    _send_msg([dst], RESET_VERIFY_SUBJECT, body)

def send_acct_verified_msg(dsts,team_name):
    _send_msg(dsts, ACCT_VERIFIED_SUBJECT, ACCT_VERIFIED_MSG % team_name)

def send_acct_declined_msg(dst,team_name):
    _send_msg([dst], ACCT_DECLINED_SUBJECT, ACCT_DECLINED_MSG % team_name)

def send_ticket(ticket_id, team_name, team_email, team_id, subject, ts, msg):
    subj = TICKET_SUBJECT % (str(ticket_id), team_name , subject)
    body = TICKET_MSG % (str(ticket_id), team_name, team_email, team_id, subject, ts, msg)
    _send_msg([TICKET_DST], subj, body)
