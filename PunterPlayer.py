import matplotlib.pyplot as plt
import networkx as nx
import time
from model import ScoringGraph
from model import FullGraph
from model import print_err
from Discovery import DiscoveryGraph
import sys
from UCT import UCT
from model import PunterGameState

def printD(string :str):
    print(string, file = sys.stderr)

class LambdaPunter:
    def __init__(self, client, display=True):
        # initialize variables
        self.mines = []
        self.punters = None
        self.punter = None
        self.client = client
        self.scores = {}
        client.set_strategycb(lambda line: self.eventIncoming(line))
        self.leftMoves = 0
        self.display = display

    def applyMove(self, moves):
        for move in moves:
            if "claim" in move.keys():
                # claim rivers for each claim received
                self.claimRiver(move["claim"]["punter"], move["claim"]["source"], move["claim"]["target"])

    def eventIncoming(self, event :dict):
        # starts the timeout
        self.client.timeStart = time.time()
        for key, value in event.items():
            if key == u'map':
                self.setup_map(value, self.display)
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

    def setScores(self, punter :int, score :int):
        self.scores[punter] = score

    # noinspection PyMethodMayBeStatic
    def close(self):
        plt.close('all')

    def claimRiver(self, punter :int, source :int, target :int):
        assert False

    def getNextMove(self):
        assert False

    def setup_map(self, map):
        assert False

class DiscoveryStrategy(LambdaPunter):
    def setup_map(self, map :dict, should_display=True):
        fullgraph = FullGraph(map, should_display)
        scoringGraph = ScoringGraph(fullgraph, should_display=should_display)
        self.discoveryGraph = DiscoveryGraph(scoringGraph)
        self.leftMoves = nx.number_of_edges(fullgraph) / self.client.punters  # initialize number of turns
        self.discoveryGraph.head.fullGraph.display()  # display map
        self.punter = self.client.punter
        self.punters = self.client.punters

    # this function should be called when a river is claimed by a punter
    def claimRiver(self, punter :int, source :int, target :int):
        timeStart = time.time()
        self.discoveryGraph.head.fullGraph.claim(source, target)  # remove the claimed river from the main graph
        if punter == self.punter:  # if punter is player, evolve the scoringgraph
            self.discoveryGraph.claim(source, target)
            self.discoveryGraph.head.displayMove(source, target)
        print_err("claiming time = " + str(time.time() - timeStart))

    # this function calculates the best next move to play
    def getNextMove(self):
        self.discoveryGraph.explore(self.client.timeout)  # explore discoveryGraph
        timeStart = time.time()
        (bestMove, bestScore) = self.discoveryGraph.getBestMove()  # get the best move found
        print_err("getBestMoveTime = " + str(time.time() - timeStart))
        self.leftMoves -= 1  # update movesleft as we are returning the next move
        self.discoveryGraph.head.fullGraph.displayScore(self.client.title, bestScore, self.leftMoves)  # display score up to date
        if bestMove:
            bestMove = bestMove.copy()
            bestMove["claim"] =  {"punter": self.client.punter, "source": bestMove["claim"][0], "target": bestMove["claim"][1]}  # set the move
        else:
            bestMove = {"pass":{"punter":self.client.punter}}
        printD(bestMove)
        return bestMove   # return the move

class UCTStrategy(LambdaPunter):
    def setup_map(self, map :dict, should_display=True):
        self.source = PunterGameState(FullGraph(map, should_display))
        self.source.fullGraph.display()
        self.uctManager = UCT(self.source, self.client.timeout, 15, False)

    def claimRiver(self, punter, source, target):
        self.uctManager.playMove((source, target))
        self.uctManager.rootState.fullGraph.displayMove(source, target)
        self.uctManager.rootState.fullGraph.claim(source, target)  # remove the claimed river from the main graph

    def getNextMove(self):
        move = self.uctManager.run()  # get the best move found
        bestScore = 0
        bestMove = {}
        self.leftMoves -= 1  # update movesleft as we are returning the next move
        self.source.fullGraph.displayScore(self.client.title, bestScore, self.leftMoves)  # display score up to date
        bestMove["claim"] =  {"punter": self.client.punter, "source": move[0], "target": move[1]}  # set the move
        printD(bestMove)
        return bestMove   # return the move
