# -*- coding: utf-8 -*-
import os
import smtplib
import sqlalchemy
import xlsxwriter
import requests
import xlrd
from requests_ntlm import HttpNtlmAuth
import csv
import sys
import time
from multiprocessing import Process
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
import win32api
import win32con
import win32evtlog
import win32security
import win32evtlogutil


def DownloadFile(url, cred):
    '''Downloads file with credentials'''
    local_filename = "sharepoint_tickets.xlsx"
    r = requests.get(url, auth=cred)
    f = open(local_filename, 'wb')
    for chunk in r.iter_content(chunk_size=512 * 1024):
        if chunk: # filter out keep-alive new chunks
            f.write(chunk)
    f.close()
    return

def InsertComments(engine):
    '''Inserts comments + satisfaction in DB'''
    wb = xlrd.open_workbook("sharepoint_tickets.xlsx")
    sheet = wb.sheets()[0]
    for i in range(1, sheet.nrows):
        if (sheet.cell(i,14).value != "" or sheet.cell(i,15).value != ""):
            values = "'" + str(int(sheet.cell(i,0).value)) + "','" + str(sheet.cell(i,14).value) + "','" + str(sheet.cell(i,15).value.encode('utf-8')) + "'"
            query = "INSERT INTO Comments VALUES("+values+")"
            engine.execute(query)

def mwatchcsrf( content ):
    '''Gets mwatchcsrf (unique token) from sdp.mymwatch.com login page'''
    start = "<input type=\"hidden\" value=\""
    end = "\""
    startIndex = content.find(start) + len(start)
    endIndex  = content.find(end,startIndex)
    return content[startIndex:endIndex]

def WriteCSV( content ):
    '''Saves CSV content to folder on desktop'''
    ## File to save output to
    date = time.strftime("%Y%m%d")
    path = directory + "Incidents.csv"
    fh = open(path,"w")
    fh.write(ResolveDoubleNewLine(content))
    fh.close()

def AppendCSV( content ):
    '''Appends to CSV file'''
    ## File to save output to
    path = directory + "Incidents.csv"
    resolveDub = ResolveDoubleNewLine(content)
    withoutHeaders= resolveDub[resolveDub.find("\n") + 2:] ## +2 to not include newline
    fh = open(path,"a")
    fh.write(ResolveDoubleNewLine(content))
    fh.close()

def ResolveDoubleNewLine( content ):
    '''Resolves the double new line in CSV files'''
    resolver = content.replace("\r\n","\n")
    return resolver

def Authenticate( password ):
    '''Authenticated to sdp.mymwatch.com'''
    username = "b.marks@fordfound.org"
    postUrl = "https://sdp.mymwatch.com/Portal/index.php?r=User/authentication/Login&goto=https%3A%2F%2Fsdp.mymwatch.com%2FPortal%2Findex.php"
    session = requests.Session()

    ## To get the token
    response = session.get(postUrl)

    postData = {
        "Login[username]" : username,
        "Login[password]" : password,
        "mwatchcsrf" : mwatchcsrf(response.content)
        }

    response = session.post(postUrl,postData)


    ## Returns session
    return session

def DotDotDot():
    '''Loading dots'''
    while True:
        time.sleep(1)
        sys.stdout.write(".")
        

def GetIncidents( session ):
    '''Gets Incidents_*.csv file and saves it'''
    incidentUrl = "https://sdp.mymwatch.com/Portal/index.php?r=servicedelivery/ticket/ExportToCSV&ticketType=1&action=IncidentFilter&fStatus=ViewAll&fStatusname=All+Incidents&undefined&&searchTxt="
    response = session.get(incidentUrl)
    WriteCSV(response.content)

def AppendRequests( session ):
    '''Gets Requests_*.csv file and appends it to Incidents_*.csv file'''
    requestUrl = "https://sdp.mymwatch.com/Portal/index.php?r=servicedelivery/ticket/ExportToCSV&ticketType=2&action=RequestFilter&fStatus=ViewReqAll&fStatusname=All+Requests&undefined&&searchTxt="
    response = session.get(requestUrl)
    AppendCSV(response.content)
    
