import json
import os
import requests
import re

class Item:
    def __init__(self, name, file_path, enabled):
        self.name = name
        self.image = file_path
        self.enabled = enabled
    

class ItemManager:
    def __init__(self,item_file="items.json"):
        self.item_file = item_file
        self.items = [] # list of Item objects
        self.items_raw = {} # just dict

        if os.path.exists(item_file):
            with open(item_file, 'r') as f:
                json_items = json.load(f)
                for key,val in json_items.items():
                    self.items.append(Item(key, val['image'],val['enabled']))
        
    def add_item(self, item_name, item_image, enabled=False):
        self.items.append(Item(item_name,item_image,enabled))
        

    def get_items(self):
        return self.items

    def enabled_items(self):
        return [item for item in self.items if item.enabled]


    def print_items(self):
        print(self.items)

    def save_items(self):

        output = dict()
        for item in self.items:
            output[item.name] = {}
            output[item.name]['image'] = item.image
            output[item.name]['enabled'] = item.enabled
        with open(self.item_file, 'w') as f:
            json.dump(output, f, sort_keys=True, indent=4)




# running as a script allows generating items.json from items.txt
if __name__ == "__main__":
    i = ItemManager()
    image_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "images", "items")
    print(image_dir)
    with open("items.txt") as items_file:
        for item in items_file:
            item = item.strip()
            i.add_item(item, item.replace(" ", "_").lower()+".png" ,True)
    i.save_items()