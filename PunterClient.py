from model import LambdaMap
import socket
import json
import sys

def printD(str):
    print >> sys.stderr, str

class OnlineClient:

    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cb = lambda line: self.readCb(line)
        self.state = LambdaMap(None)
        self.handshake = None
        self.setup = False
        self.punter = None
        self.punters = None
        self.ready = None
        self.connect(host, port)

    def setReadCb(self, cb):
        self.cb = cb

    def connect(self, host, port):
        self.sock.connect((host, port))
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
                self.cb(json.loads(line))
                break

    def readCb(self, event):
        for key,value in event.iteritems():
            if (key == u'you'):
                self.handshake = True
            if (key == u'punter'):
                self.punter = value
            if (key == u'punters'):
                self.punters = value
            if (key == u'map'):
                self.state = LambdaMap(value)
        if (self.punter != None) \
                and (self.handshake != None) \
                and (self.state != None)\
                and (self.punters != None):
            self.write({"ready": self.punter})
            self.ready = True