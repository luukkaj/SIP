from bluepy.btle import Scanner, DefaultDelegate, UUID, Peripheral, BTLEException
import time
import struct
import sys
import datetime

from cloudpost import *


recognizedServices = dict()
BLE_SERVICE_ENVIRONMENT = "0000181a-0000-1000-8000-00805f9b34fb"
settings_file = ("settings.xml")

def load_recognized_characteristics():
    parsed_file = xml.etree.ElementTree.parse(settings_file).getroot()
    uuid_root = parsed_file.find('uuids')
    chars = []
    for atype in uuid_root.findall('uuid'):
        chars.append(atype.find('name').text)
    print("Parsed UUIDs:\n".format(chars))
    recognizedServices[BLE_SERVICE_ENVIRONMENT] = chars
        
#load_recognized_characteristics()


'''
BLE_CHAR_TEMPERATURE      = "00002a6e-0000-1000-8000-00805f9b34fb"
BLE_CHAR_HUMIDITY               = "00002a6f-0000-1000-8000-00805f9b34fb"


recognizedServices = dict()
recognizedServices[BLE_SERVICE_ENVIRONMENT] = [BLE_CHAR_TEMPERATURE, BLE_CHAR_HUMIDITY]
print("Services dictionary:")
'''
#print(recognizedServices)


class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, device, isNewDev, isNewData):
        if isNewDev:
            print("Discovered device: {}".format(device.addr))
        elif isNewData:
            print("Received new data from: {}".format(device.addr))
 
 
class MyDelegate(DefaultDelegate):
	def __init__(self,params):
		DefaultDelegate.__init__(self)
		self.peripheral = params

	def handleNotification(self, handle, data):
		print("Handle: {}".format(handle))
		if (handle == 0x2C):
			returned_value = struct.unpack('l',data)[0]/10.0
		else:
			returned_value = struct.unpack('h',data)[0]/100.0
		print("Notification from handle: 0x{:02X} with data: {}".format(handle,returned_value))
		tempdict = self.peripheral.availableHandles
		for key, value in tempdict.iteritems():
			#print("Value: {} Handle: {}".format(value, handle))
			if value == (handle+1):
				#print("Found correct handle: {} with UUID: {}".format(handle, key))
				field = self.peripheral.channel.get_field_for_UUID(key)
				#print("Field {}".format(field))
				print("Adding: {},{}".format(field,returned_value))
				self.peripheral.channel.add_to_buffer(field,returned_value)
    
    



def printDeviceNames(devices):
  print("\n\nList of found device names:\n*****************************")
  for dev in devices:
	  #print("Device {} ({}), RSSI={} dB".format(dev.addr, dev.addrType, dev.rssi))
	  #print ("Description: {}".format(dev.getDescription(9)))
    for (adtype, desc, value) in dev.getScanData():
    	if (desc == "Complete Local Name"):
    	  print("Device name: {}".format(value))
        

def scanForDevices():
	scanner = Scanner().withDelegate(DefaultDelegate())#ScanDelegate())
	devices = scanner.scan(4.0)
	return devices;

def scanIAQDevices():
	print("\nScanning for devices....")
	iaq_devices = [];
	devices = scanForDevices()
	for dev in devices:
		for (adtype, desc, value) in dev.getScanData():
			if (desc == "Complete Local Name"):
				if "IAQ" in value:
					iaq_devices.append(dev);
					print("  -{} \t({}) \tRSSI={} dB".format(value, dev.addr, dev.rssi))
	print("Scan complete\n");
	return iaq_devices
  
def printAdvertisingInformation(device):
  for (adtype, desc, value) in device.getScanData():
    print("{}: {}".format(desc, value)) 
  print("Address: {}".format(device.addr))
  print("AddressType: {}".format(device.addrType))
  print("Interfacenumber: {}".format(device.iface))
  print("Signal strength: {}".format(device.rssi))
  print("Device is connectable: {}".format(device.connectable))
  print("Number of recieved packets: {}".format(device.updateCount))
  return True

