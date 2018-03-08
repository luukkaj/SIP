import xml.etree.ElementTree
import requests
import socket
from time import gmtime, strftime


class Channel():
    def __init__(self, api_key, name, address, ID):
        self.settings_file = "settings.xml"
        self.api_key = api_key
        self.supportedUUIDS = []
        self.name = name
        self.description = address
        self.buffer = []
        self.api_post_url = None
        self.load_settings()
        self.id = ID;
        self.load_uuids()

    def add_to_buffer(self, field, value):
        self.buffer.append({'field': str(field), 'value': value})

    def post(self):
        print("Send read data to cloud")
        data = {'api_key': self.api_key}
        for pair in self.buffer:
            data['field' + pair['field']] = pair['value']
        try:
            r = requests.post(self.api_post_url, data)
            print("Response before json:\n{}".format(r))
            response = r.json()
            self.buffer = []
        except requests.exceptions.ConnectionError as e:
            print('Connection Error')
            response = e
        print("\nRESPONSE #")
        print(response)
        print("\n")
    
    def get_field_for_UUID(self, uuid):
      for a in self.supportedUUIDS:
        #print("a: {} uuid: {}".format(a,uuid))
        if a['name'] == uuid:
          return a['field']
      return None

    def load_uuids(self):
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
            self.supportedUUIDS.append(new_uuid)    

    def load_settings(self):
        parsed_file = xml.etree.ElementTree.parse(self.settings_file).getroot()
        # Load thingspeak settings
        #server_element = parsed_file.find('server')
        thingspeak_element = parsed_file.find('thingspeak')
        post_address_element = thingspeak_element.find('post_address')
        self.api_post_url = post_address_element.text

        '''# Load RF-SensIt settings
        server_element = parsed_file.find('server')
        rfsensit_element = server_element.find('rfsensit_tcp')
        self.TCP_IP = rfsensit_element.find('post_address').text
        self.TCP_PORT = int(rfsensit_element.find('post_port').text)
        self.BUFFER_SIZE = int(rfsensit_element.find('post_buffer_size').text)
        '''

