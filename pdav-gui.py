#!/usr/bin/env python3

# stdlib imports
import signal
import sys
import subprocess
import os
import json
import shutil

# pip package imports
import FreeSimpleGUI as sg # pip:FreeSimpleGui
import pulsectl # pip:pulsectl

# local imports
from pdav import get_save_file, get_quirks_file, apply_quirks, ident

def _signal_handler(sig, frame):
        sys.exit(0)

def call(cmd):
    return subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0].decode("utf8")

class PDAVGui():
    __VERSION__ = "0.2.0"
    __CALLS__ = {
        "status" : ["systemctl", "--user", "status", "pdav.service"],
        "reload" : ["systemctl", "--user", "daemon-reload"],
        "restart"  : ["systemctl", "--user", "--now", "restart", "pdav.service"],
        "start"  : ["systemctl", "--user", "--now", "enable", "pdav.service"],
        "stop"  : ["systemctl", "--user", "--now", "disable", "pdav.service"]
    }

    def __init__(self):
        # setup signal handlers
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)
        if os.path.exists(os.path.join(os.path.dirname(__file__), ".git")) == True and shutil.which("git") is not None:
            self.__VERSION__ = subprocess.Popen(["bash", "-c", "git describe --long --tags"], stdout=subprocess.PIPE).communicate()[0].decode("utf8")
        self.pa_client = pulsectl.Pulse("pdav-gui")
        self.save_file = get_save_file()
        self.default_save = {
            "applications" : {},
            "ignores" : {
                "devies" : [],
                "applications": {}
            },
            "last_default_sink" : "default_sink_input"
        }

        self._is_user_service_installed = os.path.exists("/etc/systemd/user/pdav.service")
        # setup window style
        sg.change_look_and_feel("DarkGrey11")
    
    def load_save(self):
        default_sink_input = self.pa_client.server_info().default_sink_name
        # default empty save & config
        save = self.default_save
        # parse pdav-config.json if possible and overwrite default save
        if os.path.exists(self.save_file) == True:
            with open(self.save_file, "r", encoding="utf8") as f:
                try:
                    save = json.loads(f.read())
                except json.JSONDecodeError:
                    print(f"[PDAV] cant parse json save file '{self.save_file}'")
        try:
            save["ignores"]
        except KeyError:
            save["ignores"] = {}
        try:
            save["ignores"]["devices"]
        except KeyError:
            save["ignores"]["devices"] = []
        try:
            save["ignores"]["applications"]
        except KeyError:
            save["ignores"]["applications"] = {}
        
        return save
        

    def _main_menu(self):
        layout = [
            [sg.Button("Manage systemd user service", key="user_service", size=(25, 2))],
            [sg.Button("Manage device ignores", key="device_ignores", size=(25, 2))],
            [sg.Button("Manage application ignores", key="app_ignores", size=(25, 2))],
            [sg.Button("Exit", key="Exit", size=(25, 2))]
        ]
        self.mainmenu = sg.Window(f"PDAV Gui {self.__VERSION__}", layout, finalize=True)
        while True:
            event, value = self.mainmenu.read()
            if event == "Exit":
                break
            if event in (None, "Exit"):
                break
            if event == "user_service":
                self.mainmenu.hide()
                self._user_service_menu()
                self.mainmenu.UnHide()
            if event == "device_ignores":
                self.mainmenu.hide()
                self._device_ignores_menu()
                self.mainmenu.UnHide()
            if event == "app_ignores":
                self.mainmenu.hide()
                self._application_ignores_menu()
                self.mainmenu.UnHide()

        self.mainmenu.close()
    
    def _user_service_menu(self):
        layout = [
            [sg.Text(f"PDAV systemd user service installed: {"Yes" if self._is_user_service_installed == True else "No"}")],
            [
                sg.Button("Start service", key="start_service", size=(15, 1)),
                sg.Button("Stop service", key="stop_service", size=(15, 1)),
                sg.Button("Restart service", key="restart_service", size=(15, 1)),
                sg.Button("Refresh status", key="refresh_service", size=(15, 1))
            ],
            [sg.Output(size=(80, 20), key="Out")],
            [sg.Button("Exit", key="Exit", size=(15, 1))]
        ]
        self.userservicemenu = sg.Window(f"PDAV Gui :: systemd user service", layout, finalize=True)
        self.userservicemenu["refresh_service"].Update(disabled=(self._is_user_service_installed == False))
        self.userservicemenu["restart_service"].Update(disabled=(self._is_user_service_installed == False))
        self.userservicemenu["start_service"].Update(disabled=(self._is_user_service_installed == False))
        self.userservicemenu["stop_service"].Update(disabled=(self._is_user_service_installed == False))
        once = False
        while True:
            if self._is_user_service_installed == True and once == False:
                print("PDAV systemd user service status:\n")
                print(call(self.__CALLS__["status"]))
                once = True
            event, value = self.userservicemenu.read()
            if event == "Exit":
                self.userservicemenu.close()
                break
            if event in (None, "Exit"):
                self.userservicemenu.close()
                break
            if event == "refresh_service":
                self.userservicemenu["Out"].Update("")
                print("PDAV systemd user service status:\n")
                print(call(self.__CALLS__["status"]))
            if event == "start_service":
                self.userservicemenu["Out"].Update("")
                print("PDAV systemd user service starting:\n")
                print(call(self.__CALLS__["reload"]))
                print(call(self.__CALLS__["start"]))
                print("PDAV systemd user service status:\n")
                print(call(self.__CALLS__["status"]))
            if event == "restart_service":
                self.userservicemenu["Out"].Update("")
                print("PDAV systemd user service restarting:\n")
                print(call(self.__CALLS__["reload"]))
                print(call(self.__CALLS__["restart"]))
                print("PDAV systemd user service status:\n")
                print(call(self.__CALLS__["status"]))
            if event == "stop_service":
                self.userservicemenu["Out"].Update("")
                print("PDAV systemd user service stopping:\n")
                print(call(self.__CALLS__["stop"]))
                print("PDAV systemd user service status:\n")
                print(call(self.__CALLS__["status"]))

    def _device_ignores_menu(self):
        save = self.load_save()
        layout = [
            [sg.Text("", key="status")],
            [sg.Text("Ignored Devices:")]
        ]
        keys = []
        for sink in self.pa_client.sink_list():
            keys.append(f"dev_ignore_{sink.name}")
            layout.append(
                [sg.Checkbox("", key=f"dev_ignore_{sink.name}", default=True if sink.name in save["ignores"]["devices"] else False, enable_events=True), sg.Text(f"{sink.description} ({sink.name})")]
            )
        layout.append(
            [sg.Button("Save device ignores", key="save", size=(15, 1)), sg.Button("Exit", key="Exit", size=(15, 1))]
        )
        self.deviceignoresmenu = sg.Window(f"PDAV Gui :: device ignores", layout, finalize=True)
        while True:
            event, value = self.deviceignoresmenu.read()
            self.deviceignoresmenu["status"].Update("")
            if event == "Exit":
                self.deviceignoresmenu.close()
                break
            if event in (None, "Exit"):
                self.deviceignoresmenu.close()
                break
            if event == "save":
                # write save to disk
                new_dev = []
                for key in keys:
                    if value[key] == True and key[11:] not in save["ignores"]["devices"]:
                        new_dev.append(key[11:])
                save["ignores"]["devices"] = new_dev
                with open(self.save_file, "w", encoding="utf8") as f:
                    f.write(json.dumps(save, indent=4, ensure_ascii=False))
                self.deviceignoresmenu["status"].Update("Device ignores saved!")
    
    def _application_ignores_menu(self):
        run = True
        while run == True:
            save = self.load_save()
            layout = [
                [sg.Text("", key="status")],
                [sg.Text("Only Applications currently outputting audio or already on the application ignore list can be managed!")],
                [sg.Button("Refresh applications", key="refresh_applications"), sg.Button("Save device ignores", key="save", size=(15, 1)), sg.Button("Exit", key="Exit", size=(15, 1))],
                [sg.Text("Application ignores:")]
            ]
            keys = {}
            for k, v in save["ignores"]["applications"].items():
                layout.append(
                    [sg.Checkbox("", default=True, key=f"app_ignore_{k}", enable_events=True), sg.Text(f"{v["application.name"]} ({v["application.process.binary"]})")]
                )
                keys[f"app_ignore_{k}"] = v
            for sink in self.pa_client.sink_input_list():
                proplist = apply_quirks(sink.proplist)
                k = ident(proplist)
                if k not in save["ignores"]["applications"].keys():
                    layout.append(
                        [sg.Checkbox("", default=False, key=f"app_ignore_{k}", enable_events=True), sg.Text(f"{proplist["application.name"]} ({proplist["application.process.binary"]})")]
                    )
                    keys[f"app_ignore_{k}"] = {
                        "application.name" : proplist["application.name"],
                        "application.process.binary" : proplist["application.process.binary"]
                    }
            self.applicationignoresmenu = sg.Window(f"PDAV Gui :: application ignores", layout, finalize=True)
            while True:
                event, value = self.applicationignoresmenu.read()
                self.applicationignoresmenu["status"].Update("")
                if event == "refresh_applications":
                    self.applicationignoresmenu.close()
                    break
                if event == "Exit":
                    run = False
                    self.applicationignoresmenu.close()
                    break
                if event in (None, "Exit"):
                    run = False
                    self.applicationignoresmenu.close()
                    break
                if event == "save":
                    new_app = {}
                    for k, v in keys.items():
                        if value[k] == True:
                            new_app[k[11:]] = v
                    save["ignores"]["applications"] = new_app
                    # write save to disk
                    with open(self.save_file, "w", encoding="utf8") as f:
                        f.write(json.dumps(save, indent=4, ensure_ascii=False))
                    self.applicationignoresmenu["status"].Update("Application ignores saved!")


if __name__ == "__main__":
    PDAVGui()._main_menu()
