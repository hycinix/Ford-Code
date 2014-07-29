import os
import glob ## Dir with wildcard
import csv
import requests
import time
import sys
import datetime
import smtplib
import sqlalchemy
import pyodbc
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
from multiprocessing import Process

George = True

def mwatchcsrf( content ):
    '''Gets mwatchcsrf (unique token) from sdp.mymwatch.com login page'''
    start = "<input type=\"hidden\" value=\""
    end = "\""
    startIndex = content.find(start) + len(start)
    endIndex  = content.find(end,startIndex)
    return content[startIndex:endIndex]

def write( content ):
    '''Saves content to folder on desktop'''
    ## File to save output to
##    path = "C:\\Users\\b.marks\\Desktop\\Incident\\currSession.html"
    path = "Incident\\currSession.html"
    fh = open(path,"w")
    fh.write(content)
    fh.close()

def writeCSV( content ):
    '''Saves CSV content to folder on desktop'''
    ## File to save output to
    date = time.strftime("%Y%m%d")
    ## path = "C:\\Users\\b.marks\\Desktop\\Incident\\Incidents_%s.csv" % (date) ## If saving multiple files
##    path = "C:\\Users\\b.marks\\Desktop\\Incident\\Incidents.csv"
    path = "Incident\\Incidents.csv"
    fh = open(path,"w")
    fh.write(ResolveDoubleNewLine(content))
    fh.close()

def ResolveDoubleNewLine( content ):
    '''Resolves the double new line in CSV files'''
    resolver = content.replace("\r\n","\n")
    return resolver

def ResolveLinks( content ):
    '''Resolves internal links'''
    resolver = content.replace("/Portal/","https://sdp.mymwatch.com/Portal/")
    return resolver

    
def Authenticate():
    '''Authenticated to sdp.mymwatch.com'''
    username = "b.marks@fordfound.org"
    password = "ZaQwSx12"
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
##    write(ResolveLinks(response.content)) ## Outputs HTML file


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
#    incidentUrl = "https://sdp.mymwatch.com/Portal/index.php?r=servicedelivery/ticket/ExportToCSV&ticketType=1&action=IncidentFilter&fStatus=ViewAll&fStatusname=All%20Incidents&fCategory=&fGroupname=72&fPriority=&fromDate=Created%20Date%20From&toDate=Created%20Date%20To&fStatusId=&undefined&&searchTxt="
    response = session.get(incidentUrl)
    writeCSV(response.content)

def GetFiles():
    '''Gets all files with Incidents*.csv and Advanced...*.csv and finds the most recent one (going by filename). Returns incident,advanced'''
##    path = "C:\\Users\\b.marks\\Desktop\\Incident\\"
    path = "Incident\\"
    os.chdir(path)
    incidents = glob.glob("Incidents*.csv")
    advanceds = glob.glob("AdvancedSearchTicket*.csv")
    ## If saving multiple files
    ## incident = max(incidents)
    ## advanced = max(advanceds)
    incident = path + "Incidents.csv"
    advanced = path + "AdvancedSearchTicket.csv"
    return incident,advanced

def GetDescriptions( advanced ):
    '''Gets dictionary of TicketID to Description'''
    descriptions = {}
    with open(advanced,"rb") as advancedCSV:
        reader = csv.reader(advancedCSV, delimiter=',', quotechar='"')
        for row in reader:
            if row[0] not in descriptions:
                descriptions[row[0]] = row[1]
    advancedCSV.close()
    return descriptions

def UpdateDescription(ticketID, session ):
    '''Updates descriptions.csv file from web'''
    description = LookupDescription( ticketID, session )
    description = description.replace("\r\n"," ").replace("Problem:"," ").replace("Problem Description:"," ")
    description = description.strip()
    writeHandle = open("descriptions.csv","a")
    writeHandle.write('"%s","%s"\n' % (ticketID, description))
    writeHandle.close()
    return description

def GetResolutions(advanced):
    '''Gets dictionary of TicketID to Resolution'''
    resolutions = {}
    with open(advanced,"rb") as advancedCSV:
        reader = csv.reader(advancedCSV, delimiter=',', quotechar='"')
        for row in reader:
            if row[0] not in resolutions:
                resolutions[row[0]] = row[1]
    advancedCSV.close()
    return resolutions