def LookupResolution( ticketID, session ):
    '''Looks up resoltuion of ticket. Ticket must be either closed or resolved'''
    delimeter = 'Resolution Comments </td>\n            <td width="65%" class="bg-col2">'
    url = "https://sdp.mymwatch.com/Portal/index.php?r=servicedelivery/ticket/view&id=%s" % (ticketID)
    response = session.get(url)
    content = response.content
    start = content.find(delimeter) + len(delimeter)
    end = content.find("</tr>",start)
    resolution = content[start:end]

    while resolution.find("&nbsp;") != -1:
        resolution = resolution.replace("&nbsp;"," ")
    while resolution.find("<") != -1:
        subset = resolution[resolution.find("<"):resolution.find(">") + 1]
        resolution = resolution.replace(subset," ").strip().replace("\r\n"," ")
    return resolution

def LookupDescription( ticketID, session ):
    '''Looks up description of ticket'''
    url = "https://sdp.mymwatch.com/Portal/index.php?r=servicedelivery/ticket/view&id=%s" % (ticketID)
    response = session.get(url)
    content = response.content

    delimeters = [
        '<td  class="bg-col1" width="17.9%" >Description</td>'
        ]

    description = ""
    for i in range(len(delimeters)):
        delimeter = delimeters[i]
        start = content.find(delimeter) + len(delimeter)
        end = content.find("</tr>",start)
        description = content[start:end]
        if not ( description == "" or start == (-1 + len(delimeter))):
            break
    while description.find("&nbsp;") != -1:
        description = description.replace("&nbsp;"," ")
    subset = description[description.find("<"):description.find(">") + 1]
    while description.find("<") != -1 and subset != '':
        description = description.replace(subset," ")
        subset = description[description.find("<"):description.find(">") + 1]
    description = description.replace("\r\n"," ").replace("Problem:"," ").replace("Problem Description:"," ").strip()
    return description

    
def GetContents( incident ):
    '''Gets List of Rows of the file'''
    rows = []
    with open(incident,"rb") as incidents:
        reader = csv.reader(incidents, delimiter=',', quotechar = '"')
        for csvRow in reader:
                if csvRow[0].strip('"').isdigit():
                        row = ""
                        for col in csvRow:
                                row += ("'" + str(col).replace("'","") + "',")
                        row = row.strip(',')
                        rows.append(row)
        incidents.close()
        return rows

def GetCCLs(mWatchEngine):
    '''Gets list of Tickets to CCL#'''
    server = "ffnyc0355"
    database = "FordNet_Content"
    query = "SELECT FLOAT2 AS MWATCHID, tp_ID AS CCLnR, nvarchar3 as Status FROM AllUserData WHERE TP_LISTID = '5E36CE12-E5BD-45F6-8260-244BE2008D7F' AND tp_IsCurrent =1 AND FLOAT2 IS NOT NULL ORDER BY TP_ID DESC"
    engine = sqlalchemy.create_engine("mssql+pyodbc://%s/%s" % (server, database))

    tickets = []
    ## Wipe CCls
    mWatchEngine.execute("DELETE FROM Ccls WHERE Ccl > 0")
    result = mWatchEngine.execute( "SELECT TicketId FROM Tickets") ## WHERE TicketId not in (SELECT TicketId FROM Ccls)" )
    for ticket in result:
        tickets.append(ticket[0])

    for row in engine.execute(query):
        if row[0] in tickets:
            values = "'" + str(int(row[0])) + "','" + str(row[1]) + "','" + str(row[2]) + "'"
            query = "INSERT INTO Ccls VALUES("+values+")"
            mWatchEngine.execute(query)