def getCCCHandle(peripheral, handle):
  for descriptor in peripheral.getDescriptors(handle,handle+1):
    if (descriptor.uuid == 0x2902):                   #      but is not done due to a Bluez/BluePy bug :(     
      return descriptor.handle
  return None



def preparePeripheral(device):
	peripheral = Peripheral(device)#devices[0].addr, devices[0].addrType)
	peripheral.setDelegate(MyDelegate(peripheral))
	Peripheral.availableHandles = {} # Dictionary containing ['UUID' : cccHandle]
	Peripheral.availabeChararacteristics = []
	#peripheral.connect()
	time.sleep(2)

	services = peripheral.getServices()
	for ser in services:
		if ser.uuid in recognizedServices.keys():
			#print("  Found recognized service: {}".format(ser.uuid))
			serChar = ser.getCharacteristics()
			for char in serChar:
				#print("Found char: {}".format(char.uuid))
				if char.uuid in recognizedServices[str(ser.uuid)]:
					handle = char.getHandle()
					#print("   -with recognized charachteristic: {}\t({})".format(char.uuid.getCommonName(),char.uuid))
					#print("      -with handle: 0x{:02X}".format(handle))
					cccHandle = getCCCHandle(peripheral, handle)
					#print ("      -CCC handle: 0x{:02X}".format(cccHandle))
					#peripheral.availableHandles.append(cccHandle)
					peripheral.availableHandles[char.uuid]  = cccHandle
					peripheral.availabeChararacteristics.append(char)

	return peripheral

def readCharacteristicsToBuffer(peripheral):
	for char in peripheral.availabeChararacteristics:
				for uuids in peripheral.channel.supportedUUIDS:
					if uuids['name'] == char.uuid:
						sensor 		= uuids['sensor']
						data_type 	= uuids['data_type']
						factor 			= uuids['factor']
						unit 				= uuids['unit']
						field 			= uuids['field']
				try:
					value = factor*struct.unpack(data_type,char.read())[0]
					peripheral.channel.add_to_buffer(field,value)
				except:
					print("Read of value {} failed.".format(sensor))
				print("  -{}:\t{} {}".format(sensor,value, unit))	



def main():
  load_recognized_characteristics()
  cloud = CloudPost()
  cloud.get_channel_information()
  loop_counter = 0
  while True:
		loop_counter = loop_counter + 1
		# Scan for devices until found
		devices = []
		while not len(devices):
			devices = scanIAQDevices();
		
		# Prepare peripherals
		# Read recognized services and characteristics and enable adding a channel
	  	peripherals = []
	  	print("Preparing peripherals:")
	  	for device in devices:
	  		print(" Peripheral:\t{}".format(device.addr))
	  		try:
				peripherals.append(preparePeripheral(device))
			except:
				print("Failed to prepare peripheral")
				break

		# See if a Thingspeak channel exists for this device
		# Create a new channel if not
		for peripheral in peripherals:
			if peripheral.addr.upper() in cloud.channels.keys():
				peripheral.channel = cloud.channels[peripheral.addr.upper()]
	  		else:
	  			peripheral.channel = cloud.create_channel(peripheral.addr.upper())

		# Read all connected devices characteristics
		# Add them to a buffer and post to the cloud
		print("\n")
		for peripheral in peripherals:
			print(peripheral.addr)
			time.sleep(2);//Wait for the peripheral to write all measurements
			try:
				readCharacteristicsToBuffer(peripheral)
			except:
				print("Failed to read characteristics")
				break

			try:
				print("\n")
				peripheral.channel.post()
				peripheral.disconnect()
			except:
				print("Post failed")
	
			print("Time: {}\n".format(datetime.datetime.now()))
			time.sleep(5*60)



if __name__ == "__main__":
    main()
