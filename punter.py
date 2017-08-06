#!/usr/bin/env python
import signal
from model import River
from PunterClient import OnlineClient
import sys

def signal_handler(signal, frame):
    raise IOError()

def printD(str):
    print >> sys.stderr, str

class LambdaPunter:

    def __init__(self, client):
        self.client = client
        self.map = client.state
        self.position = None
        self.currentlyMining = None

    def start(self):
        while True:
            self.client.readNext()
            if self.client.ready:
                self.map = client.state
                self.client.setReadCb(lambda line: self.eventIncoming(line))

    def applyMove(self, moves):
        for move in moves:
            if "claim" in move.keys():
                if not self.map.riverClaimed.has_key(int(move["claim"]["punter"])):
                    self.map.riverClaimed[int(move["claim"]["punter"])] = []
                self.map.riverClaimed[int(move["claim"]["punter"])].append(River(move["claim"]["source"], move["claim"]["target"]))



    def findshortestMineFromMine(self, startMine, currentloc, recursionFactor):
        if recursionFactor == 5:
            return (10,None)

        if (currentloc == 7):
            pass
        if (currentloc == 16):
            pass
        shortest = 0
        shortestDist = 10
        for river in self.map.sites[currentloc].rivers:
            if self.map.sites[river.otherSide(currentloc)].isMine and river.otherSide(currentloc) != startMine:
                return (recursionFactor, river.otherSide(currentloc))
            else:
                (distance, mine) = self.findshortestMineFromMine(startMine, river.otherSide(currentloc), recursionFactor+1)
                if distance < shortestDist:
                    shortestDist = distance
                    path = river.otherSide(currentloc)
        if (shortestDist == 10):
            return (shortestDist, None)
        return (shortestDist, path)

    def calculateNextMove(self):
        move = {"punter":self.client.punter, "source":0, "target":0}

        if (self.currentlyMining == None):
            for mine in self.map.mines:
                mineFree = True
                for river in self.map.sites[mine].rivers:
                    if self.map.riverClaimed.has_key(self.client.punter) and river in self.map.riverClaimed[self.client.punter]:
                        mineFree = False
                if mineFree:
                    self.currentlyMining = (mine, mine)
                    break;
        if self.currentlyMining == None:
            printD("serious issue, no free mine found")
            return None

        (distance, path) = self.findshortestMineFromMine(self.currentlyMining[0], self.currentlyMining[1], 0)

        if (path != None):
            move["source"] = self.currentlyMining[1]
            move["target"] = path
            self.currentlyMining = (self.currentlyMining[0], path)
            if self.map.sites[path].isMine:
                self.currentlyMining = None
        else:
            move = None
        return move

    def eventIncoming(self, event):
        printD("event : " + str(event))
        for key,value in event.iteritems():
            if (key == u'move'):
                self.applyMove(value["moves"])
                self.map.display()
                move = self.calculateNextMove()
                if (move):
                    printD("found move, playing")
                    self.client.write({"claim":move})
                else:
                    printD("did not find any move, passing")
                    self.client.write({"pass":{"punter":self.client.punter}})

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    client = OnlineClient("punter.inf.ed.ac.uk", 9005)
    game = LambdaPunter(client)
    try:
        game.start()
    except IOError as e:
        print e
        client.sock.close()

    printD("exit correctly")