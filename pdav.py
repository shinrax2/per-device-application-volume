import pulsectl
import concurrent.futures
import signal
import sys
import os
import time
import hashlib
import json

def ident( proplist):
        ident = hashlib.shake_128()
        ident.update(proplist["application.name"].encode("utf-8"))
        ident.update(proplist["application.process.binary"].encode("utf-8"))
        return ident.hexdigest(16)

def run(mute=False):    
    SAVE_FILE = os.path.join(os.path.dirname(__file__), "save.json")
    pa_client = pulsectl.Pulse("per-device-application-volume")
    default_sink_input = pa_client.server_info().default_sink_name
    save = {
        "applications" : {},
        "last_default_sink" : default_sink_input
    }
    if os.path.exists(SAVE_FILE) == True:
        with open(SAVE_FILE, "r", encoding="utf8") as f:
            save = json.loads(f.read())
    
    for sink in pa_client.sink_input_list():
      vol = pa_client.volume_get_all_chans(sink)
      try:
          save["applications"][ident(sink.proplist)]["volumes"][default_sink_input] = vol
      except KeyError:
          # no data for application
          save["applications"][ident(sink.proplist)] = {"volumes": {default_sink_input : vol}}
    
    for sink in pa_client.sink_input_list():
      try:
          vol = save["applications"][ident(sink.proplist)]["volumes"][default_sink_input]
          if pa_client.volume_get_all_chans(sink) != vol and save["last_default_sink"] != default_sink_input:
              pa_client.volume_set_all_chans(sink, vol)
          if mute == False:
              print(f"volume for application '{sink.proplist["application.name"]}' on device '{default_sink_input}' set to {vol*100}%!")
      except KeyError:
          if mute == False:
              print(f"no volume for application '{sink.proplist["application.name"]}' on device '{default_sink_input}' set!")
    save["last_default_sink"] = default_sink_input
    with open(SAVE_FILE, "w", encoding="utf8") as f:
        f.write(json.dumps(save, indent=4, ensure_ascii=False))
    pa_client.close()

def signal_handler(sig, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

with pulsectl.Pulse("per-device-application-volume_listener") as pulse:
  def event_handler(ev):
    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.submit(run(mute=True))
    raise pulsectl.PulseLoopStop

  pulse.event_mask_set('sink_input')
  pulse.event_callback_set(event_handler)
  while True:
    pulse.event_listen()
    time.sleep(0.1)
