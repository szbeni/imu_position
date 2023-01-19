#!/usr/bin/python3
from scipy.spatial.transform import Rotation as R

import zmq
import random
import sys
import time
import json
import numpy as np
import socket
from madgwick_py.madgwickahrs import MadgwickAHRS
import pygame
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *

verticies = (
    (1, -1, -1),
    (1, 1, -1),
    (-1, 1, -1),
    (-1, -1, -1),
    (1, -1, 1),
    (1, 1, 1),
    (-1, -1, 1),
    (-1, 1, 1)
)

edges = (
    (0, 1),
    (0, 3),
    (0, 4),
    (2, 1),
    (2, 3),
    (2, 7),
    (6, 3),
    (6, 4),
    (6, 7),
    (5, 1),
    (5, 4),
    (5, 7)
)


def Cube():
    glBegin(GL_LINES)
    for edge in edges:
        for vertex in edge:
            glVertex3fv(verticies[vertex])
    glEnd()


m = None


def graph_init():
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)
    glTranslatef(0.0, 0.0, -5)
    global m
    m = glGetFloatv(GL_MODELVIEW_MATRIX)
    print(m)


def graph_loop(angles):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
    # glLoadIdentity()
    #glTranslatef(0.0, 0.0, -5)

    glLoadMatrixf(m)
    glRotatef(angles[0], 1, 0, 0)
    glRotatef(-angles[1], 0, 1, 0)
    glRotatef(angles[2], 0, 0, 1)

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    Cube()
    pygame.display.flip()
    pygame.time.wait(1)


# IMU
graph_init()

HOST = "0.0.0.0"  # Standard loopback interface address (localhost)
PORT = 2055  # Port to listen on (non-privileged ports are > 1023)


port_zmq = "5556"

context = zmq.Context()
zmqsocket = context.socket(zmq.PUB)
zmqsocket.bind("tcp://*:%s" % port_zmq)


linAcc_prev = np.array([0, 0, 0])
linVel_prev = np.array([0, 0, 0])
linPos_prev = np.array([0, 0, 0])

linVelHPEMA = np.array([0, 0, 0])
linPosHPEMA = np.array([0, 0, 0])


samplePeriod = 0.01
madgwick = MadgwickAHRS(sampleperiod=samplePeriod)
madgwick.beta = 0.1


def process_data(data):
    global samplePeriod, linAcc_prev, linVel_prev, linPos_prev, linVelHPEMA, linPosHPEMA, zmqsocket
    values = data.split(',')
    for i in range(0, len(values)):
        values[i] = float(values[i])

    accel = (-values[0], values[1], values[2])  # x,y,z
    mag = (values[3], values[4], values[5])  # xy,xz,zy
    gyro = (values[6], -values[7], -values[8])  # x,y,z
    gps = (values[9], values[10], values[11])  # lat, long, alt

    #madgwick.update(gyro, accel, mag)
    madgwick.update_imu(gyro, accel)

    euler = np.degrees(madgwick.quaternion.to_euler_angles())

    r = R.from_euler('xzy', [euler[0], euler[1], euler[2]], degrees=True)
    acc = np.array(accel) / 9.81

    tcAcc = r.as_matrix().dot(acc)
    linAcc = (tcAcc - np.array([0, 0, 1])) * 9.81

    # calc velocity
    linVel = linVel_prev + linAcc * samplePeriod

    # highpass velocity
    alpha = 0.01
    linVelHPEMA = alpha * linVel + (1.0-alpha)*linVelHPEMA
    linVelHP = linVel - linVelHPEMA

    # calc pos
    linPos = linPos_prev + linVelHP * samplePeriod

    # highpass pos
    #linPosHPEMA = alpha * linPos + (1.0-alpha)*linPosHPEMA
    #linPosHP = linPos - linPosHPEMA

    data = json.dumps(linPos[2])
    zmqsocket.send_string(data)

    linAcc_prev = linAcc
    linVel_prev = linVel
    linPos_prev = linPos
    return euler


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        buffer = ''
        while True:

            data = conn.recv(4096)
            if not data:
                break
            buffer += data.decode()

            if '\n' in buffer:
                lines = buffer.split('\r\n')
                degrees = None
                for i in range(0, len(lines)-1):
                    degrees = process_data(lines[i])
                if degrees is not None:
                    graph_loop(degrees)

                buffer = lines[-1]
