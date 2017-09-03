# This is a very simple implementation of the UCT Monte Carlo Tree Search algorithm in Python 2.7.
# The function UCT(rootstate, itermax, verbose = False) is towards the bottom of the code.
# It aims to have the clearest and simplest possible code, and for the sake of clarity, the code
# is orders of magnitude less efficient than it could be made, particularly by using a 
# state.GetRandomMove() or state.DoRandomRollout() function.
# 
# Example GameState classes for Nim, OXO and Othello are included to give some idea of how you
# can write your own GameState use UCT in your 2-player game. Change the game to be played in 
# the UCTPlayGame() function at the bottom of the code.
# 
# Written by Peter Cowling, Ed Powley, Daniel Whitehouse (University of York, UK) September 2012.
# 
# Licence is granted to freely use and distribute for any sensible/legal purpose so long as this comment
# remains in any distributed code.
# 
# For more information about Monte Carlo Tree Search check out our web site at www.mcts.ai

from math import *
import time
import random
import sys
import numpy as np
from functools import reduce

class Node:
    """ A node in the game tree. Note wins is always from the viewpoint of playerJustMoved.
        Crashes if state not specified.
    """
    def __init__(self, move = None, parent = None, state = None):
        self.move = move # the move that got us to this node - "None" for the root node
        self.parentNode = parent # "None" for the root node
        self.childNodes = np.array([])
        self.wins = 0
        self.visits = 0
        self.untriedMoves = state.GetMoves() # future child nodes
        self.playerJustMoved = state.playerJustMoved # the only part of the state that the Node needs later

    def UCTSelectChild(self):
        """ Use the UCB1 formula to select a child node. Often a constant UCTK is applied so we have
            lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits to vary the amount of
            exploration versus exploitation.
        """
        s = sorted(self.childNodes, key=lambda c: c.wins / c.visits + sqrt(2 * log(self.visits) / c.visits))[-1]
        return s
    
    def AddChild(self, m, s):
        """ Remove m from untriedMoves and add a new child node for this move.
            Return the added child node
        """
        n = Node(move = m, parent = self, state = s)
        self.untriedMoves.remove(m)
        self.childNodes = np.append(self.childNodes, n)
        return n
    
    def Update(self, result):
        """ Update this node - one additional visit and result additional wins. result must be from the viewpoint of playerJustmoved.
        """
        self.visits += 1
        self.wins += result

    def __repr__(self):
        return "[M:" + str(self.move) + " W/V:" + str(self.wins) + "/" + str(self.visits) + " U:" + str(self.untriedMoves) + "]"

    def TreeToString(self, indent):
        s = self.IndentString(indent) + str(self)
        for c in self.childNodes:
             s += c.TreeToString(indent+1)
        return s

    def IndentString(self,indent):
        s = "\n"
        for i in range (1,indent+1):
            s += "| "
        return s

    def ChildrenToString(self):
        s = ""
        for c in self.childNodes:
             s += str(c) + "\n"
        return s

class UCT:

    def __init__(self, rootstate, timeout, depthMax, displayDebug = False):
        self.timeout = timeout
        self.depthMax = depthMax
        self.rootNode = Node(state = rootstate)
        self.rootState = rootstate
        self.displayDebug = displayDebug

    def playMove(self, move):
        for child in self.rootNode.childNodes:
            if child.move == move:
                self.rootNode = child
                break
        self.rootState.DoMove(move)

    def run(self, k):
        """ Conduct a UCT search for itermax iterations starting from rootstate.
            Return the best move from the rootstate.
            Assumes 2 alternating players (player 1 starts), with game results in the range [0.0, 1.0]."""
        startTime = time.time()
        number_of_addchild = 0
        number_of_evolution = 0
        while(time.time() - startTime < self.timeout-0.20):
        #iterMax = 20000
        #while iterMax:
        #    iterMax -= 1
            explored = 0
            node = self.rootNode
            state = self.rootState.Clone()
            #clear graphics
            if self.displayDebug:
                state.clearDisplay()
                state.display('b-')
            # Select
            while node.untriedMoves == [] and node.childNodes != []: # node is fully expanded and non-terminal
                node = node.UCTSelectChild()
                state.DoMove(node.move)
                explored += 1
                if self.displayDebug:
                    state.displayMove(node.move, "r-")

            # Expand
            if node.untriedMoves != []: # if we can expand (i.e. state/node is non-terminal)
                m = random.choice(node.untriedMoves)
                state.DoMove(m)
                node = node.AddChild(m,state) # add child and descend tree
                number_of_addchild += 1
                number_of_evolution += 1
                if self.displayDebug:
                    state.displayMove(m, 'g-')
            else:
                break
            # Rollout - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
            bestResult = 0
            for i in range(0, k):
            #if True:
                stateRollout = state.Clone()
                depthAllowed=self.depthMax
                rolloutNode = node
                while depthAllowed > 0: # while state is non-terminal
                    m = stateRollout.GetRandomMove()
                    if m:
                        stateRollout.DoMove(m)
                        number_of_evolution += 1
                        if self.displayDebug:
                            stateRollout.displayMove(m, 'y-')
                    depthAllowed -= 1
                # Backpropagate
                while rolloutNode != None: # backpropagate from the expanded node and work back to the root node
                    rolloutNode.Update(stateRollout.GetResult(node.playerJustMoved)) # state is terminal. Update node with result from POV of node.playerJustMoved
                    rolloutNode = rolloutNode.parentNode

        print("explored : " + str(number_of_addchild) + " evolved : " + str(number_of_evolution) + " explored : " + str(explored), file=sys.stderr)
        bestMoves = sorted(self.rootNode.childNodes, key = lambda c: c.visits)
        if bestMoves:
            return bestMoves[-1].move # return the move that was most visited
        else:
            return None