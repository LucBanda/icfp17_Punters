#!/usr/bin/env python
import signal
import sys
import time
import getopt
from PunterClient import OnlineClient, getStatus


# noinspection PyUnusedLocal,PyUnusedLocal
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
                # when client is ready, "steal" the reception cb, this should be avoided
                self.map = client.state
                self.client.setReadCb(lambda line: self.eventIncoming(line))

    def applyMove(self, moves):
        for move in moves:
            if "claim" in move.keys():
                # claim rivers for each claim received
                self.map.claimRiver(move["claim"]["punter"], move["claim"]["source"], move["claim"]["target"])

    def eventIncoming(self, event):
        # starts the timeout
        self.client.timeStart = time.time()
        for key, value in event.iteritems():
            if key == u'move':
                # when received a move, apply it
                self.applyMove(value["moves"])
                # ask the next move to the model
                move = self.map.getNextMove()
                # check if move was found
                if move:
                    self.client.write(move)
                else:
                    printD("did not find any move, passing")
                    self.client.write({"pass": {"punter": self.client.punter}})
                printD("playing at :" + str(self.client.getTimeout()))
            if key == u'stop':
                # when received a stop, register the scores
                for punterScore in value["scores"]:
                    self.map.setScores(punterScore["punter"], punterScore["score"])
                printD(str(self.map.scores))
                printD("my Score : " + str(self.map.scores[self.client.punter]))
                return True
        return False

    def close(self):
        if self.map:
            self.map.close()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    argv = sys.argv[1:]
    timeout = 2
    options = u""
    gamesToPlay = []
    port = None

    try:
        opts, args = getopt.getopt(argv, "ht:o:m:p:")
    except getopt.GetoptError:
        print 'punter.py [-h -p port -m map -o options -t timeout]'
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print '-h -p port -m map -o options -t timeout'
            sys.exit()
        elif opt == "-o":
            options = arg
        elif opt == "-t":
            timeout = int(arg)
        elif opt == "-m":
            maps = [arg]
        elif opt == "-p":
            port = int(arg)

    if port is None:
        # play with online server
        status = getStatus()
        if status is None:
            print "can't connect"
            exit(-2)
        maps = status.keys()
        for map in maps:
            for option in status[map]:
                if option == options:
                    if not timeout:
                        for timeoutiter in status[map][option]:
                            gamesToPlay.append({"map": map, "options": option, "timeout": timeoutiter,
                                                "port": status[map][option][timeoutiter]})
                    else:
                        if timeout in status[map][option]:
                            gamesToPlay.append({"map": map, "options": option, "timeout": timeout,
                                                "port": status[map][option][timeout]})
        print ("listing games : ")
        for game in gamesToPlay:
            print str(game)
        for gameToPlay in gamesToPlay:
            client = OnlineClient("punter.inf.ed.ac.uk", gameToPlay["port"])
            game = LambdaPunter(client)
            client.title = str(gameToPlay)

            client.timeout = gameToPlay["timeout"]
            try:
                game.start()
                print "game : " + str(gameToPlay) + " score : " + str(game.map.scores[game.client.punter])
                game.close()
                client.sock.close()
            except IOError as e:
                print e
                game.close()
                client.sock.close()

    else:
        # play with local server provided by compete at http://git.kthxb.ai/compete/icfpc2017
        # instanciate and connect online client
        client = OnlineClient("localhost", port)
        # instanciate a punter
        game = LambdaPunter(client)
        # set the parameters of the client
        client.title = "local map"
        client.timeout = timeout
        try:
            # start the game
            game.start()
            # if game exits correctly, it means game has ended
            print "local game score : " + str(game.map.scores[game.client.punter])
            game.close()
            client.sock.close()
        except IOError as e:
            # this happens in case of connection error
            print e
            game.close()
            client.sock.close()

    printD("exit correctly")
