from model import LambdaMap
import socket
import json
import sys
import time

def printD(str):
    print >> sys.stderr, str

class OnlineClient:

    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cb = lambda line: self.readCb(line)
        self.state = None
        self.handshake = None
        self.setup = False
        self.punter = None
        self.punters = None
        self.ready = None
        self.connect(host, port)
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
            exit(0)
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
                self.state = LambdaMap(value, self.punters, self.punter)
        if (self.punter != None) \
                and (self.handshake != None) \
                and (self.state != None)\
                and (self.punters != None):
            self.state.punter = self.punter
            self.state.punters = self.punters
            self.write({"ready": self.punter})
            self.ready = True