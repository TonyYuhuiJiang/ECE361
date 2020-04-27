#
# Copyright 2020 University of Toronto
#
# Permission is hereby granted, to use this software and associated
# documentation files (the "Software") in course work at the University
# of Toronto, or for personal use. Other uses are prohibited, in
# particular the distribution of the Software either publicly or to third
# parties.
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from multiprocessing import Process, JoinableQueue

import time
import random
import signal
import logging
import sys
import math
import os

if len(sys.argv) != 2:
    print("USAGE: python3 %s <total arrival rate G>" % __file__)
    sys.exit(1)

# Set logging format and logging level
# Can change INFO to DEBUG for more information, or WARNING for less information
logging.basicConfig(format='%(asctime)s %(module)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__) # Get logger for *this* module
logger.setLevel(logging.INFO)
start_time = time.time()

# Set up signal handling
TERMINATE = False
def signal_handler(sig, frame):
    global TERMINATE
    if TERMINATE:
        logger.debug("Previous signal detected, killing and exiting now")
        sys.exit(0)
    logger.debug("Signal %s captured!" % sig)
    TERMINATE = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ALOHA Parameters
MAX_BACKOFF = 5 # Seconds
FRAME_SIZE =  704 # bits
TX_RATE = 9600 # bps
SERIAL_DELAY = float(FRAME_SIZE) / TX_RATE
PROP_DELAY = 0 # Seconds
G = float(sys.argv[1])
GLOBAL_ARR_RATE = G / SERIAL_DELAY # Frames / second
NUM_STATIONS = 3
ARR_RATE = float(GLOBAL_ARR_RATE) / NUM_STATIONS # Per-station; Frames / second

logger.info("Frame size = %s bits" % FRAME_SIZE)
logger.info("Tx Rate = %s bps" % TX_RATE)
logger.info("Serializaiton delay = %s seconds" % SERIAL_DELAY)
logger.info("Propagation delay = %s seconds" % PROP_DELAY)
logger.info("Global arrival rate = %s frames / second" % GLOBAL_ARR_RATE)
logger.info("Number of stations = %s" % NUM_STATIONS)
logger.info("Per-station arrival rate = %s frames / second" % ARR_RATE)
logger.info("====================\n\n")

# Simulation parameters
SHARED_MEDIA = JoinableQueue(maxsize=NUM_STATIONS * 2)
ACK_CHAN_MAP = {} # Map from station name => JoinableQueue (one per station)
RUN_TIME = 50 # Seconds to run simulation before exiting
SLOT_INTERVAL = math.ceil(1000 * SERIAL_DELAY) / 1000 # Avoid repeating decimals
assert (SLOT_INTERVAL >= SERIAL_DELAY)

def Station(SHARED_MEDIA, ackChannel, stnName):
    logger.info("Starting %s" % stnName)

    now = time.time()
    lastTxTime = now # Last tx time
    lastPktArrTime = now # Last packet arrival time
    waitingForAck = False
    nextTxTime = math.ceil(now) + 1

    # Sync all stations to a common start time
    time.sleep(nextTxTime - now)

    while True:
        now = time.time()

        if not waitingForAck:
            nextPktArrTime = lastPktArrTime + random.expovariate(ARR_RATE)
            # nextTxTime = nextPktArrTime # i.e. Transmit immediately
            nextTxTime = math.ceil(nextPktArrTime / SLOT_INTERVAL) * SLOT_INTERVAL # i.e. Transmit in intervals

            if now < nextTxTime:
                logger.debug("%s sleeping for %s until %s" % (stnName, (nextTxTime - now), nextTxTime))
                time.sleep(nextTxTime - now)

            # Stay faithful to exponential inter-arrival times
            lastTxTime = nextTxTime
            lastPktArrTime = nextPktArrTime

            data = random.random()
            packet = (lastTxTime, stnName, data)
            logger.debug("%s writing data: %s" % (stnName, packet))

            # Transmit
            try:
                SHARED_MEDIA.put(packet, timeout=5)
            except:
                logger.error("\n\nERROR: %s could not tx! Queue size is %s\n\n" % (stnName, SHARED_MEDIA.qsize()))
                break

            waitingForAck = True
        else:
            # The mathematical models do not account for timeout back-off.
            # Thus, set timeout = 0 to match the models. If the goal is to
            # have a realistic simulation, then the timeout should be set
            # to a minimum value:
            #   lastTxTime + SERIAL_DELAY + (2 * PROP_DELAY)
            timeout = 0
            if now > timeout:
                # Simply set waitingForAck to False. The poisson process
                # process used is for R, the traffic rate that includes
                # re-transmissions. Thus, just do another exponential sleep,
                # and resume transmitting.
                waitingForAck = False

            # Use 'while', ACKs may have been delayed, built-up in queue
            # This is an artifact of a coded simulation, no such queue in ALOHA
            while not ackChannel.empty():
                ack = ackChannel.get()
                ackChannel.task_done()
                if ack == stnName:
                    logger.debug("%s received an ACK" % stnName)
                    waitingForAck = False
                else:
                    logger.error("\n\nERROR: %s got ACK for %s\n\n" % (stnName, ack))
                    break

        # Break and exit if signal has been caught
        if TERMINATE:
            break

def SharedMedia(SHARED_MEDIA, ACK_CHAN_MAP):
    currPacket = None
    chanFreeAfter = 0 # Time after which channel is free
    ackNum = 0
    while True:
        now = time.time()

        # ACK outstanding packet that have been successfully received
        if currPacket and now > chanFreeAfter:
            # Frame successfully received without collission, send ACK
            logger.debug("Central: Sending ACK to %s" % currPacket[1])
            ackChannel = ACK_CHAN_MAP.get(currPacket[1])
            try:
                ackChannel.put(currPacket[1], timeout=5)
            except:
                logger.error("\n\nERROR: Central station couldn't ACK %s! Queue size is %s" % (currPacket[1], ackChannel.qsize()))
                break

            currPacket = None
            chanFreeAfter = 0
            ackNum += 1

            # Print debugging info (e.g. # of ACKs)
            elapsedTime = now - start_time
            S = SERIAL_DELAY * ackNum / elapsedTime
            logger.info("\n--- %s seconds ---" % (elapsedTime))
            logger.info("Number of ACKs: %s" % ackNum)
            logger.info("\tS: %s" % S)

            # Append results to ouptut file if simulation is over
            if (elapsedTime > RUN_TIME):
                fout = open("out.txt", 'a')
                fout.write(str(G) + "," + str(S) + "\n")
                fout.close()
                logger.info("Written results to file, exiting central station")
                break

        while not SHARED_MEDIA.empty():
            packet = SHARED_MEDIA.get()
            SHARED_MEDIA.task_done()
            logger.debug("Central: Received packet: %s" % (packet,))

            # Determine if collision occured; two scenarios:
            #   1. currPacket is not None
            #   2. Previous collision occurred, but sender kept sending
            if currPacket or packet[0] <= chanFreeAfter:
                # Discard currPacket and ignore current packet
                currPacket = None
                logger.debug("Central: UH OH, COLLISION!")
            else:
                currPacket = packet

            if packet[0] + SERIAL_DELAY + PROP_DELAY > chanFreeAfter:
                chanFreeAfter = packet[0] + SERIAL_DELAY + PROP_DELAY

        # Break and exit if signal has been caught
        if TERMINATE:
            break


# Add stations
STATION_PROCS = []
for i in range(NUM_STATIONS):
    stnName = "Station-%s" % (i + 1)
    ackChannel = JoinableQueue(maxsize=10)
    ACK_CHAN_MAP[stnName] = ackChannel
    proc = Process(target=Station, args = (SHARED_MEDIA, ackChannel, stnName))
    proc.daemon = True
    STATION_PROCS.append(proc)

# Run central station
centralProc = Process(target=SharedMedia, args = (SHARED_MEDIA, ACK_CHAN_MAP))
centralProc.daemon = True
centralProc.start()

# Start stations here (after central station is up)
for proc in STATION_PROCS:
    proc.start()

# Wait for central station to end, then send SIGINT to the stations
centralProc.join()

for proc in STATION_PROCS:
    pid = proc.pid
    os.kill(pid, signal.SIGINT)

# Wait for station procs to end
for proc in STATION_PROCS:
    proc.join()

logger.info("Total run time: %s seconds" % (time.time() - start_time))
logger.info("Exiting, bye!")


