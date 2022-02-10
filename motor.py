from cmd_id_enums import *
from odrive.enums import *
import can
import cantools

class Motor:
  def __init__(self, axisID):
    self.axisID = axisID
    self.axisID_shifted = self.axisID << 5

  def init(self):
    # Calibration sequence for motors
    print("\nRequesting AXIS_STATE_FULL_CALIBRATION_SEQUENCE (0x03) on axisID's: " + str(self.axisID))
    # Import the message that should be sent
    msg = db.get_message_by_name('Set_Axis_State')
    # Encode message, using format 'Command': ENUM (from odrive.enums)
    data = msg.encode({'Axis_Requested_State': AXIS_STATE_FULL_CALIBRATION_SEQUENCE})
    # Update the msg variable to be a CAN message with
    msg_0 = can.Message(arbitration_id=msg.frame_id | self.axisID_shifted, is_extended_id=False, data=data)
