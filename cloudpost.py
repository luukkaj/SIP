import requests
import json
import xml.etree.ElementTree

# Own modules
from channel import *

class CloudPost(object):

    def __init__(self):
        print("Init cloud connection")
        self.channels = {}
        self.fields = {}
        
        # Urls
        self.get_channel_info_url = ''#'https://api.thingspeak.com/channels.json?api_key=' + self.user_api_key
        self.create_channel_url = ''#'https://api.thingspeak.com/channels.json'
        self.api_post_url = ''#'https://api.thingspeak.com/update.json'
        
        self.settings_file = 'settings.xml'
        self.load_settings()

        # Variables
        self.account_info = None

    def create_channel(self, address):
        # parsed_address = address.replace(":", "")

        data = {'api_key': self.user_api_key,  'name' : 'IAQP device: ' + address, 'description': address} 
        print("Data before updating:\n{}".format(data));
        print("self.fields before updating:\n{}".format(self.fields));
        data.update(self.fields)
        print("Creating channel with data:\n{}".format(data))
        try:
            r = requests.post(self.create_channel_url, data)
            print(r)
            response = r.json()
            print(response)
            self.parse_channel_info(response)
            return self.channels[address]
            
        except requests.exceptions.ConnectionError as e:
            print('Connection Error')
            response = e
        print("\nRESPONSE #")
        print(response)
        print("\n")
        return None

    def get_channel_information(self):
        try:
            r = requests.get(self.get_channel_info_url)
            response = r.json()
            if response == 0:
                print("Channel information request failed!")
                return
            elif len(response) == 0:
                print("No available channels")
                return
            else:
                print("Channel info request succesfull!")
                #self.account_info = json.loads(response)
                #self.account_info_pretty_print = json.dumps(response, indent=4, sort_keys=True)
                self.parse_channel_info(response)

        except requests.exceptions.ConnectionError as e:
            print('Cloud connection Error\n')
            response = e

    def parse_channel_info(self, response):

        self.channels = {}
        print("Parsing ---------------")
        #print(response)
        
        single_channel = False
        for i in response:
            if i == "name":
                print("Only one channel")
                single_channel = True
        #print(response['name'])
        if single_channel == True:
            if "IAQ" in response['name']:
                new_channel = Channel(str(response['api_keys'][0]['api_key']), response['name'], response['description'], response['id'])
                self.channels[response['description']] = new_channel
                print("new channel parsed")
                single_channel = False
        else:
            for iter_channel in response:
                print(iter_channel)
                if "IAQP device" in iter_channel['name']:
                    new_channel = Channel(str(iter_channel['api_keys'][0]['api_key']), iter_channel['name'], iter_channel['description'], iter_channel['id'])
                    self.channels[iter_channel['description']] = new_channel
                    

    

    def print_channel_info(self):
        if self.channel_info != None:
            print(self.account_info_pretty_print)
            print("\n")
        else:
            print("Channel info not avaible!\n")

    def load_settings(self):
        parsed_file = xml.etree.ElementTree.parse(self.settings_file).getroot()
        found_keys = parsed_file.find('api_keys')
        self.user_api_key = str(found_keys.find('user_api_key').text)
        
        found_addresses = parsed_file.find('thingspeak')
        self.get_channel_info_url = str(found_addresses.find('info_address').text) + self.user_api_key
        self.create_channel_url = str(found_addresses.find('create_channel_address').text)
        self.api_post_url = str(found_addresses.find('post_address').text)
        
        uuid_root = parsed_file.find('uuids')
        for atype in uuid_root.findall('uuid'):
            new_field = {}
            field = 'field' +  atype.find('field').text
            field_name  = atype.find('sensor').text
            self.fields[field] = field_name
        print("Cloud settings found fields:\n{}".format(self.fields))
        
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
            
            
            
            
