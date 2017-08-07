import matplotlib.pyplot as plt
import networkx as nx

class Site:
    def __init__(self, id, x, y,):
        self.id = id
        self.x=x
        self.y=y
        self.rivers=[]
        self.isMine = False

    def addRiver(self, river):
        self.rivers.append(river)

class River:
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def otherSide(self, source):
        if source == self.source:
            return self.target
        else:
            return self.source

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (self.source == other.source and self.target == other.target) or\
                   (self.source == other.target and self.target == other.source)
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

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

        self.graph.add_edges_from([(river["source"],river["target"],{"claimed":-1}) for river in map["rivers"]])

        self.mines = map["mines"]
        for mine in self.mines:
            self.graph.node[mine]["site"].isMine = True

        self.scores = {}
        self.availableGraph = self.graph.copy()
        self.scoringGraph = nx.Graph()
        for mine in self.mines:
            self.scoringGraph.add_node(mine, attr_dict=self.graph.node[mine])
            self.scoringGraph.node[mine]["score"] = {}
            for otherMine in self.mines:
                self.scoringGraph.node[mine]["score"][otherMine] = nx.shortest_path_length(self.graph, otherMine, mine)**2

        self.displayMap()

    def claimInScoringGraph(self, source, target):
        nodes = self.scoringGraph.nodes()
        if not (target in nodes):
            self.scoringGraph.add_node(target, attr_dict = self.graph.node[target])
            self.scoringGraph.node[target]["score"] = {}
            for othermine in self.mines:
                self.scoringGraph.node[target]["score"][othermine] = nx.shortest_path_length(self.graph, othermine, target)**2
        if not (source in nodes):
            self.scoringGraph.add_node(source, attr_dict = self.graph.node[source])
            self.scoringGraph.node[source]["score"] = {}
            for othermine in self.mines:
                self.scoringGraph.node[source]["score"][othermine] = nx.shortest_path_length(self.graph, othermine, source)**2
        self.scoringGraph.add_edge(source, target)

    def claimRiver(self, punter, source, target):
        self.graph.edge[source][target]["claimed"] = punter
        if (punter != self.punter):
            self.availableGraph.remove_edge(source, target)
        else:
            self.availableGraph.edge[source][target]["claimed"] = punter
            self.claimInScoringGraph(source, target)

    def getAvailableGraph(self):
        return self.availableGraph

    def calculateScore(self, claim = None):
        score = 0

        if claim:
            self.claimInScoringGraph(claim[0], claim[1])

        for (node, attr) in self.scoringGraph.nodes_iter(data=True):
            for mine in self.mines:
                if (nx.has_path(self.scoringGraph, node, mine)):
                    score += attr["score"][mine]

        if claim:
            self.scoringGraph.remove_edge(claim[0], claim[1])

        return score

    def setScores(self, punter, score):
        self.scores[punter] = score

    def displayMap(self):
        plt.title('map ')
        for river in self.graph.edges_iter():
            plt.plot([self.graph.node[river[0]]["site"].x, self.graph.node[river[1]]["site"].x],
                     [self.graph.node[river[0]]["site"].y, self.graph.node[river[1]]["site"].y], "b--", linewidth=1)
        plt.plot([site["site"].x for site in self.graph.node.values()],
                 [site["site"].y for site in self.graph.node.values()], 'k.', label="site")

        plt.plot([site["site"].x for site in self.graph.node.values() if site["site"].isMine],
                 [site["site"].y for site in self.graph.node.values() if site["site"].isMine], 'ro', label="mine")


    def displayMove(self, punter, source, target):
        if (self.punters > 7) and punter != self.punter:
            return
        colors = ["c-", "g-", "y-", "k-", "m-","b-", "w-"]
        if (punter == self.punter):
            color = "r-"
        else:
            color = colors[punter if punter < self.punters else punter -1]
        plt.plot([self.graph.node[source]["site"].x, self.graph.node[target]["site"].x],
                    [self.graph.node[source]["site"].y, self.graph.node[target]["site"].y], color, linewidth=5)
        plt.show(block = False)
        plt.draw()
        self.fig.canvas.draw()

    def displayScore(self, score):
        plt.title('map ' + str(score))

