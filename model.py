import matplotlib.pyplot as plt
import networkx as nx
import sys
import time
import copy

def print_err(str):
    print >> sys.stderr, str
    pass


class Site:
    def __init__(self, id, x, y, isMine=False):
        self.id = id
        self.x = x
        self.y = y
        self.isMine = isMine

# noinspection PyClassHasNoInit
class DiscoveryGraph(nx.DiGraph):
    def __init__(self, scoringGraph):
        nx.DiGraph.__init__(self)
        self.add_node(scoringGraph, attr_dict={'graph': scoringGraph})  # register a new scoringGraph
        self.head = scoringGraph

    def explore(self, timeout):
        currentNode = self.head
        for source in currentNode.endpoints:
            for target in currentNode.fullGraph.neighbors(source):
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
        self.clear()
        self.add_node(self.head, attr_dict={'graph':self.head})

    def evolve_from(self, scoringGraph, source, target):
        newGraph = ScoringGraph(scoringGraph.fullGraph, scoringGraph)  #copy the source scoringGraph
        newGraph.claim(source, target)  # claim the (source, target) in a new scoring graph
        if not newGraph in self.nodes():  # if the result is already known
            self.add_node(newGraph, attr_dict={'graph':newGraph})  #add the new node
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
            self.head.fullGraph.fig.canvas.draw()
        plt.show(block=False)  # show non blocking

class Path:
    def __init__(self, mine):
        self.mines=[mine]
        self.nodes=[mine]
        self.score=0

    def __add__(self, other):
        third = Path(None)
        third.mines = self.mines + list(set(other.mines) - set(self.mines))  # append 2 lists with no duplicates
        third.nodes = self.nodes + list(set(other.nodes) - set(self.nodes))
        return third

    def __deepcopy__(self, memodict={}):
        ret = Path(None)
        ret.score = self.score
        ret.mines = self.mines[:]
        ret.nodes = self.nodes[:]
        return ret

class ScoringGraph(nx.Graph):
    # node is:
    # key : 'site.id'
    # 'site'
    # 'path'
    # "pathForMine_%d"

    def __init__(self, parentGraph, other=None):
        if other is None:
            nx.Graph.__init__(self)
            self.explored = False
            self.fullGraph = parentGraph
            self.score = 0
            self.pathes = {}
            for mine in self.fullGraph.mines:
                self.pathes[mine] = Path(mine)  # import mines in pathes as id
                dict = parentGraph.node[mine].copy()
                dict['path'] = self.pathes[mine]
                self.add_node(mine, attr_dict=dict)  # import mines as nodes of scoring graph
            self.endpoints = self.fullGraph.mines
        else:
            nx.Graph.__init__(self, other)
            self.explored = False
            self.fullGraph = parentGraph
            self.score = other.score
            self.pathes = copy.deepcopy(other.pathes)
            self.endpoints = other.endpoints[:]

    # make it comparable with __eq__ and __hash__
    def __eq__(self, other):
        return sorted(self.edges()) == sorted(other.edges())

    def __hash__(self):
        return hash(tuple(sorted(self.edges())))

    def claim(self, source, target):
        assert source in self.nodes() #make sure source is in graph

        if not self.has_node(target):  # if target is not in graph
            nodeAttr = self.fullGraph.node[target]  # getAttributes in node
            self.add_node(target, attr_dict=nodeAttr.copy())  # add the node
            self.add_edge(source, target)  # add the claimed edge to the scoring graph
            nodesource = self.node[source]  # append target to the same path as source
            nodeTarget = self.node[target]  # get nodeSource and nodeTarget
            path = self.pathes[nodesource["path"].mines[0]]  # get the current path it belongs to
            path.nodes.append(target)  # append the target to the current path
            for mine in path.mines:  # calculate associated score for each mine of the path
                score = nodeTarget["pathForMine_"+str(mine)]**2
                path.score += score  # increase the path score
                self.score += score  # and the graph score
            self.node[target]["path"] = path  # store the path in the node
        else:  #if target is already in graph
            assert target in self.nodes()  # make sure of it
            self.add_edge(source, target)  # add the claimed edge to the scoring graph
            nodeSource = self.node[source]  # append target to the same path as source
            nodeTarget = self.node[target]  # get nodeSource and nodeTarget
            sourcePath = self.pathes[nodeSource["path"].mines[0]]# target path is a bit odd to be up to date,
            targetPath = self.pathes[nodeTarget["path"].mines[0]] # it needs to refer to the current path of it's first mine path
            if (target in self.fullGraph.mines):
                pass
            if sourcePath != targetPath:  # if source and target does not share the same path
                #add one path to the other
                self.score = self.score - targetPath.score - sourcePath.score
                newPath = sourcePath + targetPath
                for nodeId in newPath.nodes:  # update score for new path
                    for mine in newPath.mines:
                        if nodeId not in self.nodes():
                            pass
                        score = self.node[nodeId]["pathForMine_" + str(mine)]**2
                        newPath.score += score
                        self.score += score

                for mine in newPath.mines:
                    self.pathes[mine] = newPath

        self.update_endpoints(source)
        self.update_endpoints(target)

    def update_endpoints(self, source):
        stillneighbors = False
        for neighbor in self.fullGraph.neighbors(source):
            if neighbor not in self.pathes[self.node[source]['path'].mines[0]].nodes:
                stillneighbors = True
                break
        if not stillneighbors and source in self.endpoints:
            self.endpoints.remove(source)
        elif stillneighbors and source not in self.endpoints:
            self.endpoints.insert(0,source)

    def displayMove(self, source, target):
        sourceSite = self.node[source]["site"]  # get source and target in the graph
        targetSite = self.node[target]["site"]
        plt.plot([sourceSite.x, targetSite.x], [sourceSite.y, targetSite.y], 'r-', linewidth=3)  # plot them
        self.fullGraph.fig.canvas.draw()  # update figure

