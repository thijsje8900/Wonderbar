# ledmatrix-scroll by Andrew Oakley www.aoakley.com Public Domain 2015-10-18
#
# Takes an image file (e.g. PNG) as command line argument and scrolls it
# across a grid of WS2811 addressable LEDs, repeated in a loop until CTRL-C
#
# Use a very wide image for good scrolling effect.
#
# If you have a low resolution matrix (like mine, 12x8 LEDs) then you will
# probably need to create your image height equal to your matrix height
# and draw lettering pixel by pixel (e..g in GIMP or mtpaint) if you want
# words or detail to be legible.

import time, sys, os, re
from neopixel import * # See https://learn.adafruit.com/neopixels-on-raspberry-pi/software
from PIL import Image  # Use apt-get install python-imaging to install this
import logging
import socket
import struct

# LED strip configuration:
LED_COUNT      = 576*3      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 15     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)

# Speed of movement, in seconds (recommend 0.1-0.3)
SPEED=1

# Size of your matrix
MATRIX_WIDTH=24
MATRIX_HEIGHT=24

# LED matrix layout
# A list converting LED string number to physical grid layout
# Start with top right and continue right then down
# For example, my string starts bottom right and has horizontal batons
# which loop on alternate rows.
#
# Mine ends at the top right here:     -----------\
# My last LED is number 95                        |
#                                      /----------/
#                                      |
#                                      \----------\
# The first LED is number 0                       |
# Mine starts at the bottom left here: -----------/ 

myMatrix=[0, 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,
48,47,46,45,44,43,42,41,40,39,38,37,36,35,34,33,32,31,30,29,28,27,26,25,
49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,
96,95,94,93,92,91,90,89,88,87,86,85,84,83,82,81,80,79,78,77,76,75,74,73,
97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,
144,143,142,141,140,139,138,137,136,135,134,133,132,131,130,129,128,127,126,125,124,123,122,121,
145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,
192,191,190,189,188,187,186,185,184,183,182,181,180,179,178,177,176,175,174,173,172,171,170,169,
193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,
240,239,238,237,236,235,234,233,232,231,230,229,228,227,226,225,224,223,222,221,220,219,218,217,
241,242,243,244,245,246,247,248,249,250,251,252,253,254,255,256,257,258,259,260,261,262,263,264,
288,287,286,285,284,283,282,281,280,279,278,277,276,275,274,273,272,271,270,269,268,267,266,265,
289,290,291,292,293,294,295,296,297,298,299,300,301,302,303,304,305,306,307,308,309,310,311,312,
336,335,334,333,332,331,330,329,328,327,326,325,324,323,322,321,320,319,318,317,316,315,314,313,
337,338,339,340,341,342,343,344,345,346,347,348,349,350,351,352,353,354,355,356,357,358,359,360,
384,383,382,381,380,379,378,377,376,375,374,373,372,371,370,369,368,367,366,365,364,363,362,361,
385,386,387,388,389,390,391,392,393,394,395,396,397,398,399,400,401,402,403,404,405,406,407,408,
432,431,430,429,428,427,426,425,424,423,422,421,420,419,418,417,416,415,414,413,412,411,410,409,
433,434,435,436,437,438,439,440,441,442,443,444,445,446,447,448,449,450,451,452,453,454,455,456,
480,479,478,477,476,475,474,473,472,471,470,469,468,467,466,465,464,463,462,461,460,459,458,457,
481,482,483,484,485,486,487,488,489,490,491,492,493,494,495,496,497,498,499,500,501,502,503,504,
528,527,526,525,524,523,522,521,520,519,518,517,516,515,514,513,512,511,510,509,508,507,506,505,
529,530,531,532,533,534,535,536,537,538,539,540,541,542,543,544,545,546,547,548,549,550,551,552,
576,575,574,573,572,571,570,569,568,567,566,565,564,563,562,561,560,559,558,557,556,555,554,553]

