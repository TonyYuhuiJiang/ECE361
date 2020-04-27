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

import time

from ece361.lab4 import FrameMetadata

PRINT_PERIOD = 1.0

# Core logic of the CSMA/CD simulator
# Input:
#   - stationArrivals: Object of type StationArrivals containing the arrival
#                      times for each station. Students need not know about this.
#   - numStations: The number of simulated stations.
#   - propDelay: The medium's propagation delay. Proportional to the network diameter.
#   - serializationDelay: The time required to transmit a frame. A function of
#                         the frame size the the channel bandwidth.
#
# Returns: A single tuple of 4 values:
#   - (numStnObsvSuccess, numActualCollisions, numStnObsvCollisions, simulationEndTime)
#     The first three variables will have to be incremented by the student's code.
#     See the comments below for the purposes of the first three variables.
def RunSimulation(stationArrivals, numStations, propDelay, serializationDelay, quiet = False):

    # Counter variables to track and return
    # The number of actual frame collisions that occurred
    numActualCollisions = 0

    # The number of frame collisions where the source station was aware
    # of the occurrence of the collision
    numStnObsvCollisions = 0

    # The number of frames where the source station believes it successfully
    # delivered the frame (successful delivery means no collisions)
    numStnObsvSuccess = 0

    # Calling stationArrivals.getNextArrival() will return the next arriving
    # frame to be transmitted in the simulation. This will be an object of
    # type FrameMetadata. Thus, lastFrame and currFrame should be used to hold
    # objects of this type, or None.
    #
    # Starting condition, set lastFrame to the first frame
    lastFrame = stationArrivals.getNextArrival()
    currFrame = None

    lastProgressUpdate = 0
    startTime = time.time()
    while True:
        # Print progress updates
        now = time.time()
        if not quiet and now - lastProgressUpdate > PRINT_PERIOD:
            lastProgressUpdate = time.time()
            print("\nProgress update (%s seconds)" % int(now - startTime))
            for stnID in range(numStations):
                print("Station %s has %s remaining frames" % (stnID, len(stationArrivals.stnPktArrTimes[stnID])))

        currFrame = stationArrivals.getNextArrival()
        if currFrame is None:
            # Last frame will obviously succeed
            numStnObsvSuccess += 1
            print("\nFinished transmitting frames from all stations")
            break

        currFrameBegin = currFrame.arrTime
        currFrameFinish = currFrameBegin + serializationDelay
        lastFrameBegin = lastFrame.arrTime
        lastFrameFinish = lastFrameBegin + serializationDelay
        lastFrameRxBegin = lastFrameBegin + propDelay
        lastFrameRxFinish = lastFrameBegin + propDelay + serializationDelay

        # Sanity check
        if currFrame.stnID == lastFrame.stnID:
            assert (currFrame.arrTime - lastFrame.arrTime) >= serializationDelay

            numStnObsvSuccess += 1
                
        else: # currFrame.stnID != lastFrame.stnID

            assert (currFrameBegin > lastFrameBegin)

            # if lastFrameBegin < currFrameBegin < lastFrameFinish < currFrameFinish:
            #     if currFrameBegin > lastFrameRxBegin:
            #         # Medium is busy
            #         stationArrivals.rescheduleFrame(currFrame)
            #         continue
            #     numActualCollisions += 1
            #     # Case 1
            #     # Collision detected
            #     if currFrameBegin + propDelay < lastFrameFinish:
            #         numStnObsvCollisions += 1
            #     else:
            #         # Case 2
            #         # Collision undetected
            #         numStnObsvSuccess += 1
            # elif lastFrameBegin < lastFrameFinish < currFrameBegin < currFrameFinish:
            #     if currFrameBegin < lastFrameRxFinish:
            #         # Medium is busy
            #         stationArrivals.rescheduleFrame(currFrame)
            #         continue
            #     numStnObsvSuccess += 1
            # else:
            #     print("Error, we shouldn't be here")
            #     exit(-1)
            if currFrameBegin >= lastFrameRxFinish:
                numStnObsvSuccess += 1
            elif currFrameBegin >= lastFrameRxBegin:
                stationArrivals.rescheduleFrame(currFrame)
            else:
                numActualCollisions += 1
                if currFrameBegin + propDelay < lastFrameFinish:
                    numStnObsvCollisions += 1
                else:
                    numStnObsvSuccess += 1



        lastFrame = currFrame


    # The end time within the simulation (i.e. not real time / wall clock)
    simulationEndTime = lastFrame.arrTime + serializationDelay + propDelay

    return (numStnObsvSuccess, numActualCollisions,
            numStnObsvCollisions, simulationEndTime)