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

def get_data_dir_file(filename):
    # search order: /usr/share/pdav/, ~/.local/share/pdav/, ./
    if os.path.exists(os.path.join("/usr/share/pdav/", filename)) == True:
        return os.path.join("/usr/share/pdav/", filename)
    elif os.path.exists(os.path.join(os.path.expanduser("~/.local/share/pdav/"), filename)) == True:
        return os.path.join(os.path.expanduser("~/.local/share/pdav/"), filename)
    elif os.path.exists(filename) == True:
        return filename
    else:
        return None

def _signal_handler(sig, frame):
        sys.exit(0)

def call(cmd):
    return subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0].decode("utf8")

class l10n():
    __SUPPORTED_LANGS__ = ["en", "de"]

    def __init__(self, fallback_language="en"):
        self.lang_files = {}
        self.fallback_language = fallback_language
        self.language = fallback_language
        self._lang = {}
        self._fallback_lang = {}
        self.fallback = False
        # get language files
        self._get_language_files()
        # get user language
        self.user_language = self._get_user_language()
        # load language files
        if self.user_language != self.fallback_language and self.user_language in self.__SUPPORTED_LANGS__ and self.user_language in self.lang_files.keys():
            self._lang = self._load_language_file(f"l10n/{self.user_language}.json")
            self._fallback_lang = self._load_language_file(f"l10n/{self.fallback_language}.json")
            self.language = self.user_language
        else:
            self._lang = self._load_language_file(f"l10n/{self.fallback_language}.json")
            self._fallback_lang = self._lang
            self.fallback = True

    
    def _get_language_files(self):
        for lang in self.__SUPPORTED_LANGS__:
            file = get_data_dir_file(f"l10n/{lang}.json")
            if file is not None:
                self.lang_files[lang] = file
    
    def _get_user_language(self):
        try:
            if os.environ["LANG"] != "":
                return os.environ["LANG"][:2].lower()
            else:
                return self.fallback_language
        except KeyError:
            return self.fallback_language
    
    def _load_language_file(self, file):
        if os.path.exists(file) == True:
            with open(file, "r", encoding="utf8") as f:
                try:
                    return json.loads(f.read())
                except json.JSONDecodeError:
                    return {}
    
    def get_string(self, key):
        s_fb = None
        try:
            s_fb = self._fallback_lang[key]
        except KeyError: # key not found -> ERROR
            return f"ERROR: '{key}' not found!"
        if self.fallback == True and s_fb is not None:
            return s_fb["string"]
        try:
            s = self._lang[key]
        except KeyError: # key not found in lang -> fallback_lang
            if s_fb is not None:
                return s_fb["string"]
        if s["version"] < s_fb["version"]:
            return s_fb["string"] # string version lower in lang -> fallback_lang
        else:
            return s["string"] # everything alright -> lang 

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
        # use git version if possible
        if os.path.exists(os.path.join(os.path.dirname(__file__), ".git")) == True and shutil.which("git") is not None:
            self.__VERSION__ = subprocess.Popen(["bash", "-c", "git describe --long --tags"], stdout=subprocess.PIPE).communicate()[0].decode("utf8")
        self.pa_client = pulsectl.Pulse("pdav-gui")
        self.save_file = get_save_file()
        self.iconpath = get_data_dir_file("images/icon-64x64.png")
        self.l10n = l10n()
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
                    pass
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
            [sg.Image(source=get_data_dir_file("images/icon-128x128.png"), size=(200, 128))],
            [sg.Text(f'{self.l10n.get_string("gui_version")}: {self.__VERSION__}', justification="center", expand_x=True)],
            [sg.Button(self.l10n.get_string("gui_mainmenu_userservice_btn"), key="user_service", size=(25, 2))],
            [sg.Button(self.l10n.get_string("gui_mainmenu_devignores_btn"), key="device_ignores", size=(25, 2))],
            [sg.Button(self.l10n.get_string("gui_mainmenu_appignores_btn"), key="app_ignores", size=(25, 2))],
            [sg.Button(self.l10n.get_string("gui_exit"), key="Exit", size=(25, 2))]
        ]
        self.mainmenu = sg.Window(self.l10n.get_string("gui_mainmenu_title"), layout, finalize=True, icon=self.iconpath)
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
            [sg.Text(self.l10n.get_string("gui_userservicemenu_serviceinstalled_text").format(self.l10n.get_string('gui_yes') if self._is_user_service_installed == True else self.l10n.get_string('gui_no')))],
            [
                sg.Button(self.l10n.get_string("gui_userservicemenu_startservice_btn"), key="start_service", size=(15, 1)),
                sg.Button(self.l10n.get_string("gui_userservicemenu_stopservice_btn"), key="stop_service", size=(15, 1)),
                sg.Button(self.l10n.get_string("gui_userservicemenu_restartservice_btn"), key="restart_service", size=(15, 1)),
                sg.Button(self.l10n.get_string("gui_userservicemenu_refreshstatus_btn"), key="refresh_service", size=(15, 1))
            ],
            [sg.Output(size=(80, 20), key="Out")],
            [sg.Button(self.l10n.get_string("gui_back"), key="Exit", size=(15, 1))]
        ]
        self.userservicemenu = sg.Window(self.l10n.get_string("gui_userservicemenu_title"), layout, finalize=True, icon=self.iconpath)
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
                print(self.l10n.get_string("gui_userservicemenu_status_line"))
                print(call(self.__CALLS__["status"]))
            if event == "start_service":
                self.userservicemenu["Out"].Update("")
                print(self.l10n.get_string("gui_userservicemenu_start_line"))
                print(call(self.__CALLS__["reload"]))
                print(call(self.__CALLS__["start"]))
                print(self.l10n.get_string("gui_userservicemenu_status_line"))
                print(call(self.__CALLS__["status"]))
            if event == "restart_service":
                self.userservicemenu["Out"].Update("")
                print(self.l10n.get_string("gui_userservicemenu_restart_line"))
                print(call(self.__CALLS__["reload"]))
                print(call(self.__CALLS__["restart"]))
                print(self.l10n.get_string("gui_userservicemenu_status_line"))
                print(call(self.__CALLS__["status"]))
            if event == "stop_service":
                self.userservicemenu["Out"].Update("")
                print(self.l10n.get_string("gui_userservicemenu_stop_line"))
                print(call(self.__CALLS__["stop"]))
                print(self.l10n.get_string("gui_userservicemenu_status_line"))
                print(call(self.__CALLS__["status"]))

    def _device_ignores_menu(self):
        save = self.load_save()
        layout = [
            [sg.Text("", key="status")],
            [sg.Text(self.l10n.get_string("gui_devignoresmenu_ignoreddevices_text"))]
        ]
        keys = []
        for sink in self.pa_client.sink_list():
            keys.append(f"dev_ignore_{sink.name}")
            layout.append(
                [sg.Checkbox("", key=f"dev_ignore_{sink.name}", default=True if sink.name in save["ignores"]["devices"] else False, enable_events=True), sg.Text(f"{sink.description} ({sink.name})")]
            )
        layout.append(
            [sg.Button(self.l10n.get_string("gui_devignoresmenu_save_btn"), key="save", size=(30, 1)), sg.Button(self.l10n.get_string("gui_back"), key="Exit", size=(30, 1))]
        )
        self.deviceignoresmenu = sg.Window(self.l10n.get_string("gui_devignoresmenu_title"), layout, finalize=True, icon=self.iconpath)
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
                self.deviceignoresmenu["status"].Update(self.l10n.get_string("gui_devignoresmenu_saved_text"))
    
    def _application_ignores_menu(self):
        run = True
        while run == True:
            save = self.load_save()
            layout = [
                [sg.Text("", key="status")],
                [sg.Text(self.l10n.get_string("gui_appignoresmenu_info_text"))],
                [sg.Button(self.l10n.get_string("gui_appignoresmenu_refresh_btn"), key="refresh_applications", size=(30, 1)), sg.Button(self.l10n.get_string("gui_appignoresmenu_save_btn"), key="save", size=(30, 1)), sg.Button(self.l10n.get_string("gui_back"), key="Exit", size=(30, 1))],
                [sg.Text(self.l10n.get_string("gui_appignoresmenu_appignores_text"))]
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
            self.applicationignoresmenu = sg.Window(self.l10n.get_string("gui_appignoresmenu_title"), layout, finalize=True, icon=self.iconpath)
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
                    self.applicationignoresmenu["status"].Update(self.l10n.get_string("gui_appignoresmenu_saved_text"))


if __name__ == "__main__":
    PDAVGui()._main_menu()
