import matplotlib.pyplot as plt
import networkx as nx
import sys
import copy
import random
import numpy as np

def print_err(string :str):
    print(string, file = sys.stderr)


class Site:
    def __init__(self, id :int, x :float, y :float, isMine :bool=False):
        self.id = id
        self.x = x
        self.y = y
        self.isMine = isMine

class Path:
    def __init__(self, mine :int):
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

    def __init__(self, parentGraph :'FullGraph' =None, other :'ScoringGraph'=None, should_display :bool=True):
        self.should_display = should_display
        if other is None:
            nx.Graph.__init__(self)
            self.explored = False
            self.fullGraph = parentGraph
            self.score = 0
            self.pathes = {}
            if parentGraph != None:
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
            self.should_display = other.should_display

    # make it comparable with __eq__ and __hash__
    def __eq__(self, other:'ScoringGraph'):
        if other == None:
            return False
        if (set(self.node.keys()) == set(other.node.keys())):
            result = nx.difference(self,other)
            return len(result) == 0
        else:
            return False

    def __hash__(self):
        return nx.DiGraph.__hash__(self)

    def claim(self, source :int, target :int):
        assert source in self.nodes() #make sure source is in graph

        if not self.has_node(target):  # if target is not in graph
            nodeAttr = self.fullGraph.node[target]  # getAttributes in node
            self.add_node(target, attr_dict=nodeAttr.copy())  # add the node
            nodesource = self.node[source]  # append target to the same path as source
            nodeTarget = self.node[target]  # get nodeSource and nodeTarget
            path = self.pathes[nodesource["path"].mines[0]]  # get the current path it belongs to
            path.nodes.append(target)  # append the target to the current path
            for mine in path.mines:  # calculate associated score for each mine of the path
                score = nodeTarget["pathForMine_"+str(mine)]**2
                path.score += score  # increase the path score
                self.score += score  # and the graph score
            self.node[target]["path"] = path  # store the path in the node
            self.node[target]["path"] = path  # store the path in the node
        else:  #if target is already in graph
            assert target in self.nodes()  # make sure of it
            nodeSource = self.node[source]  # append target to the same path as source
            nodeTarget = self.node[target]  # get nodeSource and nodeTarget
            sourcePath = self.pathes[nodeSource["path"].mines[0]]# target path is a bit odd to be up to date,
            targetPath = self.pathes[nodeTarget["path"].mines[0]] # it needs to refer to the current path of it's first mine path
            if sourcePath != targetPath:  # if source and target does not share the same path
                #add one path to the other
                self.score = self.score - targetPath.score - sourcePath.score
                newPath = sourcePath + targetPath
                for nodeId in newPath.nodes:  # update score for new path
                    for mine in newPath.mines:
                        score = self.node[nodeId]["pathForMine_" + str(mine)]**2
                        newPath.score += score
                        self.score += score
                    self.node[nodeId]['path'] = newPath

                for mine in newPath.mines:
                    self.pathes[mine] = newPath
            else:
                return False

        self.update_endpoints(source)
        self.update_endpoints(target)
        return True

    def update_endpoints(self, source :int):
        stillneighbors = False
        for neighbor in self.fullGraph.neighbors(source):
            if neighbor not in self.pathes[self.node[source]['path'].mines[0]].nodes:
                stillneighbors = True
                break
        if not stillneighbors and source in self.endpoints:
            self.endpoints.remove(source)
        elif stillneighbors and source not in self.endpoints:
            self.endpoints.insert(0,source)

    def displayMove(self, source :int, target :int):
        if self.should_display:
            sourceSite = self.node[source]["site"]  # get source and target in the graph
            targetSite = self.node[target]["site"]
            plt.plot([sourceSite.x, targetSite.x], [sourceSite.y, targetSite.y], 'r-', linewidth=3)  # plot them
            self.fullGraph.fig.canvas.draw()  # update figure

    def display(self):
        for source in self.edges_iter():
            self.displayMove(source[0], source[1])

