import xml.etree.ElementTree





class definedCharacteristic(self)
  def __init__(self, api_key, name, address, ID):
        self.settings_file = "settings.xml"
        self.self.load_characteristics()
        self.characteristics = []
        
    def load_characteristics:
        parsed_file = xml.etree.ElementTree.parse(self.settings_file).getroot()
        uuid_root = parsed_file.find('uuids')
        for atype in uuid_root.findall('uuid'):
            new_uuid = {}
            new_uuid['name'] = atype.find('name').text
            new_uuid['sensor'] = atype.find('sensor').text
            new_uuid['location'] = atype.find('location').text
            new_uuid['data_type'] = atype.find('data_type').text
            new_uuid['field'] = int(atype.find('field').text)
            new_uuid['factor'] =  float(atype.find('factor').text)
            new_uuid['unit'] =  atype.find('unit').text
            self.loaded_uuids.append(new_uuid)
            
class definedCharacteristic(self):
  def __init__(self, uuid, handle):
        self.uuid = uuid
        self.self.load_characteristics()
        self.characteristics = []
