import matplotlib.pyplot as plt
import networkx as nx
import time
import sys

def printD(str):
    print >> sys.stderr, str
    pass

class Site:
    def __init__(self, id, x, y, ):
        self.id = id
        self.x = x
        self.y = y
        self.rivers = []
        self.isMine = False

    def addRiver(self, river):
        self.rivers.append(river)


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

    #this function allows to claim a river in scoringGraph only. Used to test paths
    def claimInScoringGraph(self, source, target):

        if not self.scoringGraph.has_node(target):
            nodeAttr = self.graph.node[target]
            self.scoringGraph.add_node(target, attr_dict=nodeAttr)

        if not self.scoringGraph.has_node(source):
            nodeAttr = self.graph.node[source]
            self.scoringGraph.add_node(source, attr_dict=nodeAttr)

        self.scoringGraph.add_edge(source, target)

    def claimRiver(self, punter, source, target):
        self.graph.remove_edge(source, target)
        if punter == self.punter:
            self.claimInScoringGraph(source, target)
            self.displayMove(self.punter, source, target)
        self.updateEndpoints(source, target, punter)

    def updateEndpoints(self, source, target, punter):
        #add /remove endpoints
        stillneighbors = False
        scoringGraphEdges = self.scoringGraph.edges()
        # search in available neighbors of target
        for neighbor in self.graph.neighbors(source):
            # neighbor is eligible if not already a endpoint and not in scoring graph
            if not (source, neighbor) in scoringGraphEdges:
                # then add the neighbor as an endpoint
                if not neighbor in self.scoringGraph.nodes():
                    stillneighbors = True
                    break
        if not stillneighbors and source in self.endpoints:
            # if there is no eligible neighbor anymore, remove the endpoint
            self.endpoints.remove(source)

        stillneighbors = False
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
            self.endpoints.remove(target)

    def calculateScore(self):
        score = 0

        for (node, attr) in self.scoringGraph.nodes_iter(data=True):
            for mine in self.mines:
                if (nx.has_path(self.scoringGraph, node, mine)):
                    score += attr["pathForMine_"+str(mine)]**2

        return score

    def setScores(self, punter, score):
        self.scores[punter] = score

    def displayMap(self):
        plt.title('map ')
        for (source, target) in self.graph.edges_iter():
            plt.plot([self.graph.node[source]["site"].x, self.graph.node[target]["site"].x],
                     [self.graph.node[source]["site"].y, self.graph.node[target]["site"].y], "b--", linewidth=1)
        plt.plot([site["site"].x for site in self.graph.node.values()],
                 [site["site"].y for site in self.graph.node.values()], 'k.', label="site")

        plt.plot([site["site"].x for site in self.graph.node.values() if site["site"].isMine],
                 [site["site"].y for site in self.graph.node.values() if site["site"].isMine], 'ro', label="mine")

        #for (node, attr) in self.graph.nodes(data = True):
        #    plt.annotate(node, xy=(attr["site"].x, attr["site"].y))

        plt.show(block=False)

    def displayMove(self, punter, source, target):
        if (self.punters > 7) and punter != self.punter:
            return
        colors = ["c-", "g-", "y-", "k-", "m-", "b-", "w-"]
        if (punter == self.punter):
            color = "r-"
        else:
            color = colors[punter if punter < self.punters else punter -1]
        source = self.scoringGraph.node[source]["site"]
        target = self.scoringGraph.node[target]["site"]
        plt.plot([source.x, target.x], [source.y, target.y], color, linewidth=5)
        self.fig.canvas.draw()

    def getNextMove(self):
        move = {"punter": self.client.punter, "source": 0, "target": 0}
        bestScore = 0
        bestMove = None

        scoringNodes = self.scoringGraph.nodes()
        i = 0
        for source in self.endpoints:
            for target in self.graph.neighbors(source):
                self.claimInScoringGraph(source, target)

                if not target in scoringNodes:
                    targetNode = self.scoringGraph.node[target]
                    deltascore = 0
                    for mine in self.mines:
                        if nx.has_path(self.scoringGraph, target, mine):
                            deltascore += targetNode["pathForMine_"+str(mine)]**2

                    self.scoringGraph.remove_edge(source, target)
                    self.scoringGraph.remove_node(target)
                else:
                    score = self.calculateScore()
                    deltascore = score - self.currentScore
                    self.scoringGraph.remove_edge(source, target)

                if bestScore <= deltascore:
                    bestScore = deltascore
                    bestMove = (source, target)
                if (self.client.getTimeout() < 0.01):
                    break
            if (self.client.getTimeout() < 0.01):
                break

        self.currentScore += bestScore

        self.leftMoves -= 1
        self.displayScore(self.client.title, str(bestScore) + " / " + str(self.currentScore))

        if bestMove != None:
            move["source"] = bestMove[0]
            move["target"] =     bestMove[1]
        else:
            move = None


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


