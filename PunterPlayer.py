import matplotlib.pyplot as plt
import networkx as nx
import time
from model import ScoringGraph
from model import FullGraph
from model import print_err
from Discovery import DiscoveryGraph

class LambdaPunter:
    def __init__(self, client):
        # initialize variables
        self.mines = []
        self.punters = None
        self.punter = None
        self.client = client
        self.scores = {}
        client.set_strategycb(lambda line: self.eventIncoming(line))
        self.leftMoves = 0

    def applyMove(self, moves):
        for move in moves:
            if "claim" in move.keys():
                # claim rivers for each claim received
                self.claimRiver(move["claim"]["punter"], move["claim"]["source"], move["claim"]["target"])

    def eventIncoming(self, event):
        # starts the timeout
        self.client.timeStart = time.time()
        for key, value in event.iteritems():
            if key == u'map':
                self.setup_map(value)
            if key == u'move':
                # when received a move, apply it
                self.applyMove(value["moves"])
                # ask the next move to the model
                move = self.getNextMove()
                # check if move was found
                if move:
                    self.client.write(move)
                else:
                    print_err("did not find any move, passing")
                    self.client.write({"pass": {"punter": self.client.punter}})
                print_err("playing at :" + str(self.client.getTimeout()))
            if key == u'stop':
                # when received a stop, register the scores
                for punterScore in value["scores"]:
                    self.scores[punterScore["punter"]] = punterScore["score"]
                    print_err(str(self.scores))
                print_err("my Score : " + str(self.scores[self.client.punter]))
                return True
        return False

    def displayScore(self, mapTitle, score):
        plt.title(mapTitle + str(score) + " (left:" + str(self.leftMoves) + ")")

    def setScores(self, punter, score):
        self.scores[punter] = score

    # noinspection PyMethodMayBeStatic
    def close(self):
        plt.close('all')

    def claimRiver(self, punter, source, target):
        assert False

    def getNextMove(self):
        assert False

    def setup_map(self, map):
        assert False

class DiscoveryStrategy(LambdaPunter):
    def setup_map(self, map):
        fullgraph = FullGraph(map)
        scoringGraph = ScoringGraph(fullgraph)
        self.discoveryGraph = DiscoveryGraph(scoringGraph)
        self.leftMoves = nx.number_of_edges(fullgraph) / self.client.punters  # initialize number of turns
        self.discoveryGraph.head.fullGraph.display()  # display map
        self.punter = self.client.punter
        self.punters = self.client.punters

    # this function should be called when a river is claimed by a punter
    def claimRiver(self, punter, source, target):
        timeStart = time.time()
        if punter == self.punter:  # if punter is player, evolve the scoringgraph
            self.discoveryGraph.claim(source, target)
            self.discoveryGraph.head.displayMove(source, target)
        self.discoveryGraph.head.fullGraph.claim(source, target)  # remove the claimed river from the main graph
        print_err("claiming time = " + str(time.time() - timeStart))

    # this function calculates the best next move to play
    def getNextMove(self):
        self.discoveryGraph.explore(self.client.timeout)  # explore discoveryGraph
        timeStart = time.time()
        (bestMove, bestScore) = self.discoveryGraph.getBestMove()  # get the best move found
        print_err("getBestMoveTime = " + str(time.time() - timeStart))
        self.leftMoves -= 1  # update movesleft as we are returning the next move
        self.displayScore(self.client.title, bestScore)  # display score up to date
        if bestMove:
            bestMove = bestMove.copy()
            bestMove["claim"] =  {"punter": self.client.punter, "source": bestMove["claim"][0], "target": bestMove["claim"][1]}  # set the move
        else:
            bestMove = {"pass":{"punter":self.client.punter}}
        print bestMove
        return bestMove   # return the move
