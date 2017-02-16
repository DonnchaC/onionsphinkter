#
# hooks will be executed when the corresponding event occurs
# 
import logging

def open_hook():
   pass

def closed_hook():
    pass

def failure_hook():
    pass

def timer_hook(status):
    pass
    #try:
    #    requests.post(url, data=json.dumps(data), headers=headers)
    #except Exception:
    #	pass
 
    #logging.info("finishing timer_hook")
