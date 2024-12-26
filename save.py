import pulsectl
import os
import json

def run():
    SAVE_FILE = "save.json"

    pa_client = pulsectl.Pulse("per-device-application-volume")
    default_sink_input = pa_client.server_info().default_sink_name

    if os.path.exists(SAVE_FILE) == True:
        with open(SAVE_FILE, "r", encoding="utf8") as f:
            try:
                save = json.loads(f.read())
            except json.decoder.JSONDecodeError:
                save = {
                    "applications" : {} 
                }

    for sink in pa_client.sink_input_list():
        vol = pa_client.volume_get_all_chans(sink)
        try:
            save["applications"][sink.proplist["application.name"]]["volumes"][default_sink_input] = vol
        except KeyError:
            # no data for application
            save["applications"][sink.proplist["application.name"]] = {"volumes": {default_sink_input : vol}}

    with open(SAVE_FILE, "w", encoding="utf8") as f:
        f.write(json.dumps(save, indent=4, ensure_ascii=False))
    pa_client.close()

if __name__ == '__main__':
    run()