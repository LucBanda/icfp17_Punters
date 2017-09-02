#!/usr/bin/env python3
import signal
import sys
import getopt
from PunterClient import OnlineClient
from PunterPlayer import DiscoveryStrategy
from PunterPlayer import UCTStrategy

# noinspection PyUnusedLocal,PyUnusedLocal
def signal_handler(signal, frame):
    raise IOError()


def printD(string:str):
    print(string, file=sys.stderr)
    pass

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    argv = sys.argv[1:]
    timeout = 2
    port = 9000
    display = False
    strategy = 'discovery'
    debug = False

    try:
        opts, args = getopt.getopt(argv, "hdvt:p:s:")
    except getopt.GetoptError:
        print("punter.py [-d][-v] [-h [-p port] [-t timeout] [-s strategy]]")
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('-h [-d] [-p port] [-t timeout][-s strategy]')
            sys.exit()
        elif opt == "-t":
            timeout = int(arg)
        elif opt == "-p":
            port = int(arg)
        elif opt == "-d":
            display = True
        elif opt == "-s":
            strategy = arg
        elif opt == "-v":
            debug = True

    # play with local server provided by compete at http://git.kthxb.ai/compete/icfpc2017
    client = OnlineClient("localhost", port)  # instanciate and connect online client
    client.title = "local map"  # set the parameters of the client
    client.timeout = timeout
    if strategy == 'uct':
        game = UCTStrategy(client, display, debug)  # instanciate a punter
    else:
        game = DiscoveryStrategy(client, display)  # instanciate a punter
    try:
        client.start()  # start the game
        # if game exits correctly, it means game has ended
        print("local game score : " + str(game.scores[game.client.punter]))
        game.close()
        client.sock.close()
    except IOError as e:
        # this happens in case of connection error
        print(e)
        game.close()
        client.sock.close()

    printD("exit correctly")
