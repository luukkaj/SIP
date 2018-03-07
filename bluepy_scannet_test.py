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
        
load_recognized_characteristics()


'''
BLE_CHAR_TEMPERATURE      = "00002a6e-0000-1000-8000-00805f9b34fb"
BLE_CHAR_HUMIDITY               = "00002a6f-0000-1000-8000-00805f9b34fb"


recognizedServices = dict()
recognizedServices[BLE_SERVICE_ENVIRONMENT] = [BLE_CHAR_TEMPERATURE, BLE_CHAR_HUMIDITY]
print("Services dictionary:")
'''
print(recognizedServices)


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
	scanner = Scanner().withDelegate(ScanDelegate())
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
    	    print("Found IAQ device!")
    	    iaq_devices.append(dev);
    	    print("Address: {}\nDevice name: {}\nSignal strength: {}".format(dev.addr, value, dev.rssi))
  print("Scan complete");
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
  #peripheral.connect()
  time.sleep(2)
  
  services = peripheral.getServices()
  print("Services:\n".format(services))
  for ser in services:
    if ser.uuid in recognizedServices.keys():
      print("Found recognixed service: {}".format(ser.uuid))
      serChar = ser.getCharacteristics()
      for char in serChar:
        if char.uuid in recognizedServices[str(ser.uuid)]:
          handle = char.getHandle()
          print("  -with recognized charachterisit: {}".format(char.uuid))
          print("     -with handle: 0x{:02X}".format(handle))
          cccHandle = getCCCHandle(peripheral, handle)
          print ("     -CCC handle: 0x{:02X}".format(cccHandle))
          #peripheral.availableHandles.append(cccHandle)
          peripheral.availableHandles[char.uuid]  = cccHandle
      
  return peripheral



#print("\nPrinting all information:")

#printAdvertisingInformation(devices[0])
          
#peripheral.writeCharacteristic(TempCCC, struct.pack('<bb',0x01,0x00))
#peripheral.writeCharacteristic(HumCCC, struct.pack('<bb',0x01,0x00))
#print("Notification turned on for: Temp")
def main():
  devices = scanIAQDevices();
  print("Devices: {}".format(devices))
  print("Device: {}".format(devices[0]))

  peripherals = []
  peripherals.append(preparePeripheral(devices[0]))
  cloud = CloudPost()
  cloud.get_channel_information()
  
  #print ("Cloud.channels: {}".format(cloud.channels))
  #print("User api key: {}".format(cloud.user_api_key))
  
  #print("Channels:\n{}".format(cloud.channels))
  
  for peripheral in peripherals:
    if peripheral.addr.upper() in cloud.channels.keys():
      #print("\n\nCorrect device found!\n")
      peripheral.channel = cloud.channels[peripheral.addr.upper()]
      #print("New channel: {}".format(peripheral.channel))
  
  while True:
    print("Waiting for notifications...")
    for peripheral in peripherals:
      for uuid in peripheral.availableHandles.keys():
        #print("UUID: {}".format(uuid))
        #print("Field for uuid: {}".format(cloud.get_field_for_UUID(uuid)))
        #try:
          
        ccc = peripheral.availableHandles[uuid]
        #print("  CCCHandle: {:02X}".format(ccc))
        
        peripheral.writeCharacteristic(ccc, struct.pack('<bb',0x01,0x00))
        if peripheral.waitForNotifications(4.0):
          continue
        '''
        except:
          print("Disconnected from device. Trying to reconnect...")
          try:
            print("Connecting to device address: {}".format(peripheral.addr))
            peripheral.connect(peripheral.addr,peripheral.addrType)
            time.sleep(5)
          except:
            print("Connection attempt failed")
          '''  
      peripheral.channel.post() 
    print("Time: {}".format(datetime.datetime.now()))
    time.sleep(60*15)
    
if __name__ == "__main__":
    main()
