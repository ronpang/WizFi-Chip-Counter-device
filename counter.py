import board
import busio
import time
import TM1637
from digitalio import DigitalInOut
from digitalio import Direction
from adafruit_espatcontrol import adafruit_espatcontrol

#digitalio method
pulses = DigitalInOut(board.GP13)
pulses.direction = Direction.INPUT

pulses2 = DigitalInOut(board.GP1)
pulses2.direction = Direction.INPUT

CLK = board.GP7
DIO = board.GP6
display = TM1637.TM1637(CLK, DIO)

""" WizFi360 Section"""
# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# Debug Level
# Change the Debug Flag if you have issues with AT commands
debugflag = True
#LED = board.GP25

RX = board.GP5
TX = board.GP4
resetpin = DigitalInOut(board.GP20)
rtspin = False
uart = busio.UART(TX, RX, baudrate=115200, receiver_buffer_size=2048)
#edit host and port to match server
Dest_IP = "10.0.1.74"
Dest_PORT= 5000

print("ESP AT commands")
print(uart.baudrate)
# For Boards that do not have an rtspin like challenger_rp2040_wifi set rtspin to False.
esp = adafruit_espatcontrol.ESP_ATcontrol(
    uart, 115200, reset_pin=resetpin, rts_pin=rtspin, debug=debugflag
)
print("Resetting ESP module")
esp.hard_reset()
print("Checking connection")

while not esp.is_connected:
  try:
    # Some ESP do not return OK on AP Scan.
    # See https://github.com/adafruit/Adafruit_CircuitPython_ESP_ATcontrol/issues/48
    # Comment out the next 3 lines if you get a No OK response to AT+CWLAP
    print("Scanning for AP's")
    for ap in esp.scan_APs():
        print(ap)
    print("Checking connection...")
    # secrets dictionary must contain 'ssid' and 'password' at a minimum
    print("Connecting...")
    esp.connect(secrets)
    print("Connected to AT software version ", esp.version)
    print("IP address ", esp.local_ip)
    
  except (ValueError, RuntimeError, adafruit_espatcontrol.OKError) as e:
    print("Failed to get data, retrying\n", e)
    print("Resetting ESP module")
    #esp.hard_reset()
    continue

""" Counter section"""
class pulse_detect:
    counter = 0
    C_counter = 0
    T_counter = 0
    wait_count = 0
    #p_counter = 0
    current_stage = None
    previous_stage = 0b00
    flow = None
    flow2 = None
    direction = None
    def __init__(self, pulse,pulse2):
        self.pulse = pulse # Main on the left
        self.pulse2 = pulse2 # Direction support  - on the right

    def stage (self):
        """Two IR Sensor - Direction counting"""
        if self.pulse.value is False:
            self.flow = 0b00
        elif self.pulse.value is True:
            self.flow = 0b10
            #self.p_counter += 1
        if self.pulse2.value is False:
            self.flow2 = 0b00
        elif self.pulse2.value is True:
            self.flow2 = 0b01
        self.current_stage = self.flow +self.flow2
        #print(self.p_counter)
        #print(self.pulse.value)
        """One IR Sensor - One direction counting"""
        """
        self.current_stage = self.pulse.value
        if self.previous_stage is None:
            self.previous_stage = self.current_stage
        elif self.previous_stage is self.current_stage:
            self.wait_count += 1
        elif self.previous_stage is not self.current_stage: #determin is it a uprise value or a downards value
            self.T_counter += 1
            if self.previous_stage is False and self.current_stage is True:
                self.flow += b'01'
                self.previous_stage = self.current_stage
            elif self.previous_stage is True and self.current_stage is False:
                self.flow += b'10'
                self.previous_stage = self.current_stage
            self.wait_count = 0
        """
    def hole_count(self):
        """Two IR Sensor - Direction counting"""
        if self.previous_stage is 0b11 and self.current_stage is not self.previous_stage:
            if self.current_stage is 0b01:
                self.counter += 1
            elif self.current_stage is 0b10:
                self.counter -= 1
            self.wait_count = 0
        elif self.current_stage is self.previous_stage:
            self.wait_count += 1
            
        self.previous_stage = self.current_stage
        #print (self.counter)
        self.C_counter = round(self.counter /3)
        
        """One IR Sensor - One direction counting"""
        """
        if len(self.flow) <= 2:
            pass
        else:
            if self.flow == b'0110':
                self.direction = True #Upwards pulse: 0 -> 1 -> 0
                self.counter += 1
                self.flow = b''
            elif self.flow == b'1001':
                self.direction = False #Downwards pulse: 1 -> 0 -> 1
                self.counter += 1
                self.flow = b''
            else:
                print (self.flow)
                raise RuntimeError("Wrong Input")
            
            self.C_counter = self.counter /3
            if self.counter % 3 == 0:
                self.C_counter = self.counter / 3
            else:
                self.C_counter = (self.counter - (self.counter % 3))/3 + 1
          """  
                             
    def chip_count(self, data):
        Max = data.decode()
        R_data = 0
        wait = 0
        if Max is "CV":
            mode = 1
            display.number(R_data)
        else:
            mode = 0
            display.number(R_data)
        while True:
            if mode is 0:    
                if R_data is int(Max):
                    self.C_counter = 0
                    self.counter = 0
                    return R_data
            elif mode is 1:
                wait = self.wait_count /10000
                if wait > 1:
                    self.C_counter = 0
                    self.counter = 0
                    self.wait_count = 0
                    return R_data
                    
            time.sleep(1/1000000000000)
            self.stage()
            self.hole_count()
            if R_data is not int(self.C_counter):
                R_data = int(self.C_counter)
                print ("Chip count: " + str(R_data))
                display.number(R_data)

detect = pulse_detect (pulses, pulses2)
esp.socket_create(5000)
while True:
    data = esp.socket_receive(1)
    if data:
       r_msg = detect.chip_count(data)
       esp.socket_send(str(r_msg).encode())
