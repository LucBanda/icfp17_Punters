import matplotlib.pyplot as plt
import networkx as nx
import sys
import time

def print_err(str):
    print >> sys.stderr, str
    pass


class Site:
    def __init__(self, id, x, y, ):
        self.id = id
        self.x = x
        self.y = y
        self.isMine = False

# noinspection PyClassHasNoInit
class DiscoveryGraph(nx.DiGraph):
    def __init__(self, scoringGraph):
        nx.DiGraph.__init__(self)
        self.add_node(scoringGraph)  # register a new scoringGraph
        self.head = scoringGraph

    def explore(self, timeout):

        currentNode = self.head
        for source in currentNode.endpoints:
            for target in currentNode.graph.neighbors(source):
                # create a new node by exploring it
                startTime = time.time()
                self.evolve_from(currentNode, source, target)
                print("1 evolution took : " + str(time.time() - startTime))

    def getBestMove(self):
        successors = self.successors(self.head)
        if len(successors) > 0:
            bestTarget = sorted(self.successors(self.head), key=lambda graph: graph.score, reverse=True)[0]
            bestScore = bestTarget.score
            bestMove = self.edge[self.head][bestTarget]["move"]
        else:
            bestMove = None
            bestScore = self.head.score
        return (bestMove, bestScore)

    def claim(self, source, target):
        for targetNode in self.successors(self.head):
            (moveSource, moveTarget) = self[self.head][targetNode]["move"]["claim"]
            if moveSource == source and moveTarget == target:
                self.head = targetNode
                break

    def evolve_from(self, scoringGraph, source, target):
        newGraph = ScoringGraph(scoringGraph.graph, scoringGraph)  #copy the source scoringGraph
        newGraph.claim(source, target)  # claim the (source, target) in a new scoring graph
        if not newGraph in self.nodes():  # if the result is already known
            newGraph.evolve_from(scoringGraph)  # else update the new graph with datas
            self.add_node(newGraph)  #add the new node
        self.add_path([scoringGraph, newGraph],  weight = 0, move= {"claim": (source, target)})  #add the edge


    def display(self, graph = None):
        online = False
        if graph == None:
            online = True
            graph = self
        plt.title('discovery')  # hard code the title
        nx.draw_spectral(graph)  # expand using spectral layout
        #nx.draw_networkx_edge_labels(graph, pos=nx.spectral_layout(self))  # draw labels
        nx.draw_networkx_nodes(graph, pos=nx.spectral_layout(self), nodelist=[self.head], node_color='g')

        if online :
            self.head.graph.fig.canvas.draw()
        plt.show(block=False)  # show non blocking

class ScoringGraph(nx.Graph):
    def __init__(self, parentGraph, other=None):
        if other is None:
            nx.Graph.__init__(self)
            self.explored = False
            self.graph = parentGraph
            self.endpoints = parentGraph.mines  # endpoints are mines at the very beginning
            self.score = 0
            # import mines in scoring graph
            for mine in self.endpoints:  # import mines as nodes of scoring graph
                self.add_node(mine, attr_dict=parentGraph.node[mine])
        else:
            nx.Graph.__init__(self, other)
            self.explored = False
            self.graph = parentGraph
            self.endpoints = other.endpoints

    # make it comparable with __eq__ and __hash__
    def __eq__(self, other):
        return sorted(self.edges()) == sorted(other.edges())

    def __hash__(self):
        return hash(tuple(sorted(self.edges())))

    def claim(self, source, target):
        self.pending_source = source
        self.pending_target = target
        for nodeToClaim in [source, target]:  # loop over each node
            if not self.has_node(nodeToClaim):  # if node is not is graph
                nodeAttr = self.graph.node[nodeToClaim]  # getAttributes in nodeSource
                self.add_node(nodeToClaim, attr_dict=nodeAttr)  # add the node
        self.add_edge(source, target)  # add the claimed edge to the scoring graph

    # noinspection PyAttributeOutsideInit
    def calculate_score(self):
        score = 0
        for (node, attr) in self.nodes(data=True):  # score is calculated for each node
            for mine in self.graph.mines:  # loop over mines
                if nx.has_path(self, node, mine):  # if mine has path to the node; this seems costly
                    score += attr["pathForMine_" + str(mine)] ** 2  # add the score
        return  score  # return the score

    def evolve_from(self, sourceGraph):
        self.graph = sourceGraph.graph
        self.explored = False
        if self.pending_target not in sourceGraph.nodes():
            # if target is not in scoringNode, it will add it's score for each mine it will be linked to
            targetNode = self.node[self.pending_target]
            deltascore = 0
            # deltascore is the sum of the score for each mine
            for mine in self.graph.mines:
                if nx.has_path(self, self.pending_target, mine):
                    deltascore += targetNode["pathForMine_" + str(mine)] ** 2
            self.score = sourceGraph.score + deltascore
        else:
            # target is already in the graph, difficult to do the delta so recalculate all
            self.score = self.calculate_score()

        self.evolve_endpoints_from(sourceGraph, self.pending_target, self.pending_source)

        self.pending_target = None
        self.pending_source = None

    def evolve_endpoints_from(self, sourceGraph, source, target):
        # add /remove endpoints
        stillneighbors = False
        scoringGraphEdges = sourceGraph.edges()
        retEndpoints = sourceGraph.endpoints[:]

        # search in available neighbors of source
        for neighbor in self.graph.neighbors(source):
            # neighbor is eligible if not already a endpoint and not in scoring graph
            if not (source, neighbor) in scoringGraphEdges:
                # then add the neighbor as an endpoint
                if neighbor not in sourceGraph.nodes():
                    stillneighbors = True
                    break
        # if there is no eligible neighbor anymore, remove the endpoint
        if not stillneighbors and source in retEndpoints:
            retEndpoints.remove(source)
        elif stillneighbors and source not in retEndpoints:
            # if there is no eligible neighbor anymore, remove the endpoint
            retEndpoints.insert(0, source)

        stillneighbors = False
        # search in available neighbors of target
        for neighbor in self.graph.neighbors(target):
            # neighbor is eligible if not already a endpoint and not in scoring graph
            if (target, neighbor) not in scoringGraphEdges:
                # then add the target as an endpoint
                if neighbor not in self.nodes():
                    stillneighbors = True
                    break

        if stillneighbors and target not in retEndpoints:
            # if there is no eligible neighbor anymore, remove the endpoint
            retEndpoints.insert(0, target)
        elif not stillneighbors and target in retEndpoints:
            # if eligible neighbor, add the endpoint first because
            # it has a lot of chance to make a high score again
            retEndpoints.remove(target)

        self.endpoints = retEndpoints

    def displayMove(self, source, target):
        sourceSite = self.node[source]["site"]  # get source and target in the graph
        targetSite = self.node[target]["site"]
        plt.plot([sourceSite.x, targetSite.x], [sourceSite.y, targetSite.y], 'r-', linewidth=3)  # plot them
        self.graph.fig.canvas.draw()  # update figure

