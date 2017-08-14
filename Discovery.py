import matplotlib.pyplot as plt
import networkx as nx
from model import print_err
from model import ScoringGraph
import time

# noinspection PyClassHasNoInit
class DiscoveryGraph(nx.DiGraph):
    def __init__(self, scoringGraph):
        nx.DiGraph.__init__(self)
        self.add_node(scoringGraph, attr_dict={'graph': scoringGraph})  # register a new scoringGraph
        self.head = scoringGraph

    def explore(self, timeout):
        currentNode = self.head
        start = time.time()
        nextList = [self.head]
        i=0
        while len(nextList) > 0 and (time.time() - start < timeout ):
            currentNode = nextList.pop(0)
            for source in currentNode.endpoints:
                for target in currentNode.fullGraph.neighbors(source):
                    # create a new node by exploring it
                    newGraph = self.evolve_from(currentNode, source, target)
                    i+=1
                    if newGraph:
                        nextList.append(newGraph)
        if len(nextList) != 0:
            print_err("timeout, made " + str(i))

    def getBestMove(self):
        (bestScores, bestPathes) = nx.single_source_dijkstra(self, self.head, cutoff=5)
        bestscoreitem = sorted([(key, value) for (key, value) in bestScores.items()], key=lambda x: x[1]/len(bestPathes[x[0]]))
        #bestscoreitem = sorted([(key, value) for (key, value) in bestscoreitem], key=lambda x:x[1])
        bestTarget = bestscoreitem[0]
        bestMove = None
        bestScore = self.head.score
        if len(bestPathes[bestTarget[0]]) > 1:
            bestfirstTarget = bestPathes[bestTarget[0]][1]
            bestScore = bestfirstTarget.score
            bestMove = self[self.head][bestfirstTarget]['move']
        return (bestMove, bestScore)

    def claim(self, source, target):
        self.head.claim(source,target)
        self.clear()
        return
        nodesToRemove = [node for (node, attr) in self.nodes(data=True) if nx.number_of_nodes(attr['graph']) < nx.number_of_nodes(self)]
        self.remove_nodes_from(nodesToRemove)

    def evolve_from(self, scoringGraph, source, target):
        newGraph = ScoringGraph(scoringGraph.fullGraph, scoringGraph)  #copy the source scoringGraph
        newGraph.claim(source, target)  # claim the (source, target) in a new scoring graph
        weight = -(newGraph.score - scoringGraph.score)
        self.add_node(newGraph, attr_dict={'graph':newGraph})  #add the new node
        self.add_path([scoringGraph, newGraph],  weight = weight, move= {"claim": (source, target)})  #add the edge
        return newGraph  # return newGraph

    def display(self, graph = None):
        online = False
        if graph == None:
            online = True
            graph = self
        plt.title('discovery')  # hard code the title
        nx.draw_graphviz(graph)  # expand using spectral layout
        #nx.draw_networkx_edge_labels(graph, pos=nx.spectral_layout(self))  # draw labels
        #nx.draw_networkx_nodes(graph, pos=nx.graphviz_layout(self), nodelist=[self.head], node_color='g')

        if online :
            self.head.fullGraph.fig.canvas.draw()
        plt.show(block=False)  # show non blocking
