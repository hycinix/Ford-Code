# -*- coding: utf-8 -*-
import sqlalchemy
import requests
import csv
import sys
import time
from multiprocessing import Process

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

    
def GetContents( incident, engine ):
    '''Gets List of Rows of the file without tickets already in db'''
    tickets = []
    result = engine.execute( "SELECT TicketId FROM Tickets" )
    for ticket in result:
        tickets.append(ticket[0])
    rows = []
    with open(incident,"rb") as incidents:
        reader = csv.reader(incidents, delimiter=',', quotechar = '"')
        for csvRow in reader:
                if csvRow[0].strip('"').isdigit() and int(csvRow[0].strip('"')) not in tickets:
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
    query = "SELECT FLOAT2 AS MWATCHID, tp_ID AS CCLnR FROM AllUserData WHERE TP_LISTID = '5E36CE12-E5BD-45F6-8260-244BE2008D7F' AND tp_IsCurrent =1 AND FLOAT2 IS NOT NULL ORDER BY TP_ID DESC"
    engine = sqlalchemy.create_engine("mssql+pyodbc://%s/%s" % (server, database))

    tickets = []
    result = mWatchEngine.execute( "SELECT TicketId FROM Tickets WHERE TicketId not in (SELECT TicketId FROM Ccls)" )
    for ticket in result:
        tickets.append(ticket[0])

    for row in engine.execute(query):
        if row[0] in tickets:
            values = "'" + str(int(row[0])) + "','" + str(row[1]) + "'"
            query = "INSERT INTO Ccls VALUES("+values+")"
            mWatchEngine.execute(query)

def main():
    '''Main func'''
    server = "NYCLT4940-0142\\SQL2012"
    database = "mWatch"
    engine = sqlalchemy.create_engine("mssql+pyodbc://%s/%s" % (server, database))

    sys.stdout.write("Authenticating\n")
    p = Process(target=DotDotDot)
    p.start()
    session = Authenticate()
    p.terminate()

    sys.stdout.write("\nDownloading Incidents\n")
    p = Process(target=DotDotDot)
    p.start()
    GetIncidents(session)
    sys.stdout.write("\nDownloading Requests\n")
    AppendRequests(session)
    p.terminate()

    csvFile = GetContents("Incidents.csv", engine)
    for line in csvFile:
        values = line.replace("'--'","null").replace(",'',",",null,").replace("'-'","null")
        query = "INSERT INTO Tickets VALUES("+values+")"
        engine.execute(query)

    print("Getting Descriptions")
    needDescripQry = "SELECT TicketId FROM GBSTickets WHERE TicketID not in (SELECT TicketId FROM Descriptions)"
    for row in engine.execute(needDescripQry):
            values = "'" + str(row[0]) + "','" + LookupDescription(row[0], session).replace("'","") + "'"
            query = "INSERT INTO Descriptions VALUES("+values+")"
            engine.execute(query)

    print("Getting Resolutions")
    needResolQry = "SELECT GBSTickets.TicketId, GBSTickets.Resolved_On FROM GBSTickets WHERE GBSTickets.Resolved_On is not null and TicketID not in ( SELECT TicketId FROM Resolutions ) UNION SELECT GBSTickets.TicketId, GBSTickets.Resolved_On FROM GBSTickets, Resolutions WHERE GBSTickets.TicketId = Resolutions.TicketId and GBSTickets.Resolved_On is not null and GBSTickets.Resolved_On <> Resolutions.Resolved_On"
    for row in engine.execute(needResolQry):
        values = "'" + str(row[0]) + "','" + LookupResolution(row[0], session).replace("'","") + "','" + str(row[1]) + "'"
        query = "INSERT INTO Resolutions VALUES("+values+")"
        engine.execute(query)

    print("Getting CCLs")
    GetCCLs(engine)
    
if __name__ == "__main__":
    ## const
    directory = "C:\\Users\\b.marks\\Documents\\GitHub\\Ford-Code\\mWatch\\Pull Data\\Incident\\"
    main()

