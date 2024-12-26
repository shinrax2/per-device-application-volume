import pulsectl
import os
import json
import signal
import sys

os.chdir(os.path.dirname(__file__))

def run(mute=False):
    def signal_handler(sig, frame):
        print('exiting!')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    save = {
        "applications" : {} 
    }
    SAVE_FILE = "save.json"
    pa_client = pulsectl.Pulse("per-device-application-volume")
    default_sink_input = pa_client.server_info().default_sink_name
    if os.path.exists(SAVE_FILE) == True:
        with open(SAVE_FILE, "r") as f:
            save = json.loads(f.read())

    for sink in pa_client.sink_input_list():
        try:
            vol = save["applications"][sink.proplist["application.name"]]["volumes"][default_sink_input]
            pa_client.volume_set_all_chans(sink, vol)
            if mute == False:
                print(f"volume for application '{sink.proplist["application.name"]}' on device '{default_sink_input}' set to {vol*100}%!")
        except KeyError:
            if mute == False:
                print(f"no volume for application '{sink.proplist["application.name"]}' on device '{default_sink_input}' set!")
    pa_client.close()

if __name__ == '__main__':
    run()