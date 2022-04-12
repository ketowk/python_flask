from flask import Flask, render_template, request
import argparse
import asyncio
import json
import logging
import os
import ssl
import uuid
import numpy as np
import matplotlib.pyplot as plt
from aiohttp import web
from av import VideoFrame
import aiohttp_cors
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaRelay
import requests
import sched, time
import threading
import random
app = Flask(__name__)
ROOT = os.path.dirname(__file__)

logger = logging.getLogger("pc")
pcs = set()
relay = MediaRelay()
global user_id;

@app.route('/')
def hello_world():
    return render_template("index.html")

@app.route('/offer', methods = ['POST'])
async def offer():

    f_stop = threading.Event()
    # start calling f now and every 60 sec thereafter
    f(f_stop)
    print(request)
    params = request.json

    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    pcs.add(pc)

    def log_info(msg, *args):
        logger.info(pc_id + " " + msg, *args)

    #log_info("Created for %s", request)

    # prepare local media
    #player = MediaPlayer(os.path.join(ROOT, "demo-instruct.wav"))
    #recorder = MediaBlackhole()

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str) and message.startswith("ping"):
                channel.send("pong" + message[4:])

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        log_info("Connection state is %s", pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track):
        log_info("Track %s received", track.kind)
        print("track recieveddd")

        if track.kind == "audio":
            #pc.addTrack(player.audio)
            #recorder.addTrack(track)
            print("audio")
        elif track.kind == "video":
            pc.addTrack(
                VideoTransformTrack(
                    relay.subscribe(track), transform=params["video_transform"], id=params["id"]
                )
            )

        @track.on("ended")
        async def on_ended():
            log_info("Track %s ended", track.kind)
            #await recorder.stop()

    # handle offer
    await pc.setRemoteDescription(offer)
    #await recorder.start()

    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    #return web.Response(
    #    content_type="application/json",
    #    text=json.dumps(
    #        {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
    #    ),
    #)

    return "return value"

class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"
    counter = 0;

    def __init__(self, track, transform,id):
        super().__init__()  # don't forget this!
        self.track = track
        self.transform = transform
        user_id = id
        print(id)
        

    async def recv(self):
        frame = await self.track.recv()
        #print("recv")
        return frame

def f(f_stop):
    print(user_id)
    n = random.randint(0,100)
    url = 'http://kemalbayik.com/write_od_outputs.php'
    myobj = {'id': user_id,
             'percentage': n}

    x = requests.post(url, data = myobj)

    print(x.text)
    if not f_stop.is_set():
        # call f() again in 60 seconds
        threading.Timer(10, f, [f_stop]).start()
