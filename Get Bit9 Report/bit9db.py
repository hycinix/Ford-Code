# -*- coding: utf-8 -*-
import requests
import time
import xlsxwriter
import sqlalchemy

def Authenticate():
    '''Authenticates to parity.fordfound.org'''
    session = requests.session()
    loginurl = "https://parity.fordfound.org/login.php"
    logindata = {"username" : "brian",
            "password" : ";yL$*bp!Kq5/S?/k"}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0",
        "Accept-Encoding": "gzip, deflate",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }
    response = session.post(loginurl,data=logindata, headers=headers)

    dashboardurl = "https://parity.fordfound.org/Dashboard/Dashboard/Dashboard.aspx"
    data = {"BootstrapSessionHandle" : Bootstrap(response.content) }
    response = session.post(dashboardurl, data)

    return session
    
def Bootstrap( content ):
    '''Gets the bootstrap number from dashboard'''
    delim = 'BootstrapSessionHandle" value="'
    start = content.find(delim) + len(delim)
    end = content.find('"', start)
    return content[start:end]

def AddBlockedFile( engine, line ):
    '''Adds entry to the BlockedFiles table'''
    line = line.replace('""','NULL').strip(",").replace("'","").replace('"',"'")
    query = "INSERT INTO BlockedFiles VALUES(" + line + ")"
    engine.execute(query)
    
def WipeThreats( engine ):    
    '''Wipes threats table'''
    query = "DELETE FROM BlockedFiles WHERE Description LIKE '%'"
    engine.execute(query)
    
def DatabaseImport( engine, csvfile ):
    '''Gets info from csv file and import to db'''

    WipeThreats( engine )

    csvRows = csvfile.split("\n")
    csvRows.remove(csvRows[0]) ## Header
    csvRows.remove(csvRows[-1]) ## Trailing whitespace
    
    for line in csvRows:
        AddBlockedFile( engine, line )

def UpdateThreats( engine ):
    md5s = GetMissingMd5( engine )
    for md5 in md5s:
        print(md5[0])
        md5 = md5[0]
        lookup = Lookup(md5)
        while lookup == "":
            lookup = Lookup(md5)
        if len(lookup) < 100:
            AddMd5( engine, md5, lookup )

def GetMissingMd5( engine ):
    '''Gets list of md5s not in database'''
    query = "SELECT DISTINCT FileHash FROM BlockedFiles WHERE FileHash NOT IN (SELECT FileHash FROM Threats)"
    md5s = []
    for row in engine.execute(query):
        md5s.append(row)
    return md5s

def Lookup( md5 ):
    '''Looks up md5 hash on virustotal'''
    url = "https://www.virustotal.com/en/file/%s/analysis/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'}
    response = requests.get(url % md5, headers=headers)
    content = response.content
    if content.find("The file you are looking for is not in our database.") == -1:
        delim = "<td>Detection ratio:</td>"
        startArea = content.find(delim) + len(delim)
        start = content.find(">", startArea) + 1
        end = content.find("</td>",start)
        return content[start:end].strip()
    return "Not Found"

def AddMd5( engine, md5, lookup ):
    '''Adds Md5 to database'''
    query = ""
    if lookup == "Not Found":
        query = "INSERT INTO Threats VALUES ('%s', %s, %s)" % (md5, "NULL", "NULL")
    else:
        lookup = lookup.split(" / ")
        positive = lookup[0]
        total = lookup[1]
        query = "INSERT INTO Threats VALUES ('%s', %s, %s)" % (md5, positive, total)
    engine.execute(query)

def GetCSV( session ):
    '''Gets CSV file'''
    csvurl = "https://parity.fordfound.org/events.php"
    response = session.get( csvurl )
    formToken = GetFormToken( response.content )
    raw_input(formToken)
    csvPayload = {
        "CSV_EXPORT" : "1",
        "formToken" : formToken
        }
    csvfile = session.post(csvurl, csvPayload)
    return csvfile.content

def GetFormToken( pageContent ):
    '''Gets formToken for csvForm'''
    areaDelim = "csvForm"
    startDelim = '<input type="hidden" name="formToken" id="formToken" value="'
    endDelim = '" />'
    start = pageContent.find(startDelim) + len(startDelim)
    end = pageContent.find(endDelim, start)
    return pageContent[start:end]
    
def WriteXlsx(csvfile):
    '''Writes spreadsheet'''
    sources = GetSources()
    csvRows = csvfile.split("\n")
    date = time.strftime("%Y-%m-%d")
    name = "Blocked_Files_(All)"
    filename = "Bit9\\" + name + date + ".xlsx"
    workbook = xlsxwriter.Workbook(filename)
    pivot = workbook.add_worksheet('Report')
    data = workbook.add_worksheet(name)

    csvHeader = csvRows[0].split(",")
    csvHeader[0] = 'Possible Source'
    header = []
    for i in range(len(csvHeader)):
        header.append({'header' : csvHeader[i].strip('"')})
    
    data.add_table('A1:N%s' % (len(csvRows) - 1), {'columns' : header })
    data.set_column('A:N', 20)

    for i in range(1, len(csvRows)):
        csvCols = csvRows[i].split(",")
        for j in range(len(csvCols)):
            if len(csvCols) < 9:
                continue
            try:
                source = sources[csvCols[9].strip('"')]
            except KeyError:
                source = 'Unknown'
            data.write(i,j,csvCols[j].strip('"').decode('utf-8'))
            data.write(i,0, source)

    workbook.close()

def main():
    '''main func'''
    print("Generating Engine")
    server = "NYCLT4940-0142\\SQL2012"
    database = "Bit9"
    engine = sqlalchemy.create_engine("mssql+pyodbc://%s/%s" % (server, database))
##    print("Authenticating")
##    session = Authenticate()
##    print("Downloading CSV")
##    csvfile = GetCSV( session )
    print("Currently Working On Downloading CSV... Using Local Copy")
    csvfile = open("C:\\Users\\b.marks\\desktop\\threats.csv","r").read()
    print("Importing into Database")
    DatabaseImport( engine, csvfile )

    print("Updating Threats")
    UpdateThreats(engine)

if __name__ == '__main__':
    main()