def GenerateFileXl( George, engine ):
    '''Generates result file with all the bells and whistles'''

    if George:
        workbook = xlsxwriter.Workbook(directory + "BSD_mWatch_Tickets_Report.xlsx", {'strings_to_numbers' : True, 'sort' : True})
        result = engine.execute( "SELECT * FROM GeorgeReport ORDER BY TicketID DESC" )

    else:
        workbook = xlsxwriter.Workbook(directory + "BSD_mWatch_Tickets_Report_All.xlsx", {'strings_to_numbers' : True, 'sort' : True})
        result = engine.execute( "SELECT * FROM KevinReport ORDER BY TicketID DESC" )

    worksheet = workbook.add_worksheet('mWatch Tickets')

    headerFormat = workbook.add_format()
    headerFormat.set_pattern(1)
    headerFormat.set_bg_color('#4F81BC')
    headerFormat.set_font_color('#FFFFFF')
    headerFormat.set_bold()

    rowFormat = workbook.add_format()
    rowFormat.set_align('top')
    rowFormat.set_text_wrap()
    rowFormat.set_bottom()
    rowFormat.set_bottom_color('#717B96')

    for i in range(len(result.keys())):
        worksheet.write(0,i,result.keys()[i], headerFormat)

    if George:
        worksheet.set_column('A:B', 15 ) ## TicketID, Ticket_Type
        worksheet.set_column('C:C', 10 ) ## CCL#
        worksheet.set_column('D:D', 60 ) ## Description
        worksheet.set_column('E:F', 20 ) ## Issue Type, Owner
        worksheet.set_column('G:G', 10 ) ## Priority
        worksheet.set_column('H:M', 20 ) ## others
        worksheet.set_column('N:N', 60 ) ## Resolution
        worksheet.set_column('O:P', 10 ) ## Satisfaction, Comment
    else:    
        worksheet.set_column('A:A', 15 ) ## TicketID
        worksheet.set_column('B:B', 10 ) ## CCL#
        worksheet.set_column('C:C', 15 ) ## CCL Status        
        worksheet.set_column('D:D', 60 ) ## Description
        worksheet.set_column('E:F', 20 ) ## Issue Type, Owner
        worksheet.set_column('G:G', 10 ) ## Priority
        worksheet.set_column('H:M', 20 ) ## others
        worksheet.set_column('N:N', 60 ) ## Resolution


    rows = result.fetchall()

    for i in range(len(rows) - 1):
        for j in range(len(result.keys())):
            if rows[i][j] != None:
                worksheet.write(i + 1, j, (str(rows[i][j])).decode('utf-8','ignore'), rowFormat )
            else:
                worksheet.write(i + 1, j, "", rowFormat )
        worksheet.set_row(i+1,40)

    worksheet.autofilter(0,0,len(rows) - 1,len(result.keys()) - 1)
    
    workbook.close()

def SendSharepoint( password ):
    '''Sends email to sharepoint'''
    to = [
        "testpsd@fordnet.fordfoundation.org"
        ]
    cc = [
        "b.marks@fordfoundation.org"
        ]
    
    subject = "mWatch Ticket Reports"
    text = ""
    attach = directory + "BSD_mWatch_Tickets_Report.xlsx"
    mail( to, cc, subject, text, attach, password )

def SendBSD( password ):
    '''Sends email to BSD'''
    to = [
        "k.zhao@fordfoundation.org",
        "q.sun@fordfoundation.org"
        ]
    cc = [
        "b.marks@fordfoundation.org"
        ]
    
    subject = "BSD - mWatch Ticket Report - " + time.strftime("%m/%d")
    text = '''[This is an automatic message]\n
Hello BSD Team,\n
Attached is a report of the tickets requested by the BSD\n
Please email Brian Marks at b.marks@fordfoundation.org\n
or call x4990 if you have any questions.'''
    attach = directory + "BSD_mWatch_Tickets_Report_All.xlsx"
    mail( to, cc, subject, text, attach, password )

