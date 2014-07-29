#! /usr/bin/python

import smtplib

import os
import os.path
import time

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# src == my email address
# dest == recipient's email address
src = "b.marks@fordfound.org"
dest = "b.marks@fordfound.org"

file = "C:\\RVTools\\CSV\\RVTools_tabvPartition.csv"
timestamp = time.ctime(os.path.getmtime(file))

# Create message container - the correct MIME type is multipart/alternative.
msg = MIMEMultipart('alternative')
msg['Subject'] = "Storage Report - " + time.strftime("%d/%m/%y")
msg['From'] = src
msg['To'] = dest

# Create the body of the message (a plain-text and an HTML version).
text = "Team,\nHere is the Storage Report http://ffsmq0681/\nPlease let me know if you have any questions.\n\nThank you,\nBrian"
html = """\
<html>
	<head></head>
	<body>
    <p>Team,<br/>
    Here is the <a href='http://ffsmq0681/'>Storage Report</a> generated on %s,<br/>
    Please let me know if you have any questions.<br/>
	Thank you,<br/>
	Brian<br/></p>
	</body>
</html>
""" % (timestamp)

# Record the MIME types of both parts - text/plain and text/html.
part1 = MIMEText(text, 'plain')
part2 = MIMEText(html, 'html')

# Attach parts into message container.
# According to RFC 2046, the last part of a multipart message, in this case
# the HTML message, is best and preferred.
msg.attach(part1)
msg.attach(part2)

# Send the message via local SMTP server.
s = smtplib.SMTP('smtp.fordfound.org')
# sendmail function takes 3 arguments: sender's address, recipient's address
# and message to send - here it is sent as one string.
s.sendmail(src, dest, msg.as_string())
s.quit()