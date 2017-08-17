import time
from model import ScoringGraph
import graph_tool.all as gt
from model import print_err

# noinspection PyClassHasNoInit
class DiscoveryGraph(gt.Graph):
    def __init__(self, fullgraph, should_display=True):
        gt.Graph.__init__(self)
        self.fullgraph = fullgraph
        self.add_vertex()  # register a new scoringGraph
        self.head = 0
        self.weight = self.new_edge_property('int32_t')
        self.exploration_pending = self.new_vertex_property('bool')
        self.scoringgraphs = self.new_vertex_property('object')
        self.edge_move = self.new_edge_property('vector<int>')
        self.scoringgraphs[self.head] = ScoringGraph(self.fullgraph,display=should_display)
        K = 0.5  # preferred edge length

        pos = gt.sfdp_layout(self, K=K)  # initial layout positions
        self.win = gt.GraphWindow(self, pos, geometry=(400, 400))

    def explore(self, timeout=None):
        start = time.time()
        nextList = [self.head]
        i = 0

        #for successors in gt.bfs_search(self, self.head):
        #    if successors.explored == False:
        #        nextList.append(successors)

        while len(nextList) > 0 and (timeout == None or(time.time() - start < timeout )):
            currentNode = nextList.pop(0)
            currentScoring = self.scoringgraphs[currentNode]
            if not currentScoring.discovered:
                for source in currentScoring.vfilt.a:
                    for target in self.fullgraph.get_out_neighbours(source):
                        # create a new node by exploring it
                        if not target in currentScoring.vfilt.a:
                            newVertex = self.add_vertex()
                            edge = self.add_edge(currentNode, newVertex)
                            self.edge_move[edge] = (source, target)
                            newGraph = ScoringGraph(self.fullgraph, currentScoring, source, target)
                            self.scoringgraphs[newVertex] = newGraph
                            i+=1
                            self.weight[edge] = self.fullgraph.maxScore - (newGraph.score - currentScoring.score)
                            if newGraph:
                                nextList.append(newVertex)
                currentScoring.discovered = True

        #self.display()
        if len(nextList) != 0:
            print_err("timeout, made " + str(i))
        else:
            print_err("to the end of " + str(i))

    def getBestMove(self, timeout):
        self.explore(timeout)
        dist_map, pred_map = gt.dijkstra_search(self, self.weight, self.vertex(self.head),infinity=self.fullgraph.maxScore*self.fullgraph.num_edges())
        print dist_map.a

        bestMove = None
        bestScore = self.scoringgraphs[self.vertex(self.head)].score
        #if len(bestPathes[bestTarget[0]]) > 1:
        #    bestfirstTarget = bestPathes[bestTarget[0]][1]
        #    bestScore = bestfirstTarget.score
        #    bestMove = self[self.head][bestfirstTarget]['move']
        return (bestMove, bestScore)

    def claim(self, source, target):
        for edge in self.get_out_edges(self.head):
            if target == self.edge_move[edge[2]]:
                self.head = self.vertex(edge[1])
        self.fullgraph.remove_edge(source, target)

    def display(self):

        gt.sfdp_layout(self, K=0.5)
        self.win.graph.fit_to_window(ink=True)
        # The following will force the re-drawing of the graph, and issue a
        # re-drawing of the GTK window.
        self.win.graph.regenerate_surface()
        self.win.graph.queue_draw()