def SendTeam( password ):
    '''Sends sharepoint link email to BSD'''
    to = [
        "G.Fertig@fordfoundation.org",
        "L.Ponce@fordfoundation.org",
        "B.Mendoza@fordfoundation.org",
        "K.Kothur@fordfoundation.org",
        "O.Triunfo@fordfoundation.org",
        "M.Agrawal@fordfoundation.org",
        "Q.Sun@fordfoundation.org",
        "H.Kwok@fordfoundation.org",
        "K.Zhao@fordfoundation.org"
        ]
    cc = [
        "b.marks@fordfoundation.org"
        ]
    
    subject = "BSD - mWatch Ticket Report - " + time.strftime("%m/%d")
    text = '''[This is an automatic message]\n
Hello BSD Team,\n
Attached is a report of the tickets requested by the BSD\n
Please email Brian Marks at b.marks@fordfoundation.org\n
or call x4990 if you have any questions.\n
https://fordnet.fordfound.org/ts/OPER/IT/BSD/Documents/mWatch%20Ticket%20Reports/BSD_mWatch_Tickets_Report.xlsx 
'''
    mail( to, cc, subject, text, None, password )

def mail(to, cc, subject, text, attach, password ):
    '''Sends email from b.marks@fordfound.org'''
    username = "b.marks@fordfound.org"
    msg = MIMEMultipart()

    msg['From'] = username
    msg['To'] = ", ".join(to)
    msg['Subject'] = subject
    msg['Cc'] = ", ".join(cc)

    msg.attach(MIMEText(text))

    if attach:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(attach, 'rb').read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition','attachment; filename="%s"' % os.path.basename(attach))
        msg.attach(part)

    mailServer = smtplib.SMTP("smtp.fordfound.org", 25)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(username, password)
    mailServer.sendmail(username, to+cc, msg.as_string())
    mailServer.close()