def UpdateResolution( ticketID, session ):
    '''Updates resolutions.csv file from web'''
    resolution = LookupResolution( ticketID, session )
    resolution = resolution.strip().replace("\r\n"," ")
    writeHandle = open("resolutions.csv","a")
    writeHandle.write('"%s","%s"\n' % (ticketID, resolution))
    writeHandle.close()
    return resolution
    

def GetContents( incident ):
    '''Gets List of Rows of the file'''
    fhr = open(incident,"r")
    file_read = fhr.read()
    rows = file_read.split("\n")
    fhr.close()
    return rows

def GenerateLine( rowsList, descriptions, resolutions, rowNum, session, users, issues, ccls ):
    '''Writes one line into the destination file'''
    col = rowsList[rowNum].split('","')
    if( len(col) < 40 ):
        return ""

    condition = True
    
    if George:
        condition = col[25] in users and col[9] not in issues ## Requestor in users and issue not in issues
    else:
        condition = col[25] in users or col[22] in users or col[23] == "FordGBS" ## Request in users or owner in users or group == FordGBS

##    if( col[0] != "" ## Row isn't blank
##
##        ## George
####        and col[25] in users ## If Requestor is in user list
####        and col[9] not in issues): ## and Issue type not in issue list
##
##        ## BSD
##        and (col[25] in users ## If Owner is in user list
##            or col[22] in users
##             or col[23] == "FordGBS")): ## If Requestor is in user list

    if col[0] != "" and condition:
        col[0] = col[0].strip('"') ## fixes leading quote
        col[-1] = col[-1].strip('"') ## fixes trailing quote

        resolution = ""
        description = ""
        duration = ""
        
        try:
            description = descriptions[col[0]]
        except KeyError:
            descriptions[col[0]] = UpdateDescription( col[0], session )
            description = descriptions[col[0]]

        try:
            test = ccls[col[0]]
        except:
            ccls[col[0]] = "Bunnies"
        if col[3] == "Resolved" or col[3] == "Closed":
            duration = str(GetDifference( col[5], col[31] )) + " Hours"
            try:
                resolution = resolutions[col[0]]
            except KeyError:
                resolutions[col[0]] = UpdateResolution( col[0], session )
                resolution = resolutions[col[0]]
                
        columns = [col[0].strip('"'),
                   ccls[col[0]],
                   description, ## Description
                   col[9], ## Issue Type
                   col[22], ## Owner
                   col[12], ## Priority
                   col[3], ## Status
                   col[25], ## Requestor
                   duration, ## Time to complete
                   col[5], ## Created
                   col[31], ## Resolved
                   col[33], ## Closed
                   resolution ## Resolution
                   ]
        
        oneRow = "~".join(columns)
        return oneRow + "\n"
    return ""



def GenerateHeader( rowsList ):
    '''Generates CSV header'''
    col = rowsList[0].split('","')
    col[0] = col[0].strip('"') ## fixes leading quote
    col[0] = "Ticket ID"
    col[-1] = col[-1].strip('"') ## fixes trailing quote
    columns = [
            col[0].strip('"'), ## Ticket
            "CCL#",
            "Description", ## Description
            col[9], ## Issue Type
            col[22], ## Owner
            col[12], ## Priority
            col[3], ## Status
            col[25], ## Requestor
            "Completion Time", ## Duration
            col[5], ## Created 
            col[31], ## Resolved
            col[33], ## Closed
            "Resolution Comments"
            ]
    oneRow = "~".join(columns)
    return oneRow + "\n"

def GenerateFile( session ):
    '''Generates result file with all the bells and whistles'''
