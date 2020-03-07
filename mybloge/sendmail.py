from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

import aiosmtplib
import logging

def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))

async def sendemail(to_addr,code,from_addr = 'yulansp@qq.com',password = 'qmlwskumxghzhgji',smtp_server = 'smtp.qq.com'):
    msg = MIMEText('<html><body><h3>感谢你的到来，这是你的验证码: %s (20分钟内有效)</h></body></html>'%code, 'html', 'utf-8')
    msg['From'] = _format_addr('语阑 <%s>' % from_addr)
    msg['To'] = _format_addr('<%s>' % to_addr)
    msg['Subject'] = Header('验证你的电子邮件地址', 'utf-8').encode()

    try:
        async with aiosmtplib.SMTP(hostname=smtp_server, port=465,use_tls=True) as server:
            await server.login(from_addr,password)
            await server.send_message(msg)
            await server.quit()
            logging.info('sendemail to %s'%to_addr)
    except aiosmtplib.SMTPException as e:
        logging.info('sendemail to %s failed:%s'%(to_addr,e))