def main():
    '''Main func'''
    ph = win32api.GetCurrentProcess()
    th = win32security.OpenProcessToken(ph, win32con.TOKEN_READ)
    my_sid = win32security.GetTokenInformation(th, win32security.TokenUser)[0]
     
    applicationName = "mWatch Pull Db"
    eventID = 1
    category = 5	# Shell
    myType = win32evtlog.EVENTLOG_WARNING_TYPE

    server = "FFSMQ3302"
    database = "mWatch"
    engine = sqlalchemy.create_engine("mssql+pyodbc://%s/%s" % (server, database))

    passQuery = "SELECT TicketDescription FROM Descriptions WHERE TicketId = 0"
    password = (engine.execute(passQuery).first())[0]

    eventID += 1
    win32evtlogutil.ReportEvent(applicationName, eventID, eventCategory=category, eventType=myType, strings=["Getting Comments from Sharepoint","Getting Comments from Sharepoint"], data="Application\0Data".encode("ascii"), sid=my_sid)

    print("Getting Comments From Sharepoint")
    ## Resets comments table
    query = "DELETE FROM Comments WHERE TicketId > 0"
    engine.execute(query)
    
    cred = HttpNtlmAuth('FORDFOUNDATION\\b.marks',password)
    url = "https://fordnet.fordfound.org/ts/OPER/IT/BSD/Documents/mWatch%20Ticket%20Reports/BSD_mWatch_Tickets_Report.xlsx"
    DownloadFile(url,cred)

    ## Adds comments/satisfaction from file
    InsertComments(engine)

    eventID += 1
    win32evtlogutil.ReportEvent(applicationName, eventID, eventCategory=category, eventType=myType, strings=["Authenticating","Authenticating"], data="Application\0Data".encode("ascii"), sid=my_sid)

    sys.stdout.write("Authenticating\n")
    p = Process(target=DotDotDot)
    p.start()
    session = Authenticate( password )
    p.terminate()

    eventID += 1
    win32evtlogutil.ReportEvent(applicationName, eventID, eventCategory=category, eventType=myType, strings=["Downloading Incidents","Downloading Incidents"], data="Application\0Data".encode("ascii"), sid=my_sid)

    sys.stdout.write("\nDownloading Incidents\n")
    p = Process(target=DotDotDot)
    p.start()
    GetIncidents(session)

    eventID += 1
    win32evtlogutil.ReportEvent(applicationName, eventID, eventCategory=category, eventType=myType, strings=["Downloading Requests","Downloading Requests"], data="Application\0Data".encode("ascii"), sid=my_sid)

    sys.stdout.write("\nDownloading Requests\n")
    AppendRequests(session)
    p.terminate()

    eventID += 1
    win32evtlogutil.ReportEvent(applicationName, eventID, eventCategory=category, eventType=myType, strings=["Adding Tickets to Table","Adding Tickets to Table"], data="Application\0Data".encode("ascii"), sid=my_sid)

    print("Adding Tickets to Table")
    ## Resets Ticket table
    query = "DELETE FROM Tickets WHERE TicketId > 0"
    engine.execute(query)

    ## Adds tickets from file
    csvFile = GetContents(directory + "Incidents.csv")
    for line in csvFile:
        values = line.replace("'--'","null").replace(",'',",",null,").replace("'-'","null")
        query = "INSERT INTO Tickets VALUES("+values+")"
        engine.execute(query)

    eventID += 1
    win32evtlogutil.ReportEvent(applicationName, eventID, eventCategory=category, eventType=myType, strings=["Getting Descriptions","Getting Descriptions"], data="Application\0Data".encode("ascii"), sid=my_sid)

    print("Getting Descriptions")
    needDescripQry = "SELECT TicketId FROM GBSTickets WHERE TicketID not in (SELECT TicketId FROM Descriptions)"
    for row in engine.execute(needDescripQry):
            values = "'" + str(row[0]) + "','" + LookupDescription(row[0], session).replace("'","") + "'"
            query = "INSERT INTO Descriptions VALUES("+values+")"
            engine.execute(query)

    eventID += 1
    win32evtlogutil.ReportEvent(applicationName, eventID, eventCategory=category, eventType=myType, strings=["Getting Resolutions","Getting Resolutions"], data="Application\0Data".encode("ascii"), sid=my_sid)

    print("Getting Resolutions")
    ## If there isn't a resolved_date or the resolved_date is different than the new one, delete the resolution
    query = "DELETE FROM Resolutions WHERE TicketId in (SELECT TicketId FROM GBSTickets WHERE Resolved_On is null UNION SELECT GBSTickets.TicketId FROM GBSTickets WHERE GBSTickets.Resolved_On is not null and TicketID not in ( SELECT TicketId FROM Resolutions ) UNION SELECT GBSTickets.TicketId FROM GBSTickets, Resolutions WHERE GBSTickets.TicketId = Resolutions.TicketId and GBSTickets.Resolved_On is not null and GBSTickets.Resolved_On <> Resolutions.Resolved_On)"
    engine.execute(query)
    
    needResolQry = "select GBSTickets.TicketId, GBSTickets.Resolved_On FROM GBSTickets WHERE GBSTickets.Resolved_On is not null and GBSTickets.TicketID not in (SELECT TicketId FROM Resolutions)"
    for row in engine.execute(needResolQry):
        values = "'" + str(row[0]) + "','" + LookupResolution(row[0], session).replace("'","") + "','" + str(row[1]) + "'"
        print(row[0])
        query = "INSERT INTO Resolutions VALUES("+values+")"
        engine.execute(query)

    eventID += 1
    win32evtlogutil.ReportEvent(applicationName, eventID, eventCategory=category, eventType=myType, strings=["Getting CCLs","Getting CCLs"], data="Application\0Data".encode("ascii"), sid=my_sid)

    print("Getting CCLs")
    GetCCLs(engine)

    eventID += 1
    win32evtlogutil.ReportEvent(applicationName, eventID, eventCategory=category, eventType=myType, strings=["Generating Files","Generating Files"], data="Application\0Data".encode("ascii"), sid=my_sid)

    print("Generating Files")
    GenerateFileXl( True, engine )

    GenerateFileXl( False, engine )

    eventID += 1
    win32evtlogutil.ReportEvent(applicationName, eventID, eventCategory=category, eventType=myType, strings=["Sending Email","Sending Email"], data="Application\0Data".encode("ascii"), sid=my_sid)

    print("Sending Email")
    SendSharepoint( password )
    SendBSD( password )
    SendTeam( password )

if __name__ == "__main__":
    ## const
    directory = "C:\\Users\\b.marks\\Documents\\GitHub\\Ford-Code\\mWatch\\Pull Data DB\\"
    main()
