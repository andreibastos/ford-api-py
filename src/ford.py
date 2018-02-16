# -*- coding: utf-8 -*-
"""
author: Andrei Bastos
organization: Labic/Ufes
data: 19/01/2018
"""

from enum import Enum
import json, os

import subprocess, threading

query = {
    "source": "twitter",
    "type": "flashback",
    "flashback_data": "tweets",
    "arguments": {        
        "terms": "dilma",
        "max_days": 5,
        "max_number": 10,
        "since_id": "15155345_56595951",
        "max_id": "-1",
        "language": "pt",
        "geocodes": {
            "lat": -20.351,
            "long": -40.175,
            "radius": 100
        },
        "filters": {
            "is_reverse": True,
            "terms": [
                {
                    "status.text": "não"
                },
                {
                    "status.user.screen_name": "andreibastos"
                }
            ]}
    }
}

class Twitter(threading.Thread):
    def __init__(self, collect_type, arguments):
        threading.Thread.__init__(self)
        self.arguments = arguments
        self.collect_type = collect_type
    
    @staticmethod
    def make_arguments(arguments):
        arguments_str = ""        
        for argument in arguments.keys():
            if arguments.get(argument):
                arguments_str = arguments_str + " --" +argument + " "+ str(arguments.get(argument))
        return arguments_str

    @classmethod
    def terms(cls):
        arguments_str = cls.make_arguments(self.arguments)
        command = "ford -t --twitter-data tweets -o {0} {1} -n 100 -q".format(arguments.get("output"),arguments_str )
        print(command)
        try:
            self.process = execute_command(command)
        except Exception as identifier:
            print(identifier)

    @classmethod
    def tweet_ids(cls):
        arguments_str = cls.make_arguments(self.arguments)
        command = "ford -t --twitter-data tweets-ids -o {0} {1} -n 100 -q".format(arguments.get("output"),arguments_str )
        print(command)
        try:
            self.process = execute_command(command)
        except Exception as identifier:
            print(identifier)

    @classmethod    
    def timelines(cls):
        arguments_str = cls.make_arguments(self.arguments)
        command = "ford -t --twitter-data timelines -o {0} {1} -n 100 -q".format(arguments.get("output"),arguments_str )
        print(command)
        try:
            self.process = execute_command(command)
        except Exception as identifier:
            print(identifier)
        
    @classmethod
    def timelines(cls):
        arguments_str = cls.make_arguments(self.arguments)
        command = "ford -t --twitter-data timelines -o {0} {1} -n 100 -q".format(arguments.get("output"),arguments_str )
        print(command)
        try:
            self.process = execute_command(command)
        except Exception as identifier:
            print(identifier)
    
    @classmethod
    def users(cls):
        arguments_str = cls.make_arguments(self.arguments)
        command = "ford -t --twitter-data users -o {0} {1} -n 100 -q".format(arguments.get("output"),arguments_str )
        print(command)
        try:
            self.process = execute_command(command)
        except Exception as identifier:
            print(identifier)

    @classmethod
    def friends(cls):
        arguments_str = cls.make_arguments(self.arguments)
        command = "ford -t --twitter-data friends -o coletas/{0} {1} -n 100 -q".format(arguments.get("output"),arguments_str )
        print(command)
        try:
            self.process = execute_command(command)
        except Exception as identifier:
            print(identifier)

    @classmethod        
    def followers(cls):
        arguments_str = cls.make_arguments(self.arguments)
        command = "ford -t --twitter-data followers -o {0} {1} -n 100 -q".format(arguments.get("output"),arguments_str )
        print(command)
        try:
            self.process = execute_command(command)
        except Exception as identifier:
            print(identifier)

    @classmethod
    def retweets(cls):
        arguments_str = cls.make_arguments(self.arguments)
        command = "ford -t --twitter-data retweets -o {0} {1} -n 100 -q".format(arguments.get("output"),arguments_str )
        try:
            self.process = execute_command(command)
        except Exception as identifier:
            print(identifier)
        
    def stop():
        pass

    def run(self):
        if self.collect_type is "collect":
            data = self.arguments.get("data")
            if data is "terms":
                self.terms()                
            elif data is "tweet_ids":
                self.tweet_ids()                
            elif data is "timelines":
                self.timelines()                
            elif data is "users":
                self.users()                
            elif data is "friends":
                self.friends()                
            elif data is "followers":
                self.followers()
            elif data is "retweets":
                self.retweets()                
        elif self.collect_type is "stream":
            self.stream()
        elif self.collect_type is "replies":
            self.replies()
        elif self.collect_type is "scrap":
            self.scrap()
    
def execute_command(command):    
    print(command)
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        output, error = process.communicate()
        return process        
    except Exception as identifier:
        raise identifier
        
arguments1 = {"input":"dilma", "output":"coletas/dilma", "data":"terms", "minimum":None, "maximum":None, "days":1, "geocodes":[], "lang":"pt", "number":None}
arguments2 = {"input":"lula", "output":"coletas/lula", "data":"tweet_ids", "minimum":None, "maximum":None, "days":1, "geocodes":[], "lang":"pt", "number":None}
arguments3 = {"input":"enem", "output":"coletas/enem", "data":"timelines", "minimum":None, "maximum":None, "days":1, "geocodes":[], "lang":"pt", "number":None}
arguments4 = {"input":"dica", "output":"coletas/dica", "data":"friends", "minimum":None, "maximum":None, "days":1, "geocodes":[], "lang":"pt", "number":None}
arguments5 = {"input":"wifi", "output":"coletas/wifi", "data":"followers", "minimum":None, "maximum":None, "days":1, "geocodes":[], "lang":"pt", "number":None}
arguments6 = {"input":"politica", "output":"coletas/politica", "data":"retweets", "minimum":None, "maximum":None, "days":1, "geocodes":[], "lang":"pt", "number":None}
arguments7 = {"input":"agua", "output":"coletas/agua", "data":"replies", "minimum":None, "maximum":None, "days":1, "geocodes":[], "lang":"pt", "number":None}



coleta1 = Twitter("collect", arguments1)
coleta2 = Twitter("collect", arguments2)
coleta3 = Twitter("collect", arguments3)
coleta4 = Twitter("collect", arguments4)
coleta5 = Twitter("collect", arguments5)
coleta6 = Twitter("collect", arguments6)
coleta7 = Twitter("collect", arguments7)

coleta1.start()
coleta2.start()
coleta3.start()
coleta4.start()
coleta5.start()
coleta6.start()
coleta7.start()

minhas_threads = [coleta1,coleta2,coleta3,coleta4,coleta5,coleta6,coleta7]

for minha_thread in minhas_threads:
    minha_thread.join()
