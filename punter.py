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

    def calculateNextMove(self):
        move = {"punter": self.client.punter, "source": 0, "target": 0}
        availableGraph = self.map.getAvailableGraph()
        bestScore = 0
        bestMove = None

        for source in self.map.scoringGraph.nodes():
            for target in self.map.getAvailableGraph().neighbors(source):
                if self.map.getAvailableGraph().edge[source][target]["claimed"] == -1:
                    score = self.map.calculateScore((source, target))
                    if bestScore < score:
                        bestScore = score
                        bestMove = (source, target)

        if bestMove != None:
            move["source"] = bestMove[0]
            move["target"] = bestMove[1]
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
            if (key == u'stop'):
                for punterScore in value["scores"]:
                    self.map.setScores(punterScore["punter"], punterScore["score"])
                printD(str(self.map.scores))
                raise IOError()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    printD("starting..")
    client = OnlineClient("punter.inf.ed.ac.uk", 9003)
    game = LambdaPunter(client)
    try:
        game.start()
    except IOError as e:
        print e
        client.sock.close()

    printD("exit correctly")