##    if George:
##        writeHandle = open("C:\\Users\\b.marks\\Desktop\\Incident\\George_Report.csv","w")
##    else:
##        writeHandle = open("C:\\Users\\b.marks\\Desktop\\Incident\\BSD_mWatch_Tickets_Report.csv","w")
    if George:
        writeHandle = open("Incident\\George_Report.csv","w")
    else:
        writeHandle = open("Incident\\BSD_mWatch_Tickets_Report.csv","w")
        
    writeHandle.write("sep=~\n")
    incident,advanced = GetFiles()
    MakeNewFiles()
    descriptionFile = "descriptions.csv"
    resolutionFile = "resolutions.csv"
    descriptions = GetDescriptions( descriptionFile )
    resolutions = GetResolutions( resolutionFile )
    rows = GetContents( incident )
    writeHandle.write( GenerateHeader( rows ))
    readHandle = open("users.txt","r")
    users = readHandle.read().split("\n")
    readHandle.close()

    readHandle = open("issues.txt","r")
    issues = readHandle.read().split("\n")
    readHandle.close()

    ccls = GetCCLs()

    for i in range(1, len(rows) - 1):
        sys.stdout.write("\r%s%%" % (round(float(i*100)/(len(rows) - 1),2)))
        writeHandle.write(GenerateLine( rows, descriptions, resolutions, i, session, users, issues, ccls ))
        sys.stdout.flush()
    writeHandle.close()

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
        resolution = resolution.replace("&nbsp"," ")
    while resolution.find("<") != -1:
        subset = resolution[resolution.find("<"):resolution.find(">") + 1]
        resolution = resolution.replace(subset," ")
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
    while description.find("&nbsp") != -1:
        description = description.replace("&nbsp"," ")
    while description.find("<") != -1:
        subset = description[description.find("<"):description.find(">") + 1]
        description = description.replace(subset," ")
    return description

def MakeNewFiles():
    if not os.path.exists("descriptions.csv"):
        f = open("descriptions.csv","w")
        f.write('"TicketID","Description"\n')
        f.close()

    if not os.path.exists("resolutions.csv"):
        f = open("resolutions.csv","w")
        f.write('"TicketID","Resolution"\n')
        f.close()

def GetDifference( before, after ):
    '''Gets the difference between the two date strings in hours. Date format is mwatch format'''
    dateFormat = "%Y-%m-%d %H:%M:%S"
    beforeDate = datetime.datetime.strptime(before, dateFormat)
    afterDate = datetime.datetime.strptime(after, dateFormat)
    differenceTime = afterDate - beforeDate
    seconds = differenceTime.total_seconds()
    hours = int(seconds / 3600)
    return hours

def SendGeorge():
    '''Sends email to George'''
    to = [
        "b.marks@fordfound.org"
        ]
    cc = [
        "bmarks1994@gmail.com"
        ]
    
    subject = "BSD - mWatch Ticket Report"
    text = '''Hello George,
Attached is a report of the tickets requested by the BSD
Please tell me if you have any questions or concerns.
Thanks,
Brian'''
##    attach = "C:\\Users\\B.marks\\Desktop\\Incident\\George_Report.csv"
    attach = "Incident\\George_Report.csv"
    mail( to, cc, subject, text, attach )

def mail(to, cc, subject, text, attach):
    '''Sends email from b.marks@fordfound.org'''
    username = "b.marks@fordfound.org"
    password = "ZaQwSx12"
    msg = MIMEMultipart()

    msg['From'] = username
    msg['To'] = ", ".join(to)
    msg['Subject'] = subject
    msg['Cc'] = ", ".join(cc)

    msg.attach(MIMEText(text))

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(open(attach, 'rb').read())
    Encoders.encode_base64(part)
    part.add_header('Content-Disposition',
                    'attachment; filename="%s"' % os.path.basename(attach))
    msg.attach(part)

    mailServer = smtplib.SMTP("smtp.fordfound.org", 25)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(username, password)
    mailServer.sendmail(username, to+cc, msg.as_string())
    mailServer.close()

def GetCCLs():
    '''Gets list of Tickets to CCL#'''
    server = "ffazu0317\\gbs2uat2012"
    database = "FF_Grants_TSP1"
    query = "select top 2 * from subject"
    engine = sqlalchemy.create_engine("mssql+pyodbc://%s/%s" % (server, database))

    ccl = {}
    for row in engine.execute(query):
        ccl[row[0]] = row[1]

    return ccl


def main():
    '''Main func'''
    sys.stdout.write("Authenticating\n")
    p = Process(target=DotDotDot)
    p.start()
    session = Authenticate()
    p.terminate()

    sys.stdout.write("\nDownloading\n")
    p = Process(target=DotDotDot)
    p.start()
##    GetIncidents(session)
    p.terminate()
    
    sys.stdout.write("\nGenerating File\n")
##    p = Process(target=DotDotDot)
##    p.start()
    GenerateFile( session )
##    p.terminate()

    sys.stdout.write("\nThe csv has been created\n")

    if George:
        sys.stdout.write("\nSending Email\n")
        p = Process(target=DotDotDot)
        p.start()
        SendGeorge()
        p.terminate()    

if __name__ == "__main__":
    main()
