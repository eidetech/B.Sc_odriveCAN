import math
import can
import cantools
import time
from odrive.enums import *
from cmd_id_enums import *
from motor import *

M0 = Motor(0x00)
M1 = Motor(0x01)

# Import database containing can messages
db = cantools.database.load_file("odrive-cansimple.dbc")

# bus = can.Bus("vcan0", bustype="virtual")
bus = can.Bus("can0", bustype="socketcan")

#axisID_M0 = 0x00
#axisID_M1 = 0x01

#axisID_M0_shifted = axisID_M0 << 5
#axisID_M1_shifted = axisID_M1 << 5

# Calibration sequence for M0
print("\nRequesting AXIS_STATE_FULL_CALIBRATION_SEQUENCE (0x03) on axisID's: " + str(axisID_M0))
# Import the message that should be sent
msg_0 = db.get_message_by_name('Set_Axis_State')
# Encode message, using format 'Command': ENUM (from odrive.enums)
data_0 = msg_0.encode({'Axis_Requested_State': AXIS_STATE_FULL_CALIBRATION_SEQUENCE})
# Update the msg variable to be a CAN message with
msg_0 = can.Message(arbitration_id=msg_0.frame_id | axisID_M0_shifted, is_extended_id=False, data=data_0)

# Print out the encoded message
#print(db.decode_message('Set_Axis_State', msg_0.data_0))
#print(msg_0)

# Calibration sequence for M1
print("\nRequesting AXIS_STATE_FULL_CALIBRATION_SEQUENCE (0x03) on axisID's: " + str(axisID_M1))
msg_1 = db.get_message_by_name('Set_Axis_State')
data_1 = msg_1.encode({'Axis_Requested_State': AXIS_STATE_FULL_CALIBRATION_SEQUENCE})
msg_1 = can.Message(arbitration_id=msg_1.frame_id | axisID_M1_shifted, is_extended_id=False, data=data_1)

# Try to send the CAN message to the bus
try:
    bus.send(msg_0)
    bus.send(msg_1)
    print("Message sent on {}".format(bus.channel_info))
except can.CanError:
    print("Message NOT sent!  Please verify can0 is working first")

print("Waiting for calibration to finish...")

# Read messages infinitely and wait for the right ID to show up
while True:
    msg = bus.recv()
    if msg.arbitration_id == ((axisID_M0_shifted) | db.get_message_by_name('Heartbeat').frame_id):
        current_state = db.decode_message('Heartbeat', msg.data)['Axis_State']
        if current_state == AXIS_STATE_IDLE:
            print("\nAxis has returned to Idle state.")
            break

# Check if any errors were received
for msg in bus:
    if msg.arbitration_id == ((axisID_M0_shifted) | db.get_message_by_name('Heartbeat').frame_id):
        errorCode = db.decode_message('Heartbeat', msg.data)['Axis_Error']
        if errorCode == AXIS_ERROR_NONE:
            print("No errors")
        else:
            print("Axis error!  Error code: "+str(hex(errorCode)))
        break

# Set closed loop control loop
print("\nPutting axis",axisID_M0,"into AXIS_STATE_CLOSED_LOOP_CONTROL (0x08)...")
data = db.encode_message('Set_Axis_State', {'Axis_Requested_State': AXIS_STATE_CLOSED_LOOP_CONTROL})
msg = can.Message(arbitration_id=axisID_M0_shifted | SET_AXIS_REQUESTED_STATE, is_extended_id=False, data=data)
print(msg)

# Try to send the CAN message to the bus
try:
    bus.send(msg)
    print("Message sent on {}".format(bus.channel_info))
except can.CanError:
    print("Message NOT sent!")

# Wait for reply
for msg in bus:
    if msg.arbitration_id == ODRIVE_HEARTBEAT_MESSAGE | axisID_M0_shifted:
        print("\nReceived Axis heartbeat message:")
        msg = db.decode_message('Heartbeat', msg.data)
        print(msg)
        if msg['Axis_State'] == AXIS_STATE_CLOSED_LOOP_CONTROL:
            print("Axis has entered closed loop")
        else:
            print("Axis failed to enter closed loop")
        break

data = db.encode_message('Set_Limits', {'Velocity_Limit':4.0, 'Current_Limit':10.0})
msg = can.Message(arbitration_id=axisID_M0_shifted | SET_LIMITS, is_extended_id=False, data=data)
bus.send(msg)

t0 = time.monotonic()
while True:
    setpoint = 4.0 * math.sin((time.monotonic() - t0)*2)
    print("goto " + str(setpoint))
    data = db.encode_message('Set_Input_Pos', {'Input_Pos':setpoint, 'Vel_FF':0.0, 'Torque_FF':0.0})
    msg = can.Message(arbitration_id=axisID_M0_shifted | SET_INPUT_POS, data=data, is_extended_id=False)
    bus.send(msg)
    time.sleep(0.01)
