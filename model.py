import matplotlib.pyplot as plt
import networkx as nx
import sys
import copy

def print_err(str):
    print >> sys.stderr, str


class Site:
    def __init__(self, id, x, y, isMine=False):
        self.id = id
        self.x = x
        self.y = y
        self.isMine = isMine

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

    def __init__(self, parentGraph=None, other=None, should_display=True):
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
    def __eq__(self, other):
        if other == None:
            return False
        if (set(self.node.keys()) == set(other.node.keys())):
            result = nx.difference(self,other)
            return len(result) == 0
        else:
            return False

    def claim(self, source, target):
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
        if self.should_display:
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
    def __init__(self, map, should_display=True):
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

    def display(self):
        if self.should_display:
            plt.title('map ')  # default title
            for (source, target) in self.edges_iter():  # draw edges
                plt.plot([self.node[source]["site"].x, self.node[target]["site"].x],
                         [self.node[source]["site"].y, self.node[target]["site"].y], "b-", linewidth=1)
            plt.plot([site["site"].x for site in self.node.values()],
                     [site["site"].y for site in self.node.values()], 'k.', label="site")  # draw sites
            plt.plot([site["site"].x for site in self.node.values() if site["site"].isMine],
                     [site["site"].y for site in self.node.values() if site["site"].isMine], 'ro',
                     label="mine")  # draw mines
            #for (node, attr) in self.nodes(data = True):          # this displays id of nodes if needed
            #    plt.annotate(node, xy=(attr["site"].x, attr["site"].y))

            plt.show(block=False)  # show non blocking

    def displayScore(self, mapTitle, score, leftMoves):
        if self.should_display:
            plt.title(mapTitle + str(score) + " (left:" + str(leftMoves) + ")")

    def claim(self, source, target):
        self.remove_edge(source, target)  # only remove the edge in the graph as it is not available anymore