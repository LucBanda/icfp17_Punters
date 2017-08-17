import socket
import json
import sys
import time
import urllib2


def printD(str):
    print >> sys.stderr, str
    pass


class OnlineClient:
    # use this client to connect to a lambda punter server
    def __init__(self, addr, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # register local callback for handshake
        self.cb = lambda line: self.decodeCb(line)
        self.state = None
        self.handshake = None
        self.setup = False
        self.punter = None
        self.punters = None
        self.ready = None
        self.connect(addr, port)
        self.timeout = 10.0
        self.timeStart = 0

    #   this function returns the timeout updated
    def getTimeout(self):
        return self.timeout - (time.time() - self.timeStart)

    #   this is used to update the cb
    def setReadCb(self, cb):
        self.cb = cb

    # connects the socket
    def connect(self, host, port):
        retry = 50
        # retry connection 50 times in case of fail
        while retry:
            try:
                self.sock.connect((host, port))
                break
            except:
                printD("retrying connection ... ")
                retry -= 1
        if retry == 0:
            printD("can't connect")
            raise IOError()

        # start handshake
        self.write({"me": "LucB"})

    #   this function sends a dictionnary to the server
    def write(self, dict):
        # get json from dict
        strToSend = json.dumps(dict)
        # remove spaces
        strToSend.replace(" ", "")
        # forge protocol s:json
        strToSend = str(len(strToSend)) + ":" + strToSend
        # trace execution
        printD("sending : " + strToSend)
        # send to the server
        self.sock.send(strToSend)

    # this function blocks and read the next answer from the server
    def readNext(self):
        line = ""
        while True:
            # receive one char and append to the line
            line += self.sock.recv(1)
            # when size is received, decode it
            if line.endswith(":"):
                line = line.split(":")[0]
                size = int(line)

                # and wait for the next <size> bytes
                line = self.sock.recv(size)
                while len(line) != size:
                    line += self.sock.recv(size - len(line))

                # once received, print them
                printD(str(size) + "," + str(len(line)) + ":" + line)

                # call the reception callback with a dictionary loaded from json
                return self.cb(json.loads(line))

            #   reception callback to perform the handshake

    def set_strategycb(self, cb):
        self.strategyCb = cb

    def start(self):
        shouldStop = False
        while not shouldStop:
            shouldStop = self.readNext()

    def decodeCb(self, event):
        # iterate over received items
        for key, value in event.iteritems():
            if key == u'you':
                # this is ack of 'me'
                self.handshake = True
                self.readySent = False
            if key == u'punter':
                # this is my punter id
                self.punter = value
            if key == u'punters':
                # this is the list of punters
                self.punters = value
            if key == u'map':
                # this is the map
                self.state = value
        if (self.punter is not None) \
                and (self.handshake is not None) \
                and (self.state is not None) \
                and (self.punters is not None):
            # when everything is received, instanciate the model LambdaMap
            # send ready to server
            if not self.ready:
                self.strategyCb({'map':self.state})
                self.write({"ready": self.punter})
                self.ready = True
                return False
            else:
                return self.strategyCb(event)


def getStatus():
    response = urllib2.urlopen('http://punter.inf.ed.ac.uk/status.html')
    html = response.read()
    soup = bs.BeautifulSoup(html)
    soup.prettify()
    tables = soup.findAll('table')
    statusTable = []
    for table in tables:
        if table["class"] == "table table-bordered":
            statusTable = table
    tables = []
    for line in statusTable.findAll('tr'):
        list = []
        for entry in line.findAll('td'):
            list.append(entry.text)
        tables.append(list)
    dict = {}
    for line in tables:
        if len(line) == 6:
            if len(line[0].split(' ')) == 4:
                # if game is waiting for punters
                puntersLeft = int(line[0].split(' ')[3].strip('(').strip(')').split('/')[1]) - \
                              int(line[0].split(' ')[3].strip('(').strip(')').split('/')[0])
                level = line[5]
                optionsstr = line[2]
                timeout = int(line[3].split(' ')[0])
                port = int(line[4])

                if puntersLeft == 1:
                    if level not in dict:
                        dict[level] = {optionsstr: {}}

                    if optionsstr not in dict[level]:
                        dict[level][optionsstr] = {timeout: {}}

                    dict[level][optionsstr][timeout] = port

    return dict
