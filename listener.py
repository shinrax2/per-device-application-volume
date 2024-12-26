import pulsectl
import concurrent.futures
import apply
import signal
import sys
import os
import time

os.chdir(os.path.dirname(__file__))

def signal_handler(sig, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

with pulsectl.Pulse("per-device-application-volume_listener") as pulse:
  def event_handler(ev):
    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.submit(apply.run(mute=True))
    raise pulsectl.PulseLoopStop

  pulse.event_mask_set('sink_input')
  pulse.event_callback_set(event_handler)
  while True:
    pulse.event_listen()
    time.sleep(0.1)