# Feel free to write a fancy set of loops to populate myMatrix
# if you have a really big display! I used two cheap strings of
# 50 LEDs, so I just have a 12x8 grid = 96 LEDs
# I got mine from: http://www.amazon.co.uk/gp/product/B00MXW054Y
# I also used an 74AHCT125 level shifter & 10 amp 5V PSU
# Good build tutorial here:
# https://learn.adafruit.com/neopixels-on-raspberry-pi?view=all

# Check that we have sensible width & height
if MATRIX_WIDTH * MATRIX_HEIGHT != (len(myMatrix)-1):
  raise Exception("Matrix width x height does not equal length of myMatrix")

def allonecolour(strip,colour):
  # Paint the entire matrix one colour
  for i in range(strip.numPixels()):
    strip.setPixelColor(i,colour)
  strip.show()

def initLeds(strip):
  # Intialize the library (must be called once before other functions).
  strip.begin()
  # Wake up the LEDs by briefly setting them all to white
  allonecolour(strip, Color(255,255,255))
  time.sleep(0.01)

log = logging.getLogger('udp_server')

def udp_server(host='0.0.0.0', port=65506):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    log.info("Listening on udp %s:%s" % (host, port))
    s.bind((host, port))
    while True:
        (data, addr) = s.recvfrom((LED_COUNT * 3) + 6)
        yield data

FORMAT_CONS = '%(asctime)s %(name)-12s %(levelname)8s\t%(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT_CONS)

# Create NeoPixel object with appropriate configuration.
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
initLeds(strip)

# And here we go.
try:
    for data in udp_server():
        print("Received packet")
        start_packet = struct.unpack('!H', b'\x00' + data[0:1])
        packet_type = "0x%x" % struct.unpack('!H', b'\x00' + data[1:2])
        data_length = struct.unpack('!H', data[2:4])
        packet_no = struct.unpack('>H', b'\x00' + data[4:5])
        packet_length = struct.unpack('>H', b'\x00' + data[5:6])

        # We don't care for other types
        if packet_type != "0xda":
            continue

        offset_bytes = 6
        i = 0

        # print(data[offset_bytes + i])
        # print(data[offset_bytes + i + 1])
        # print(data[offset_bytes + i + 2])

        matrixIndex = 0

        try:
            while (i+3) < data_length[0]:
                index = int((i/3)+1)
                matrixIndex = myMatrix[index + 1]
                dataIndex = offset_bytes + i
                
                # if index > 0 and index < 49:
                    # print("%r %r %r %r %r" % (myMatrix[index], index, data[dataIndex], data[dataIndex + 1], data[dataIndex + 2]))

                strip.setPixelColor(myMatrix[index] - 1, Color(data[dataIndex], data[dataIndex + 1], data[dataIndex + 2]))
                strip.setPixelColor(myMatrix[index] - 1 + 576, Color(data[dataIndex], data[dataIndex + 1], data[dataIndex + 2]))
                strip.setPixelColor(myMatrix[index] - 1 + (576*2), Color(data[dataIndex], data[dataIndex + 1], data[dataIndex + 2]))
                i += 3

            dataIndex = offset_bytes + (data_length[0]-3)
            strip.setPixelColor(myMatrix[len(myMatrix) - 1] - 1, Color(data[dataIndex], data[dataIndex + 1], data[dataIndex + 2]))
            strip.setPixelColor(myMatrix[len(myMatrix) - 1] - 1 + 576, Color(data[dataIndex], data[dataIndex + 1], data[dataIndex + 2]))
            strip.setPixelColor(myMatrix[len(myMatrix) - 1] - 1 + (576*2), Color(data[dataIndex], data[dataIndex + 1], data[dataIndex + 2]))
            strip.show()
        except (IndexError):
            print("Index error")
            print(i)
            print(i+1)
            print(i + 2)
            print(matrixIndex)
            print(len(data))
            time.sleep(SPEED)


except (KeyboardInterrupt, SystemExit):
 # print "Stopped"
  allonecolour(strip, Color(0,0,0))

