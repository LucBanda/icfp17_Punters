from model import LambdaMap
import socket
import json
import sys
import time
import urllib2
import BeautifulSoup as bs

def printD(str):
    print >> sys.stderr, str
    pass

class OnlineClient:

    def __init__(self, addr, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cb = lambda line: self.readCb(line)
        self.state = None
        self.handshake = None
        self.setup = False
        self.punter = None
        self.punters = None
        self.ready = None
        self.connect(addr, port)
        self.timeout = 10.0
        self.timeStart = 0

    def getTimeout(self):
        return self.timeout - (time.time() - self.timeStart)

    def setReadCb(self, cb):
        self.cb = cb

    def connect(self, host, port):
        retry = 50
        while retry:
            try:
                self.sock.connect((host, port))
                break
            except:
                printD("retrying connection ... ")
                retry -= 1
        if (retry == 0):
            printD("can't connect")
            raise IOError()

        self.write({"me":"LucB"})

    def write(self, dict):
        strToSend = json.dumps(dict)
        strToSend.replace(" ", "")
        strToSend = str(len(strToSend)) + ":" + strToSend
        printD("sending : " + strToSend)
        self.sock.send(strToSend)

    def readNext(self):
        line = ""
        while True:
            line += self.sock.recv(1)
            if (line.endswith(":")):
                line = line.split(":")[0]
                size = int(line)
                line = self.sock.recv(size)
                while len(line) != size:
                    line += self.sock.recv(size - len(line))
                printD(str(size) + "," + str(len(line)) + ":" + line)
                return self.cb(json.loads(line))

    def readCb(self, event):
        for key,value in event.iteritems():
            if (key == u'you'):
                self.handshake = True
            if (key == u'punter'):
                self.punter = value
            if (key == u'punters'):
                self.punters = value
            if (key == u'map'):
                self.state = value
        if (self.punter != None) \
                and (self.handshake != None) \
                and (self.state != None)\
                and (self.punters != None):
            self.state = LambdaMap(self, self.state, self.punters, self.punter)
            self.write({"ready": self.punter})
            self.ready = True


class StatusDownloader:

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def getStatus(self):
        response = urllib2.urlopen('http://punter.inf.ed.ac.uk/status.html')
        html = response.read()
        soup = bs.BeautifulSoup(html)
        soup.prettify()
        tables = soup.findAll('table')
        for table in tables:
            if (table["class"] == "table table-bordered"):
                statusTable = table
        tables = []
        for line in statusTable.findAll('tr'):
            list = []
            for entry in line.findAll('td'):
                list.append(entry.text)
            tables.append(list)
        dict={}
        for line in tables:
            if len(line) == 6:
                if len(line[0].split(' ')) == 4:
                    #if game is waiting for punters
                    puntersLeft = int(line[0].split(' ')[3].strip('(').strip(')').split('/')[1]) - \
                                  int(line[0].split(' ')[3].strip('(').strip(')').split('/')[0])
                    level = line[5]
                    optionsstr = line[2]
                    timeout = int(line[3].split(' ')[0])
                    port = int(line[4])

                    if (puntersLeft == 1):
                        if not dict.has_key(level):
                            dict[level] = {optionsstr : {}}

                        if not dict[level].has_key(optionsstr):
                            dict[level][optionsstr] = {timeout : {}}

                        dict[level][optionsstr][timeout] = port

        return dict