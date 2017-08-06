import matplotlib.pyplot as plt

class gameViz:

    def __init__(self, map):
        self.map = map
        self.puntersClaimed = []
        self.fig = plt.figure(figsize=(10, 30))

    def update(self, map, puntersClaimed):
        self.map = map
        self.puntersClaimed = puntersClaimed

    def display(self):

        plt.title('map')

        for river in self.map.rivers:
            plt.plot([self.map.sites[river.source].x, self.map.sites[river.target].x],
                     [self.map.sites[river.source].y, self.map.sites[river.target].y], "b--", linewidth=1)

        colors = ["r-", "k-", "y-", "m-"]
        for punter in self.puntersClaimed:
            for river in self.puntersClaimed[punter]:
                source = river.source
                target = river.target
                plt.plot([self.map.sites[source].x, self.map.sites[target].x],
                     [self.map.sites[source].y, self.map.sites[target].y], colors[punter], linewidth=5)

        plt.plot([site.x for site in self.map.sites.values()],
                 [site.y for site in self.map.sites.values()], 'k.', label="site")

        plt.plot([site.x for site in self.map.sites.values() if site.isMine],
                 [site.y for site in self.map.sites.values() if site.isMine], 'ro', label="mine")

        plt.show(block = False)
        plt.draw()
        self.fig.canvas.draw()
