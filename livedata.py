import time
from matplotlib import pyplot as plt
import numpy as np
import json
import time
import zmq

context = zmq.Context()
socket = context.socket(zmq.SUB)
port = 5556
socket.setsockopt(zmq.CONFLATE, 1)
socket.connect("tcp://localhost:%s" % port)
topicfilter = ""
socket.setsockopt_string(zmq.SUBSCRIBE, topicfilter)


fig = plt.figure()
fig.canvas.draw()
x = np.linspace(0, 50., num=100)
ax = fig.add_subplot(2, 1, 2)
line, = ax.plot([], lw=3)
text = ax.text(0.8, 0.5, "")
plt.show(block=False)

t_start = time.time()
i = 0
x = []
y = []
cntr = 0
while True:
    try:
        # check for a message, this will not block
        message = socket.recv(flags=zmq.NOBLOCK)

        # a message has been received
        #print("Received request: %s" % message)
        data = json.loads(message.decode())
        # print(data[1])
        x.append(cntr)
        y.append(data)

        x = x[-100:]
        y = y[-100:]
        cntr += 1
        ax.set_xlim(x[0], x[-1])
        ax.set_ylim([-1, 1])
        #ax.set_ylim([min(y), max(y)])

    except zmq.Again as e:
        pass
    line.set_data(x, y)

    tx = 'Mean Frame Rate:\n {fps:.3f}FPS'.format(
        fps=((i+1) / (time.time() - t_start)))
    text.set_text(tx)

    i += 1
    fig.canvas.draw()
    fig.canvas.flush_events()


def live_update_demo(blit=False):
    # x = np.linspace(0, 50., num=100)
    # X, Y = np.meshgrid(x, x)
    # fig = plt.figure()
    # ax1 = fig.add_subplot(2, 1, 1)
    # ax2 = fig.add_subplot(2, 1, 2)

    # img = ax1.imshow(X, vmin=-1, vmax=1, interpolation="None", cmap="RdBu")

    # line, = ax2.plot([], lw=3)
    # text = ax2.text(0.8, 0.5, "")

    # ax2.set_xlim(x.min(), x.max())
    # ax2.set_ylim([-1.1, 1.1])

    fig.canvas.draw()   # note that the first draw comes before setting data

    if blit:
        # cache the background
        axbackground = fig.canvas.copy_from_bbox(ax1.bbox)
        ax2background = fig.canvas.copy_from_bbox(ax2.bbox)

    plt.show(block=False)

    t_start = time.time()
    k = 0.

    for i in np.arange(1000):
        img.set_data(np.sin(X/3.+k)*np.cos(Y/3.+k))
        line.set_data(x, np.sin(x/3.+k))
        tx = 'Mean Frame Rate:\n {fps:.3f}FPS'.format(
            fps=((i+1) / (time.time() - t_start)))
        text.set_text(tx)
        # print tx
        k += 0.11
        if blit:
            # restore background
            fig.canvas.restore_region(axbackground)
            fig.canvas.restore_region(ax2background)

            # redraw just the points
            ax1.draw_artist(img)
            ax2.draw_artist(line)
            ax2.draw_artist(text)

            # fill in the axes rectangle
            fig.canvas.blit(ax1.bbox)
            fig.canvas.blit(ax2.bbox)

            # in this post http://bastibe.de/2013-05-30-speeding-up-matplotlib.html
            # it is mentionned that blit causes strong memory leakage.
            # however, I did not observe that.

        else:
            # redraw everything
            fig.canvas.draw()

        fig.canvas.flush_events()
        # alternatively you could use
        # plt.pause(0.000000000001)
        # however plt.pause calls canvas.draw(), as can be read here:
        # http://bastibe.de/2013-05-30-speeding-up-matplotlib.html


# live_update_demo(True)   # 175 fps
# live_update_demo(False)  # 28 fps
