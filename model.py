import sys
import graph_tool.all as gt

def print_err(str):
    print >> sys.stderr, str

class ScoringGraph(gt.GraphView):
    def __init__(self, fullgraph, sourcescoring=None, source=None, target=None, display=True):
        self.fullgraph = fullgraph
        self.shoulddisplay = display
        self.discovered = False

        if sourcescoring:
            self.shoulddisplay = sourcescoring.shoulddisplay
            self.path = sourcescoring.path.copy()
            self.path[self.fullgraph.edge(source, target)] = True
            self.vfilt = sourcescoring.vfilt.copy()
            self.vfilt[target] = True
            gt.GraphView.__init__(self, fullgraph, vfilt=self.vfilt, efilt=self.path)
            self.currentMineConnected = sourcescoring.currentMineConnected.copy()
            self.update(sourcescoring, source, target)
            self.score = self.get_score(sourcescoring, source, target)
        else:
            self.shoulddisplay = display
            self.vfilt = self.fullgraph.new_vertex_property('bool')
            self.vfilt.a = [site in self.fullgraph.mines for site in self.fullgraph.vertices()]
            self.path = self.fullgraph.new_edge_property('bool')
            gt.GraphView.__init__(self, fullgraph, vfilt=self.fullgraph.vertex_is_mine)
            self.currentMineConnected = self.fullgraph.new_vertex_property('object')
            for mine in self.fullgraph.vertices():
                self.currentMineConnected[mine] = {mine: True}

            self.score = 0


    def update(self, sourcescoring, source, target):
        if target in sourcescoring.vertices():
            diffMines = [mine for mine in self.currentMineConnected[target].keys() if self.currentMineConnected[source][mine] != self.currentMineConnected[target][mine]]
            if len(diffMines) == 0:
                self.currentMineConnected[target] =  self.currentMineConnected[source]
            else:
                newDict = {}
                for key, val in self.currentMineConnected[target].keys() + self.currentMineConnected[source].keys():
                    newDict[key] = val
                for site in self.vertices():
                    self.currentMineConnected[site] = newDict
        else:
            self.currentMineConnected[target] = self.currentMineConnected[source]



    def get_score(self, sourcescoring, source, target):
        score = 0
        if target in sourcescoring.vertices():
            for site in self.vertices():
                for mine in self.fullgraph.mines:
                    if self.currentMineConnected[site].has_key(mine):
                        score += self.fullgraph.vertex_path_for_mine[mine][site] ** 2
        else:
            for mine in self.fullgraph.mines:
                    if self.currentMineConnected[target].has_key(mine):
                        score = sourcescoring.score + self.fullgraph.vertex_path_for_mine[mine][target] ** 2

        return score

    def display(self):
        if self.shoulddisplay:
            gt.graphviz_draw(self, pos=self.fullgraph.vertex_pos, ecolor="#FF0000", pin=True, size=(16, 16))


class FullGraph(gt.Graph):
    # this is the main graph, containing all sites and rivers
    # edges taken by opponents are removed
    # node is:
    # key : 'site.id'
    def __init__(self, map, should_display=True):
        gt.Graph.__init__(self,directed=False)
        self.vertex_pos = self.new_vertex_property('vector<double>')
        self.vertex_is_mine = self.new_vertex_property('bool')
        self.vertex_path_for_mine = {}
        self.should_display = should_display
        self.mines = map["mines"]  # get mines in self.mines

        for site in map['sites']:
            v = self.vertex(site['id'], add_missing=True)
            self.vertex_pos[v] = [site['x']/100, site['y']/100]

        self.add_edge_list([(river["source"], river["target"]) for river in map["rivers"]])  # populate edges
        for mine in self.mines:  # precalculate score for all site and all mines as it is static
            self.vertex_path_for_mine[mine] = gt.shortest_distance(self, mine)
            self.vertex_is_mine[mine] = True

        self.maxScore = 0
        for site in self.vertices():
            for mine in self.mines:
                score = self.vertex_path_for_mine[mine][site]
                if score == 2147483647:
                    score = 0
                self.maxScore += score**2


    def display(self):
        if self.should_display:
            gt.graphviz_draw(self,pos = self.vertex_pos, pin=True, size=(16,16))

    def displayScore(self, mapTitle, score, leftMoves):
        pass

    def claim(self, source, target):
        self.remove_edge((source, target))  # only remove the edge in the graph as it is not available anymore