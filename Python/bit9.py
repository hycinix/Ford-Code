import requests
import time

def Authenticate():
    '''Authenticates to parity.fordfound.org'''
    session = requests.session()
    loginurl = "https://parity.fordfound.org/login.php"
    logindata = {"username" : "brian",
            "password" : ";yL$*bp!Kq5/S?/k"}
    response = session.post(loginurl,logindata)

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

def WriteHTML( content ):
    '''Writes to test.html doc on desktop'''
##    fh = open("C:\\users\\b.marks\\desktop\\test.html","w")
    fh = open("Bit9\\test.html","w")
    fh.write(content)
    fh.close()

def WriteCSV( content ):
    '''Writes to test.csv doc on desktop'''
    date = time.strftime("%Y-%m-%d")
    filename = "Blocked_Files_(All)" + date + ".csv"
##    fh = open("C:\\users\\b.marks\\desktop\\" + filename,"w")
    fh = open("Bit9\\" + filename,"w")
    fh.write(content)
    fh.close()

def GetCSV( session ):
    '''Gets CSV file'''
    csvurl = "https://parity.fordfound.org/events.php?CSV_EXPORT"
    csvfile = session.get(csvurl)
    return csvfile.content

def main():
    '''main func'''
    print("Authenticating")
    session = Authenticate()
    print("Downloading CSV")
    csvfile = GetCSV( session )
    print("Writing CSV to disk")
    WriteCSV( csvfile )

if __name__ == '__main__':
    main()
