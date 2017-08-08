#!/usr/bin/env python
import signal
from PunterClient import OnlineClient
from PunterClient import StatusDownloader

import sys
import time
import getopt

def signal_handler(signal, frame):
    raise IOError()

def printD(str):
    print >> sys.stderr, str
    pass

class LambdaPunter:

    def __init__(self, client):
        self.client = client
        self.map = client.state
        self.position = None
        self.currentlyMining = None

    def start(self):
        shouldStop = False
        while not shouldStop:
            shouldStop = self.client.readNext()
            if self.client.ready:
                self.map = client.state
                self.client.setReadCb(lambda line: self.eventIncoming(line))

    def applyMove(self, moves):
        for move in moves:
            if "claim" in move.keys():
                self.map.claimRiver(move["claim"]["punter"], move["claim"]["source"], move["claim"]["target"])

    def calculateNextMove(self):
        move = {"punter": self.client.punter, "source": 0, "target": 0}
        bestScore = 0
        bestMove = None

        scoringNodes = self.map.scoringGraph.nodes()
        i = 0
        for source in scoringNodes:
            for target in self.map.getAvailableGraph().neighbors(source):
                score = self.map.calculateScore((source, target))
                i += 1
                if bestScore < score:
                    bestScore = score
                    bestMove = (source, target)
                if self.client.getTimeout() < 0.5 :
                    printD("breaking out of time")
                    break
            if self.client.getTimeout() < 0.5:
                break
        printD("loops " + str(i))
        self.map.displayScore(self.title, bestScore)

        if bestMove != None:
            move["source"] = bestMove[0]
            move["target"] = bestMove[1]
        else:
            move = None
        return move

    def eventIncoming(self, event):
        printD("event : " + str(event))
        self.client.timeStart = time.time()

        for key,value in event.iteritems():
            if (key == u'move'):
                self.applyMove(value["moves"])
                move = self.calculateNextMove()
                if (move):
                    printD("found move, playing")
                    self.client.write({"claim":move})
                else:
                    printD("did not find any move, passing")
                    self.client.write({"pass":{"punter":self.client.punter}})
                printD("playing at :" + str(self.client.getTimeout()))
            if (key == u'stop'):
                for punterScore in value["scores"]:
                    self.map.setScores(punterScore["punter"], punterScore["score"])
                printD(str(self.map.scores))
                printD("my Score : " + str(self.map.calculateScore()))
                return True
        return False

    def close(self):
        self.map.close()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    argv = sys.argv[1:]
    ports = []
    timeout = None

    try:
        opts, args = getopt.getopt(argv, "hp:t:")
    except getopt.GetoptError:
        print 'punter.py [-h -p:port]'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'punter.py [-h -p:port]'
            sys.exit()
        elif opt == "-p":
            ports = [arg]
        elif (opt == "-t"):
            timeout = int(arg)

    gamesToPlay = []
    if ports == []:
        status = StatusDownloader().getStatus()
        if status == None:
            print "can't connect"
            exit(-2)
        for map in status.keys():
            #for now, option shall be ''
            optionFilter = ''
            for option in status[map]:
                if option == optionFilter:
                    if not timeout:
                        for timeoutiter in status[map][option]:
                            gamesToPlay.append({"map":map, "options":option, "timeout":timeoutiter, "port":status[map][option][timeoutiter]})
                    else:
                        if (status[map][option].has_key(timeout)):
                            gamesToPlay.append({"map": map, "options": option, "timeout": timeout,
                                                "port": status[map][option][timeout]})

    print ("listing games : ")
    for game in gamesToPlay:
        print str(game)

    for gameToPlay in gamesToPlay:
        client = OnlineClient(gameToPlay["port"])
        game = LambdaPunter(client)
        game.title = str(gameToPlay)

        client.timeout = gameToPlay["timeout"]
        try:
            game.start()
            print "game : " + str(gameToPlay) +" score : " + str(game.map.scores[game.client.punter])
            game.close()
            client.sock.close()
        except IOError as e:
            print e
            game.close()
            client.sock.close()


    printD("exit correctly")