class FullGraph(nx.Graph):
    # this is the main graph, containing all sites and rivers
    # edges taken by opponents are removed
    def __init__(self, map):
        nx.Graph.__init__(self)
        for site in map["sites"]:  # populate sites in main graph
            self.add_node(site["id"])
            self.node[site["id"]]["site"] = Site(site["id"], site["x"], site["y"])
        self.add_edges_from(
            [(river["source"], river["target"]) for river in map["rivers"]])  # populate edges in main graph
        self.mines = map["mines"]  # get mines in self.mines
        for mine in self.mines:  # add mines to main graph
            self.node[mine]["site"].isMine = True

        for mine in self.mines:  # precalculate score for all site and all mines as it is static
            list = nx.single_source_shortest_path_length(self, mine)  # get the path to the mine indexed by node
            nx.set_node_attributes(self, "pathForMine_" + str(mine), list)  # set the attributes

        self.fig = plt.figure(figsize=(10, 30))  # initialize graphics

    def display(self):
        plt.title('map ')  # default title
        for (source, target) in self.edges_iter():  # draw edges
            plt.plot([self.node[source]["site"].x, self.node[target]["site"].x],
                     [self.node[source]["site"].y, self.node[target]["site"].y], "b-", linewidth=1)
        plt.plot([site["site"].x for site in self.node.values()],
                 [site["site"].y for site in self.node.values()], 'k.', label="site")  # draw sites
        plt.plot([site["site"].x for site in self.node.values() if site["site"].isMine],
                 [site["site"].y for site in self.node.values() if site["site"].isMine], 'ro',
                 label="mine")  # draw mines
        # for (node, attr) in self.graph.nodes(data = True):          # this displays id of nodes if needed
        #    plt.annotate(node, xy=(attr["site"].x, attr["site"].y))

        plt.show(block=False)  # show non blocking

    def claim(self, source, target):
        self.remove_edge(source, target)  # only remove the edge in the graph as it is not available anymore


class LambdaMap:
    def __init__(self, client, map, punters, punter):
        # initialize variables
        self.mines = []
        self.punters = punters
        self.punter = punter
        self.client = client
        self.scores = {}
        fullgraph = FullGraph(map)
        scoringGraph = ScoringGraph(fullgraph)
        self.discoveryGraph = DiscoveryGraph(scoringGraph)
        self.leftMoves = nx.number_of_edges(fullgraph) / self.punters  # initialize number of turns
        self.discoveryGraph.head.graph.display()  # display map

    # this function should be called when a river is claimed by a punter
    def claimRiver(self, punter, source, target):
        timeStart = time.time()
        self.discoveryGraph.head.graph.claim(source, target)  # remove the claimed river from the main graph
        if punter == self.punter:  # if punter is player, evolve the scoringgraph
            self.discoveryGraph.claim(source, target)
            self.discoveryGraph.head.displayMove(source, target)
        print_err("claiming time = " + str(time.time() - timeStart))
    #   hold real scores at the end of the game
    def setScores(self, punter, score):
        self.scores[punter] = score

    # this function calculates the best next move to play
    def getNextMove(self):
        self.discoveryGraph.explore(self.client.timeout / 2)  # explore discoveryGraph
        timeStart = time.time()
        (bestMove, bestScore) = self.discoveryGraph.getBestMove()  # get the best move found
        print_err("getBestMoveTime = " + str(time.time() - timeStart))
        self.leftMoves -= 1  # update movesleft as we are returning the next move
        self.displayScore(self.client.title, bestScore)  # display score up to date
        if bestMove:
            bestMove = bestMove.copy()
            bestMove["claim"] =  {"punter": self.client.punter, "source": bestMove["claim"][0], "target": bestMove["claim"][1]}  # set the move
        else:
            bestMove = {"pass":{"punter":self.client.punter}}
        print bestMove
        return bestMove   # return the move

    def displayScore(self, mapTitle, score):
        plt.title(mapTitle + str(score) + " (left:" + str(self.leftMoves) + ")")

    # noinspection PyMethodMayBeStatic
    def close(self):
        plt.close('all')