import matplotlib.pyplot as plt

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
        self.rivers = []
        self.sites = {}
        self.mines = []
        self.constructedX = 0
        self.constructedY = 0
        self.toggle = 0
        self.riverClaimed = {}

        self.fig = plt.figure(figsize=(10, 30))

        if map == None:
            return

        for site in map["sites"]:
            if site.has_key("x"):
                x = float(site["x"])
                y = float(site["y"])
            else:
                if self.toggle:
                    self.constructedX += 1
                    self.toggle = 0
                else:
                    self.constructedY += 1
                    self.toggle = 1
                x = self.constructedX
                y = self.constructedY

            id = int(site["id"])
            siteToAdd = Site(id, x, y)

            self.sites[id] = siteToAdd

            if site["id"] in map["mines"]:
                self.sites[id].isMine = True

        for river in map["rivers"]:
            riverToAdd = River(river["source"],river["target"])
            self.sites[river["source"]].addRiver(riverToAdd)
            self.sites[river["target"]].addRiver(riverToAdd)
            self.rivers.append(riverToAdd)

        self.mines = map["mines"]


    def display(self):

        plt.title('map')

        for river in self.rivers:
            plt.plot([self.sites[river.source].x, self.sites[river.target].x],
                     [self.sites[river.source].y, self.sites[river.target].y], "b--", linewidth=1)

        colors = ["r-", "k-", "y-", "m-"]
        for punter in self.riverClaimed:
            for river in self.riverClaimed[punter]:
                source = river.source
                target = river.target
                plt.plot([self.sites[source].x, self.sites[target].x],
                     [self.sites[source].y, self.sites[target].y], colors[punter], linewidth=5)

        plt.plot([site.x for site in self.sites.values()],
                 [site.y for site in self.sites.values()], 'k.', label="site")

        plt.plot([site.x for site in self.sites.values() if site.isMine],
                 [site.y for site in self.sites.values() if site.isMine], 'ro', label="mine")

        plt.show(block = False)
        plt.draw()
        self.fig.canvas.draw()