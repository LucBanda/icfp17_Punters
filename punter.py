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
                self.map.claimRiver(move["claim"]["punter"], River(move["claim"]["source"], move["claim"]["target"]))


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
        pass

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
    client = OnlineClient("punter.inf.ed.ac.uk", 9003)
    game = LambdaPunter(client)
    try:
        game.start()
    except IOError as e:
        print e
        client.sock.close()

    printD("exit correctly")