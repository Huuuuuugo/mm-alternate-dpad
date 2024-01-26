# source: https://stackoverflow.com/questions/43414189/how-can-i-use-xinput-in-python-without-pygame-to-sniff-button-presses-on-the
# source: https://pastebin.com/8KDYbpaj

from __future__ import absolute_import, division
from itertools import count
from operator import itemgetter
import ctypes
 
from xinput import XInputJoystick, get_bit_values, XINPUT_GAMEPAD
 
 
class GamepadControls(XInputJoystick):
    """Wrapper for the XInputJoystick class to avoid using events."""
    
    def __init__(self, *args, **kwargs):
        try:
            device_number = args[0].device_number
        except (IndexError, AttributeError):
            raise ValueError('use the result from GamepadControls.list_gamepads() to initialize the class')
        super(GamepadControls, self).__init__(device_number, *args[1:], **kwargs)
 
    @classmethod
    def list_gamepads(self):
        """Return a list of gamepad objects."""
        return [self(gamepad) for gamepad in self.enumerate_devices()]
 
    def __enter__(self):
        """Get the current state."""
        self._state = self.get_state()
        return self
 
    def __exit__(self, *args):
        """Record the last state."""
        self._last_state = self._state
    
    def get_axis(self, dead_zone=1024):
        """Return a dictionary of any axis based inputs."""
        result = {}
        axis_fields = dict(XINPUT_GAMEPAD._fields_)
        axis_fields.pop('buttons')
        for axis, type in list(axis_fields.items()):
            old_val = getattr(self._last_state.gamepad, axis)
            new_val = getattr(self._state.gamepad, axis)
            data_size = ctypes.sizeof(type)
            old_val = int(self.translate(old_val, data_size) * 65535)
            new_val = int(self.translate(new_val, data_size) * 65535)
 
            #Detect when to send update
            movement = old_val != new_val and abs(old_val - new_val) > 1
            is_trigger = axis.endswith('trigger')
            in_dead_zone = abs(new_val) < dead_zone
            if movement and (not in_dead_zone or new_val == 0):
                result[axis] = new_val
            
        return result
        
    def get_button(self):
        """Return a dictionary of any button inputs."""
        changed = self._state.gamepad.buttons ^ self._last_state.gamepad.buttons
        changed = get_bit_values(changed, 16)
        buttons_state = get_bit_values(self._state.gamepad.buttons, 16)
        changed.reverse()
        buttons_state.reverse()
        button_numbers = count(1)
        changed_buttons = list(list(zip(changed, button_numbers, buttons_state))) # list(filter(itemgetter(0), list(zip(changed, button_numbers, buttons_state))))
        
        result = {}
        for changed, number, pressed in changed_buttons:
            result[number] = pressed
        return result
 
 
if __name__ == '__main_':
    import time
 
    #Example usage
    gamepads = GamepadControls.list_gamepads()
    while True:
        for gamepad in gamepads:
            with gamepad as gamepad_input:
                for axis, amount in gamepad_input.get_axis().items():
                    print(axis, amount)
                for button, state in gamepad_input.get_button().items():
                    print(button, state)
                    input()
        time.sleep(1/60)


if __name__ == '__main__':
    import time
 
    #Example usage
    gamepads = GamepadControls.list_gamepads()
    while True:
        for gamepad in gamepads:
            with gamepad as gamepad_input:
                print(gamepad_input.get_axis())
                print(gamepad_input.get_button())
                # input()
        time.sleep(1/60)