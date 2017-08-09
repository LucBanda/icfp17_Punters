import matplotlib.pyplot as plt
import networkx as nx
import sys

def printD(str):
    print >> sys.stderr, str
    pass

class Site:
    def __init__(self, id, x, y, ):
        self.id = id
        self.x = x
        self.y = y
        self.isMine = False


class LambdaMap:
    def __init__(self, client, map, punters, punter):
        #initialize variables
        self.mines = []
        self.punters = punters
        self.punter = punter
        self.client = client
        self.currentScore = 0
        self.fig = plt.figure(figsize=(10, 30))
        self.scores = {}
        self.graph = None
        self.scoringGraph = None
        self.endpoints = None

        #protect function
        if map == None:
            return

        # this is the main graph, containing all sites and rivers
        # edges taken by opponents are removed
        self.graph = nx.Graph()

        #populate sites in main graph
        for site in map["sites"]:
            self.graph.add_node(site["id"])
            self.graph.node[site["id"]]["site"] = Site(site["id"], site["x"], site["y"])

        #populate edges in main graph
        self.graph.add_edges_from([(river["source"], river["target"]) for river in map["rivers"]])

        #get mines in self.mines
        self.mines = map["mines"]

        #add mines to main graph
        for mine in self.mines:
            self.graph.node[mine]["site"].isMine = True

        # precalculate score for all site and all mines as it is static
        for mine in self.mines:
            list = nx.single_source_shortest_path_length(self.graph, mine)
            nx.set_node_attributes(self.graph, "pathForMine_" + str(mine), list)

        #create scoring graph, this graph will maintain current taken path
        self.scoringGraph = nx.Graph()

        #import mines in scoring graph
        for mine in self.mines:
            self.scoringGraph.add_node(mine, attr_dict=self.graph.node[mine])

        self.endpoints = self.scoringGraph.nodes()

        #initialize number of turns
        self.leftMoves = nx.number_of_edges(self.graph) / self.punters

        #display map
        self.displayMap()

# this function allows to claim a river in scoringGraph only. Used to test pathes
    def claimInScoringGraph(self, source, target):
        #if target is not in graph, add it
        for nodeToClaim in [source, target]:
            if not self.scoringGraph.has_node(nodeToClaim):
                nodeAttr = self.graph.node[target]
                self.scoringGraph.add_node(target, attr_dict=nodeAttr)

        #add the claimed edge to the scoring graph
        self.scoringGraph.add_edge(source, target)

# this function should be called when a river is claimed by a punter
    def claimRiver(self, punter, source, target):
        #remove the claimed river from the main graph
        self.graph.remove_edge(source, target)

        # if punter is player, claim in scoringgraph and display move
        if punter == self.punter:
            self.claimInScoringGraph(source, target)
            self.displayMove(self.punter, source, target)

        #update the endpoints for future search
        self.updateEndpoints(source, target, punter)

    def updateEndpoints(self, source, target, punter):
        #add /remove endpoints
        stillneighbors = False
        scoringGraphEdges = self.scoringGraph.edges()

        # search in available neighbors of source
        for neighbor in self.graph.neighbors(source):
            # neighbor is eligible if not already a endpoint and not in scoring graph
            if not (source, neighbor) in scoringGraphEdges:
                # then add the neighbor as an endpoint
                if not neighbor in self.scoringGraph.nodes():
                    stillneighbors = True
                    break
        # if there is no eligible neighbor anymore, remove the endpoint
        if not stillneighbors and source in self.endpoints:
            self.endpoints.remove(source)

        stillneighbors = False
        #search in available neighbors of target
        for neighbor in self.graph.neighbors(target):
            # neighbor is eligible if not already a endpoint and not in scoring graph
            if not (target, neighbor) in scoringGraphEdges:
                # then add the target as an endpoint
                if not neighbor in self.scoringGraph.nodes():
                    stillneighbors = True
                    break

        if stillneighbors and not target in self.endpoints and punter == self.punter:
            # if there is no eligible neighbor anymore, remove the endpoint
            self.endpoints.insert(0, target)
        elif not stillneighbors and target in self.endpoints:
            # if eligible neighbor, add the endpoint first because
            # it has a lot of chance to make a high score again
            self.endpoints.remove(target)

    def calculateScore(self):
        score = 0
        #score is calculated for each node
        for (node, attr) in self.scoringGraph.nodes(data=True):
            #add score for each mine which has path to the node; this seems costly
            for mine in self.mines:
                if (nx.has_path(self.scoringGraph, node, mine)):
                    score += attr["pathForMine_"+str(mine)]**2
        return score

#   hold real scores at the end of the game
    def setScores(self, punter, score):
        self.scores[punter] = score

