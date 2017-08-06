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

    def __init__(self, map):
        self.mines = []
        self.riverClaimed = {}

        self.fig = plt.figure(figsize=(10, 30))

        if map == None:
            return

        self.graph = nx.Graph()

        for site in map["sites"]:
            self.graph.add_node(site["id"])
            self.graph.node[site["id"]]["site"] = Site(site["id"], site["x"], site["y"])

        self.graph.add_edges_from([(river["source"],river["target"]) for river in map["rivers"]])

        self.mines = map["mines"]
        for mine in self.mines:
            self.graph.node[mine]["site"].isMine = True

    def claimRiver(self, punter, river):
        if not self.riverClaimed.has_key(punter):
            self.riverClaimed[punter] = []
        self.riverClaimed[punter].append(river)
        self.graph.remove_edge(river.source, river.target)

    def display(self):

        plt.title('map')

        for river in self.graph.edges_iter():
            plt.plot([self.graph.node[river[0]]["site"].x, self.graph.node[river[1]]["site"].x],
                     [self.graph.node[river[0]]["site"].y, self.graph.node[river[1]]["site"].y], "b--", linewidth=1)

        colors = ["r-", "k-", "y-", "m-"]
        for punter in self.riverClaimed:
            for river in self.riverClaimed[punter]:
                source = river.source
                target = river.target
                plt.plot([self.graph.node[source]["site"].x, self.graph.node[target]["site"].x],
                     [self.graph.node[source]["site"].y, self.graph.node[target]["site"].y], colors[punter], linewidth=5)

        plt.plot([site["site"].x for site in self.graph.node.values()],
                 [site["site"].y for site in self.graph.node.values()], 'k.', label="site")

        plt.plot([site["site"].x for site in self.graph.node.values() if site["site"].isMine],
                 [site["site"].y for site in self.graph.node.values() if site["site"].isMine], 'ro', label="mine")

        plt.show(block = False)
        plt.draw()
        self.fig.canvas.draw()