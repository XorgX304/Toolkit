import re
import sys

def  readText(txtpath):
    fp = open(txtpath,'r')
    ff = fp.read()
    fp.close()
    return ff

def  extractIp(data):
    ipPattern = re.compile('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
    findIP = re.findall(ipPattern,data)
    ip = list(set(findIP))
    ip = sorted(ip)
    for i in ip:
        print i

def  extractDomain(data):
    domainPattern = re.compile(r'[a-zA-Z0-9]*\.{0,1}[a-zA-Z0-9]*\.{0,1}[a-zA-Z0-9]*\.{0,1}[a-zA-Z0-9]*\.{0,1}[a-zA-Z0-9]*\.{0,1}[a-zA-Z0-9]+\.{1}[a-zA-Z]+')
    findDomain = re.findall(domainPattern,data)
    domain = list(set(findDomain))
    domain = sorted(domain)
    for i in domain:
        print i

if __name__ == "__main__":
    try:
        data = readText(sys.argv[1])
        for opt in sys.argv:
            if opt == 'ip':
                extractIp(data)
                break
            if opt == 'domain':
                extractDomain(data)
                break
    except:
        print 'usage: ' + sys.argv[0] + ' FileName' +' {ip,domain}'