#   this function will display the map and show it; very costly
    def displayMap(self):
        #default title
        plt.title('map ')
        #draw edges
        for (source, target) in self.graph.edges_iter():
            plt.plot([self.graph.node[source]["site"].x, self.graph.node[target]["site"].x],
                     [self.graph.node[source]["site"].y, self.graph.node[target]["site"].y], "b--", linewidth=1)
        #draw sites
        plt.plot([site["site"].x for site in self.graph.node.values()],
                 [site["site"].y for site in self.graph.node.values()], 'k.', label="site")

        #draw mines
        plt.plot([site["site"].x for site in self.graph.node.values() if site["site"].isMine],
                 [site["site"].y for site in self.graph.node.values() if site["site"].isMine], 'ro', label="mine")

        #this displays id of nodes if needed
        #for (node, attr) in self.graph.nodes(data = True):
        #    plt.annotate(node, xy=(attr["site"].x, attr["site"].y))

        plt.show(block=False)

#   this function update a move on display
    def displayMove(self, punter, source, target):
        #proctect if nb of punters is too high
        if (self.punters > 7):
            return
        #calculate color of player
        colors = ["c-", "g-", "y-", "k-", "m-", "b-", "w-"]
        if (punter == self.punter):
            color = "r-"
        else:
            color = colors[punter if punter < self.punters else punter -1]

        #get source and target in the graph
        source = self.scoringGraph.node[source]["site"]
        target = self.scoringGraph.node[target]["site"]

        #plot them
        plt.plot([source.x, target.x], [source.y, target.y], color, linewidth=5)

        #update graphics
        self.fig.canvas.draw()

# this function calculates the best next move to play
    def getNextMove(self):
        move = {"punter": self.client.punter, "source": 0, "target": 0}
        bestScore = 0
        bestMove = None
        scoringNodes = self.scoringGraph.nodes()
        i = 0

        #make a pass on each endpoint in the list, ordered in filo
        for source in self.endpoints:
            for target in self.graph.neighbors(source):
                # for each neighbor of each endpoint to search try the score and take the best
                #fakely claim in scoring graph only
                self.claimInScoringGraph(source, target)

                if not target in scoringNodes:
                    # if target is not in scoringNode, it will add it's score for each mine it will be linked to
                    targetNode = self.scoringGraph.node[target]
                    deltascore = 0
                    #deltascore is the sum of the score for each mine
                    for mine in self.mines:
                        if nx.has_path(self.scoringGraph, target, mine):
                            deltascore += targetNode["pathForMine_"+str(mine)]**2

                    #clean the fake claiming
                    self.scoringGraph.remove_edge(source, target)
                    self.scoringGraph.remove_node(target)
                else:
                    #target is already in the graph, so recalculate all
                    score = self.calculateScore()
                    deltascore = score - self.currentScore
                    #clean fake, but do not remove the endpoint as it was already in graph
                    self.scoringGraph.remove_edge(source, target)

                #record best score for which move
                if bestScore <= deltascore:
                    bestScore = deltascore
                    bestMove = (source, target)

                #break the loop at timeout
                if (self.client.getTimeout() < 0.01):
                    break
            if (self.client.getTimeout() < 0.01):
                break

        #maintain a currentscore
        self.currentScore += bestScore

        #update movesleft as we are returning the next move
        self.leftMoves -= 1

        #display score up to date
        self.displayScore(self.client.title, str(bestScore) + " / " + str(self.currentScore))

        #forge the move with the best move until now
        if bestMove != None:
            move["source"] = bestMove[0]
            move["target"] = bestMove[1]
        else:
            move = None

        #return the move
        return move

    def displayScore(self, mapTitle, score):
        plt.title(mapTitle + score + " (left:" +str(self.leftMoves) +")")

    def close(self):
        plt.close('all')

class Futures(LambdaMap):

    def __init__(self, client, map, punter, punters):
        super(LambdaMap).__init__(client, map, punter, punters)
        average = nx.average_shortest_path_length(self.graph)

        mineStart = self.mines[0]
        currentNode = self.graph.node[mineStart]
        maxiteration = average
        while currentNode["pathForMine_"+str(mineStart)] < average and maxiteration:
            maxiteration -= 1
            for neighbor in self.graph.neighbors(currentNode):
                if neighbor["pathForMine_"+str(mineStart)] > currentNode["pathForMine_"+str(mineStart)]:
                    currentNode = neighbor
                    break
        if (maxiteration == 0):
            printD("maxiteration reached")

        self.bet = (mineStart, currentNode)


    def getNextMove(self):
        if (self.bet == None):
            return super(LambdaMap).getNextMove()
        else:
            target = self.bet[1]
            start = self.bet[0]
            nodeList = nx.shortest_path(self.graph, start, tartget)
            currentStartMove = nodeList[0]
            for node in nodeList:
                if currentStartMove != node and not (currentStartMove, node) in self.scoringGraph.edges():
                    return (currentStartMove, node)


