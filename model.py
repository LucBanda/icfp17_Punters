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
    def __init__(self, map, punters, punter):
        self.mines = []
        self.punters = punters
        self.punter = punter

        self.fig = plt.figure(figsize=(10, 30))

        if map == None:
            return

        self.graph = nx.Graph()

        for site in map["sites"]:
            self.graph.add_node(site["id"])
            self.graph.node[site["id"]]["site"] = Site(site["id"], site["x"], site["y"])

        self.graph.add_edges_from([(river["source"], river["target"], {"claimed": -1}) for river in map["rivers"]])

        self.mines = map["mines"]
        for mine in self.mines:
            self.graph.node[mine]["site"].isMine = True

        self.scores = {}
        self.availableGraph = self.graph.copy()
        self.scoringGraph = nx.Graph()

        start = time.time()
        for mine in self.mines:
            list = nx.single_source_shortest_path_length(self.graph, mine)
            nx.set_node_attributes(self.graph, "pathForMine_" + str(mine), list)

            self.scoringGraph.add_node(mine, attr_dict=self.graph.node[mine])
            self.scoringGraph.node[mine]["score"] = {}

        self.displayMap()

    def claimInScoringGraph(self, source, target):

        if not self.scoringGraph.has_node(target):
            nodeAttr = self.graph.node[target]
            self.scoringGraph.add_node(target, attr_dict=nodeAttr)

        if not self.scoringGraph.has_node(source):
            nodeAttr = self.graph.node[source]
            self.scoringGraph.add_node(source, attr_dict=nodeAttr)

        self.scoringGraph.add_edge(source, target)

    def claimRiver(self, punter, source, target):
        self.availableGraph.remove_edge(source, target)
        if punter == self.punter:
            self.claimInScoringGraph(source, target)
            self.displayMove(self.punter, source, target)

    def getAvailableGraph(self):
        return self.availableGraph

    def calculateScore(self, claim=None):
        score = 0

        if claim:
            self.claimInScoringGraph(claim[0], claim[1])

        for (node, attr) in self.scoringGraph.nodes_iter(data=True):
            for mine in self.mines:
                if (nx.has_path(self.scoringGraph, node, mine)):
                    score += attr["pathForMine_"+str(mine)]**2

        if claim:
            self.scoringGraph.remove_edge(claim[0], claim[1])

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

    def displayScore(self, mapTitle, score):
        plt.title(mapTitle + str(score))

    def close(self):
        plt.close('all')
