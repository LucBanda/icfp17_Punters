

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
        self.map = map
        self.rivers = []
        self.sites = {}
        self.mines = []
        self.constructedX = 0
        self.constructedY = 0
        self.toggle = 0
        if map == None:
            return

        for site in self.map["sites"]:
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

            if site["id"] in self.map["mines"]:
                self.sites[id].isMine = True

        for river in self.map["rivers"]:
            riverToAdd = River(river["source"],river["target"])
            self.sites[river["source"]].addRiver(riverToAdd)
            self.sites[river["target"]].addRiver(riverToAdd)
            self.rivers.append(riverToAdd)

        self.mines = self.map["mines"]
