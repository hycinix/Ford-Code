import ExtractMsg
import requests
import urllib

name = "test.msg"
msg = ExtractMsg.Message( name )

urls = []

del1 = "This was flagged due to the following:"
del2 = "________________________________"


start = msg.body.find(del1) + len(del1)
end = msg.body.find(del2, start )

    
while start != (len(del1) - 1) and end != -1:
    urls += msg.body[start:end].strip().split()
    start = msg.body.find(del1, end) + len(del1)
    end = msg.body.find(del2, start )

urls = list(set(urls))

key = "AIzaSyARZsbBCxcACZDmsSNn7mJH_kmrZLcQoL0"

for i in range(len(urls)):
    ascii = urllib.quote(urls[i],"")
    googleUrl = "https://sb-ssl.google.com/safebrowsing/api/lookup?client=chrome&key="+key+"&appver=1.5.2&pver=3.1&url=" + ascii
    response = requests.get(googleUrl)
    if( response.status_code == 200 ):
        ## phishsing, malware, or both
        print("Malicious")
    elif( response.status_code == 204 ):
        ## Good url
        print("Good")
    elif( response.status_code == 400 ):
        ## Bad request
        print("Invalid")
    elif( response.status_code == 401 ):
        ## Bad key
        print("Key failure")
    elif( response.status_code == 503 ):
        ## server cannot handle request
        print("Limit reached")
    else:
        ## Unknown error
        print("Unknown")
        
