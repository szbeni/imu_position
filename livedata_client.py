import zmq
import json
from time import sleep

import zmq
import random
import sys
import time

port = "5555"

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:%s" % port)

i = 0
while True:
    asd = [0, i, 0]
    data = json.dumps(asd)
    socket.send_string(data)
    i += 0.3
    if i > 100:
        i = 0

    time.sleep(0.01)