class FullGraph(nx.Graph):
    # this is the main graph, containing all sites and rivers
    # edges taken by opponents are removed
    # node is:
    # key : 'site.id'
    # 'site'
    # "pathForMine_%d"
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


class LambdaPunter:
    def __init__(self, client):
        # initialize variables
        self.mines = []
        self.punters = None
        self.punter = None
        self.client = client
        self.scores = {}
        client.set_strategycb(lambda line: self.eventIncoming(line))
        self.leftMoves = 0

    def applyMove(self, moves):
        for move in moves:
            if "claim" in move.keys():
                # claim rivers for each claim received
                self.claimRiver(move["claim"]["punter"], move["claim"]["source"], move["claim"]["target"])

    def eventIncoming(self, event):
        # starts the timeout
        self.client.timeStart = time.time()
        for key, value in event.iteritems():
            if key == u'map':
                self.setup_map(value)
            if key == u'move':
                # when received a move, apply it
                self.applyMove(value["moves"])
                # ask the next move to the model
                move = self.getNextMove()
                # check if move was found
                if move:
                    self.client.write(move)
                else:
                    print_err("did not find any move, passing")
                    self.client.write({"pass": {"punter": self.client.punter}})
                print_err("playing at :" + str(self.client.getTimeout()))
            if key == u'stop':
                # when received a stop, register the scores
                for punterScore in value["scores"]:
                    self.scores[punterScore["punter"]] = punterScore["score"]
                    print_err(str(self.scores))
                print_err("my Score : " + str(self.scores[self.client.punter]))
                return True
        return False

    def displayScore(self, mapTitle, score):
        plt.title(mapTitle + str(score) + " (left:" + str(self.leftMoves) + ")")

    def setScores(self, punter, score):
        self.scores[punter] = score

    # noinspection PyMethodMayBeStatic
    def close(self):
        plt.close('all')

    def claimRiver(self, punter, source, target):
        assert False

    def getNextMove(self):
        assert False

    def setup_map(self, map):
        assert False

class DiscoveryStrategy(LambdaPunter):
    def setup_map(self, map):
        fullgraph = FullGraph(map)
        scoringGraph = ScoringGraph(fullgraph)
        self.discoveryGraph = DiscoveryGraph(scoringGraph)
        self.leftMoves = nx.number_of_edges(fullgraph) / self.client.punters  # initialize number of turns
        self.discoveryGraph.head.fullGraph.display()  # display map
        self.punter = self.client.punter
        self.punters = self.client.punters

    # this function should be called when a river is claimed by a punter
    def claimRiver(self, punter, source, target):
        timeStart = time.time()
        if punter == self.punter:  # if punter is player, evolve the scoringgraph
            self.discoveryGraph.claim(source, target)
            #self.discoveryGraph.head.displayMove(source, target)
        self.discoveryGraph.head.fullGraph.claim(source, target)  # remove the claimed river from the main graph
        print_err("claiming time = " + str(time.time() - timeStart))

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
