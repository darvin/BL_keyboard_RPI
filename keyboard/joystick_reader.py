
import os, struct, array
import evdev
from fcntl import ioctl
from evdev import list_devices, InputDevice, categorize, ecodes
import pprint



DEVICE_CAPABILITY_BUTTONS = 1L
DEVICE_CAPABILITY_AXISES = 3L




class VirtualJoystik:
    def __init__(self):
        self.capability = {}
        self.mapping = {}
        self.last_button = 0
        self.last_axis = 0



    def __add_mapping(self, mapping_type, devices_descriptor):
        if mapping_type not in self.capability:
            self.capability[mapping_type] = []
        if devices_descriptor not in self.mapping:
            self.mapping[devices_descriptor] = {}
        if mapping_type not in self.mapping[devices_descriptor]:
            self.mapping[devices_descriptor][mapping_type] = {}


    def add_buttons(self, devices_descriptor, capability):
        self.__add_mapping(DEVICE_CAPABILITY_BUTTONS, devices_descriptor)
        for hardware_button_name in capability:
            self.last_button += 1
            virtual_button_name = self.last_button
            self.capability[DEVICE_CAPABILITY_BUTTONS] += [virtual_button_name]
            self.mapping[devices_descriptor][DEVICE_CAPABILITY_BUTTONS][hardware_button_name] = virtual_button_name


    def add_axises(self, devices_descriptor, capability):
        self.__add_mapping(DEVICE_CAPABILITY_AXISES, devices_descriptor)
        for hardware_axis_name, axis_abs in capability:
            self.last_axis += 1
            virtual_axis_name = self.last_axis
            self.capability[DEVICE_CAPABILITY_AXISES] += [(virtual_axis_name, axis_abs)]
            self.mapping[devices_descriptor][DEVICE_CAPABILITY_AXISES][hardware_axis_name] = virtual_axis_name

    def get_vaxis(self, device_descriptor, axis_code):
        return self.mapping[device_descriptor][DEVICE_CAPABILITY_AXISES][axis_code]

    def get_vbutton(self, device_descriptor, axis_code):
        return self.mapping[device_descriptor][DEVICE_CAPABILITY_BUTTONS][axis_code]



    def __repr__(self):
        return str(self)

    def __str__(self):
        return "%s \n %s"%(self.capability, self.mapping)


def generate_virtual_joystick_and_device_descriptors_from_all_hardware_joysticks():
    devices = [evdev.InputDevice(dev) for dev in list_devices()]
    devices = [device for device in devices if device.capabilities().get(DEVICE_CAPABILITY_AXISES)]

    vjoy = VirtualJoystik()

    for device in devices:
        print device
        capabilities = device.capabilities()
        for device_capability_key in capabilities:
            if device_capability_key not in [DEVICE_CAPABILITY_BUTTONS, DEVICE_CAPABILITY_AXISES]:
                continue
            capability = capabilities[device_capability_key]

            if device_capability_key == DEVICE_CAPABILITY_BUTTONS:
                vjoy.add_buttons(device.fd, capability)
            if device_capability_key == DEVICE_CAPABILITY_AXISES:
                vjoy.add_axises(device.fd, capability)


    devices_descriptors = {dev.fd: dev for dev in devices}

    return vjoy,devices_descriptors


if __name__=="__main__":
    from select import select
    vjoy,devices_descriptors = generate_virtual_joystick_and_device_descriptors_from_all_hardware_joysticks()
    def main_loop():
        while True:
            r, w, x = select(devices_descriptors, [], [])
            for fd in r:
                for event in devices_descriptors[fd].read():
                    time, value, type, code = event.timestamp(), event.value, event.type, event.code

                    if type & 0x80:
                        print "(initial)",

                    

                    if type & 0x02:
                        print "%s: %.3f" % (vjoy.get_vaxis(fd, code), value)
                    elif type & 0x01:
                        if value:
                            print "%s pressed" % (vjoy.get_vbutton(fd, code))
                        else:
                            print "%s released" % (vjoy.get_vbutton(fd, code))

    main_loop()

