import matplotlib.pyplot as plt
import networkx as nx
from model import print_err
from model import ScoringGraph
import time

# noinspection PyClassHasNoInit
class DiscoveryGraph(nx.DiGraph):
    def __init__(self, scoringGraph):
        nx.DiGraph.__init__(self)
        self.add_node(scoringGraph)  # register a new scoringGraph
        self.head = scoringGraph

    def explore(self, timeout):
        start = time.time()
        nextList = [self.head]
        i = 0

        for successors in nx.bfs_successors(self, self.head):
            if successors.explored == False:
                nextList.append(successors)

        while len(nextList) > 0 and (time.time() - start < timeout ):
            currentNode = nextList.pop(0)
            for source in currentNode.endpoints:
                for target in currentNode.fullGraph.neighbors(source):
                    # create a new node by exploring it
                    newGraph = self.evolve_from(currentNode, source, target)
                    i+=1
                    if newGraph:
                        nextList.append(newGraph)   
            currentNode.explored = True

        if len(nextList) != 0:
            print_err("timeout, made " + str(i))
        else:
            print_err("to the end of " + str(i))

    def getBestMove(self):
        (bestScores, bestPathes) = nx.single_source_dijkstra(self, self.head, cutoff=10)
        maxLen = 0
        for bestPath in bestPathes.values():
            if maxLen < len(bestPath): maxLen = len(bestPath)
        print_err("max path len = " + str(maxLen))

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
        for s,t,attr in self.out_edges(self.head, data=True):
            if attr['move']['claim'][0] == source and attr['move']['claim'][1] == target:
                self.head = t
                break

        #clean graph
        edges_to_remove = []
        for (s, t, data) in self.edges_iter(data=True):
            if (data['move']['claim'][0]) in [source, target] and (data['move']['claim'][1]) in [source, target]:
                edges_to_remove.append((s, t))
        self.remove_edges_from(edges_to_remove)

        edges_to_remove = []
        nodes_to_remove = []
        for node in self.nodes_iter():
            if len(node.nodes()) < len(self.head.nodes()):
                for distant in self.out_edges_iter(node):
                    edges_to_remove.append((distant, node))
                nodes_to_remove.append(node)
        self.remove_edges_from(edges_to_remove)
        self.remove_nodes_from(nodes_to_remove)

    def evolve_from(self, scoringGraph, source, target):
        for s,t,attr in self.out_edges_iter(scoringGraph, data=True):
            if attr['move']['claim'][0] == source and attr['move']['claim'][1] == target:
                return t
        newGraph = ScoringGraph(scoringGraph.fullGraph, scoringGraph)  #copy the source scoringGraph
        meaningGraph = newGraph.claim(source, target)  # claim the (source, target) in a new scoring graph
        weight = -(newGraph.score - scoringGraph.score)
        meaningGraph = meaningGraph and weight != 0
        if meaningGraph:
            self.add_node(newGraph)  #add the new node
            self.add_path([scoringGraph, newGraph],  weight = weight, move= {"claim": (source, target)})  #add the edge
            return newGraph  # return newGraph
        else:
            return None

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
