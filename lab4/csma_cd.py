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

import sys
import time
import argparse

from ece361.lab4 import StationArrivals

# Non-configurable parameters
MEDIUM_VELOCITY = 97656250 # m/s

# Depends on arguments, will be calculated later
SERIALIZATION_DELAY = None
PROP_DELAY = None
NORM_DELAY_BW = None

def PrintSimulationParameters(args):
    # Print simulation params
    print("\n====================")
    print("SIMULATION PARAMETERS:")
    print("  - NUM_STATIONS = %s" % args.num_stations)
    print("  - NUM_FRAMES = %s (per station)" % args.num_frames)
    print("  - ARR_RATE = %s (frames / sec)" % args.arr_rate)
    print("  - FRAME_SIZE = %s (bits)" % args.frame_size)
    print("  - MEDIUM_BW = %s (bits / sec)" % args.bandwidth)
    print("  - MEDIUM_DIAMETER = %s (metres)" % args.diameter)
    print("  - MEDIUM_VELOCITY = %s (metres / sec)" % MEDIUM_VELOCITY)
    print("  - SERIALIZATION_DELAY = %s (sec)" % SERIALIZATION_DELAY)
    print("  - PROP_DELAY = %s (sec)" % PROP_DELAY)
    print("  - NORM_DELAY_BW = %s" % NORM_DELAY_BW)


def SetupSimulation(args):
    totalFrames = args.num_frames * args.num_stations

    # Generate arrival times
    print("\n====================")
    print("Generating arrival times...")
    START_TIME = time.time()

    # Create a StationArrivals object
    # This includes all the expected arrival information for all stations
    stationArrivals = StationArrivals(args.num_stations, args.num_frames,
                              SERIALIZATION_DELAY, args.arr_rate, args.seed)

    ELAPSED_TIME = time.time() - START_TIME
    print("Generated %s arrivals in %s seconds" % (totalFrames, ELAPSED_TIME))

    print("\n====================")
    print("Starting CSMA-CD simulation...")
    START_TIME = time.time()

    # Run simulation
    from simulation_logic import RunSimulation
    (numStnObsvSuccess, numActualCollisions,
        numStnObsvCollisions, simTime) = RunSimulation(stationArrivals,
                                                        args.num_stations,
                                                        PROP_DELAY,
                                                        SERIALIZATION_DELAY,
                                                        args.quiet)

    ELAPSED_TIME = time.time() - START_TIME
    print("Elapsed real time: %s seconds" % round(ELAPSED_TIME, 5))
    print("Elapsed simulation time: %s seconds" % round(simTime, 5))

    assert (numStnObsvSuccess + numStnObsvCollisions) == totalFrames

    # Calculate and print statistics (stations' point-of-view vs actual)
    print("\n====================")
    print("Stations' statistics (stations' point-of-view):")
    proportion = round(numStnObsvSuccess / totalFrames * 100, 3)
    print("  - Number of successful transmissions: %s (%s %%)" % (numStnObsvSuccess, proportion))

    print("  - Number of frame collisions: %s" % numStnObsvCollisions)

    chanEfficiency = round(numStnObsvSuccess * args.frame_size / simTime / args.bandwidth * 100, 3)
    print("  - Efficiency of channel utilization: %s %%" % chanEfficiency)

    print("\nActual statistics:")
    numActualSuccess = totalFrames - numActualCollisions
    proportion = round(numActualSuccess / totalFrames * 100, 3)
    print("  - Number of successful transmissions: %s (%s %%)" % (numActualSuccess, proportion))

    print("  - Number of frame collisions: %s" % numActualCollisions)

    chanEfficiency = round(numActualSuccess * args.frame_size / simTime / args.bandwidth * 100, 3)
    print("  - Efficiency of channel utilization: %s %%" % chanEfficiency)

def ParseArguments():
    description = "ECE361 simulator for CSMA/CD"
    parser = argparse.ArgumentParser(description = description,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--num-stations", action="store", type=int, default=3,
                        help="Number of stations")
    parser.add_argument("--num-frames", action="store", type=int, default=1000000,
                        help="Number of frames per station")
    parser.add_argument("--arr-rate", action="store", type=float, default=10000.0,
                        help="Arrival rate per station (frames per second)")
    parser.add_argument("--frame-size", action="store", type=int, default=512,
                        help="Size of each frame (bits)")
    parser.add_argument("--bandwidth", action="store", type=int, default=10000000,
                        help="Bandwidth of the medium (bits per second)")
    parser.add_argument("--diameter", action="store", type=float, default=2500,
                        help="Diameter of the network (metres)")
    parser.add_argument("--seed", action="store", type=int, default=-1,
                        help="Seed for random number generators (positive integers only)")
    parser.add_argument("--quiet", action="store_true", default=False,
                        help="Suppress the period printing of stations' status")

    args = parser.parse_args()

    # Calculate argument-dependent simulation params
    global SERIALIZATION_DELAY, PROP_DELAY, NORM_DELAY_BW
    SERIALIZATION_DELAY = args.frame_size / args.bandwidth
    PROP_DELAY = args.diameter / MEDIUM_VELOCITY
    NORM_DELAY_BW = PROP_DELAY * args.bandwidth / args.frame_size

    return args

if __name__ == "__main__":
    args = ParseArguments()

    PrintSimulationParameters(args)

    SetupSimulation(args)

    sys.exit(0)