class PunterGameState():
    """ A state of the game, i.e. the game board. These are the only functions which are
        absolutely necessary to implement UCT in any 2-player complete information deterministic 
        zero-sum game, although they can be enhanced and made quicker, for example by using a 
        GetRandomMove() function to generate a random move during rollout.
        By convention the players are numbered 1 and 2.
    """
    def __init__(self, fullGraph = None):
        self.fullGraph = fullGraph
        self.playerJustMoved = 2 # At the root pretend the player just moved is player 2 - player 1 has the first move
        self.score = 0 # score is invalid
        self.pathes = {}
        self.scores = {}
        self.endpoints = []
        if fullGraph:
            for mine in self.fullGraph.mines:
                self.pathes[mine] = Path(mine)  # import mines in pathes as id
                self.scores[mine] = 0

    def Clone(self):
        """ Create a deep clone of this game state.
        """
        st = PunterGameState()
        st.fullGraph = self.fullGraph
        st.score = self.score
        st.playerJustMoved = self.playerJustMoved
        st.pathes = copy.deepcopy(self.pathes)
        st.scores = copy.deepcopy(self.scores)
        st.endpoints = self.endpoints[:]
        return st

    def DoMove(self, move):
        """ Update a state by carrying out the given move.
            Must update playerJustMoved.
        """
        source = move[0]
        target = move[1]
        if target not in self.scores:  # if target is not in graph
            path = self.pathes[source]
            path.nodes.append(target)  # append the target to the current path
            self.endpoints.insert(0, target)
            for mine in path.mines:  # calculate associated score for each mine of the path
                score = self.fullGraph.node[target]["pathForMine_"+str(mine)]**2
                self.scores[target] = score
                path.score += score  # increase the path score
                self.score += score  # and the graph score
            self.pathes[target] = path
        else:  #if target is already in graph
            sourcePath = self.pathes[source]  # target path is a bit odd to be up to date,
            targetPath = self.pathes[target]  # it needs to refer to the current path of it's first mine path
            if sourcePath != targetPath:  # if source and target does not share the same path
                # add one path to the other
                self.score = self.score - targetPath.score - sourcePath.score
                newPath = sourcePath + targetPath
                for nodeId in newPath.nodes:  # update score for new path
                    self.scores[nodeId] = 0
                    for mine in newPath.mines:
                        score = self.fullGraph.node[nodeId]["pathForMine_" + str(mine)] ** 2
                        self.scores[nodeId] += score
                        newPath.score += score
                        self.score += score
                for nodeId in newPath.nodes:  # update score for new path
                    self.pathes[nodeId] = newPath

    def GetMoves(self):
        """ Get all possible moves from this state.
        """
        return [(source, target) for source in self.scores.keys() for target in self.fullGraph.neighbors_iter(source) if target not in self.pathes[source].nodes]

    def GetRandomMove(self):
        move = None
        trials = 10
        if self.endpoints:
            while trials:
                p = min(np.random.poisson(1), len(self.endpoints)-1)
                source = self.endpoints[p]
                targets = self.fullGraph.neighbors(source)
                while targets:
                    target = random.choice(targets)
                    if target not in self.pathes[source].nodes:
                        move = (source, target)
                        break
                    else:
                        targets.remove(target)
                trials -= 1
        return move

    def GetResult(self, playerjm):
        """ Get the game result from the viewpoint of playerjm.
        """
        return self.score

    def __repr__(self):
        """ Don't need this - but good style.
        """
        return self.scores()

    def displayMove(self, move, color='r-'):
        self.fullGraph.displayMove(move[0],move[1], color)

    def display(self, color='b-'):
        #for node in self.scores.keys():
        pass

    def clearDisplay(self):
        self.fullGraph.display(reset=True)

class FullGraph(nx.Graph):
    # this is the main graph, containing all sites and rivers
    # edges taken by opponents are removed
    # node is:
    # key : 'site.id'
    # 'site'
    # "pathForMine_%d"
    def __init__(self, map :dict, should_display :bool =True):
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
        self.should_display = should_display
        if self.should_display:
            self.fig = plt.figure(figsize=(10, 30))  # initialize graphics

    def display(self, color='b-', reset=False):
        if reset:
            plt.clf()
        if self.should_display:
            plt.title('map ')  # default title
            for (source, target) in self.edges_iter():  # draw edges
                plt.plot([self.node[source]["site"].x, self.node[target]["site"].x],
                         [self.node[source]["site"].y, self.node[target]["site"].y], color, linewidth=1)
            plt.plot([site["site"].x for site in self.node.values()],
                     [site["site"].y for site in self.node.values()], 'k.', label="site")  # draw sites
            plt.plot([site["site"].x for site in self.node.values() if site["site"].isMine],
                     [site["site"].y for site in self.node.values() if site["site"].isMine], 'ro',
                     label="mine")  # draw mines
            #for (node, attr) in self.nodes(data = True):          # this displays id of nodes if needed
            #    plt.annotate(node, xy=(attr["site"].x, attr["site"].y))

            plt.show(block=False)  # show non blocking

    def displayScore(self, mapTitle :str, score :int, leftMoves :int):
        if self.should_display:
            plt.title(mapTitle + str(score) + " (left:" + str(leftMoves) + ")")

    def claim(self, source :int, target :int):
        self.remove_edge(source, target)  # only remove the edge in the graph as it is not available anymore

    def displayMove(self, source: int, target: int, color='b-'):
        if self.should_display:
            sourceSite = self.node[source]["site"]  # get source and target in the graph
            targetSite = self.node[target]["site"]
            plt.plot([sourceSite.x, targetSite.x], [sourceSite.y, targetSite.y], color, linewidth=4)  # plot them
            self.fig.canvas.draw()  # update figure
