import smtplib
import logging
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate


def send_mail(text, stream, filename, args):

    send_from = args.mail_from
    send_to = args.mail_to
    subject = args.mail_subject
    smtp_host = args.smtp_host
    smtp_port = args.smtp_port or 25
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = send_to
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(text))
    part = MIMEApplication(
        stream.read(),
        Name=basename(filename)
    )
    part['Content-Disposition'] = 'attachment; filename="%s"' % filename
    msg.attach(part)
    try:
        logging.debug("Sending report via SMTP server %s:%s", smtp_host, smtp_port)
        smtp = smtplib.SMTP(smtp_host, smtp_port)
        smtp.sendmail(send_from, send_to, msg.as_string())
        smtp.close()
    except:
        logging.info("Report was successfully sent to %s", send_to)
        logging.error("Sending report to %s failed" % send_to)
        raise SystemExit("Please check your SMTP connection configuration. "
                         "Botstat was not able to send email with your data")
