
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

import smtplib


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


def send_email(content: str, to_addr_email: list,subject='Balance monitoring'):
    from_addr = 'cryptogirl2@163.com'
    # password = 'pwd@PWD666'
    password = 'XJnft3R58KBRZGwS'
    smtp_server = 'smtp.163.com'

    msg = MIMEText(content)
    msg['From'] = _format_addr('hummingbot <%s>' % from_addr)
    msg['To'] = _format_addr(to_addr_email)
    msg['Subject'] = Header(str(subject), 'utf-8').encode()

    server = smtplib.SMTP(smtp_server, 25)
    # server.set_debuglevel(1)
    server.starttls()
    server.login(from_addr, password)
    server.sendmail(from_addr, to_addr_email, msg.as_string())
    server.quit()


send_email('本次打包相关信息',to_addr_email=['ancona117@163.com'])
