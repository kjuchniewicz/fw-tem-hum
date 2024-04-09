__author__ = "Juchniewicz Kamil"
__copyright__ = "Prawo autorskie 2024, ŻHU Zarna"
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "Juchniewicz Kamil"
__email__ = "k.juchniewicz@zarna.pl"
__status__ = "Rozwój"

import time

import machine
import network
import ujson as json

SECRETS = "secrets.json"

wlan_sta = network.WLAN(network.STA_IF)

#  Zwraca połączenie z siecią WiFi
def get_connection():
    # Sprawdzam czy jest połączenie
    if wlan_sta.isconnected():
        return wlan_sta

    connected = False
    try:
        # ESP potrzebuje chwile aby się połączyć
        time.sleep(3)
        if wlan_sta.isconnected():
            return wlan_sta

        #  Wczytuje profile z pliku
        profiles = read_profiles()

        # Wyszukujemy WiFi w zasięgu
        wlan_sta.active(True)
        networks = wlan_sta.scan()

        AUTHMODE = {0: "open", 1: "WEP", 2: "WPA-PSK", 3: "WPA2-PSK", 4: "WPA/WPA2-PSK"}

        for ssid, b_ssid, channel, rssi, authmode, hidden in sorted(networks, key=lambda x: x[3], reverse=True):
            ssid = ssid.decode('utf-8')
            print("ssid: %s kanał: %d rssi: %d mode: %s" % (ssid, channel, rssi, AUTHMODE.get(authmode, '?')))
            if authmode > 0:
                if ssid in profiles:
                    password = profiles[ssid]
                    connected = do_connect(ssid, password)
                else:
                    print("pomijanie nieznanej sieci szyfrowanej: %s\n" % ssid)
                    print("-"*100)
            else:  # open
                print("pomijanie sieci otwartych: %s\n" % ssid)
                print("-"*100)
                # connected = do_connect(ssid, None)
            if connected:
                break

    except OSError as e:
        print(e)

    # Rozpocznij serwer  dla Menedżera połączeń:
    if not connected:
        # Trzeba restartować połączenie
        restart()

    return wlan_sta if connected else None


def restart():
    print("Resetowanie...")
    time.sleep(1)
    machine.reset()


# Zwracam profile odczytane z pliku nazwa sieci i hasło nie m
def read_profiles():
    try:
        with open(SECRETS, 'r') as f:
            settings = json.loads( f.read())
    except OSError:
        return {}

    profiles = {}
    profiles[settings["WiFi"]["ssid"]] = settings["WiFi"]["ssid_pass"]

    return profiles

# Zwracam profile odczytane z pliku nazwa sieci i hasło nie m
def read_config():
    try:
        with open(SECRETS, 'r') as f:
            settings = json.loads( f.read())
    except OSError:
        return {}

    # config = {}
    # config[settings["WiFi"]["ssid"]] = settings["WiFi"]["ssid_pass"]

    return settings["mqtt"]


# łączenie z siecia WiFi
def do_connect(ssid, password):
    wlan_sta.active(True)
    if wlan_sta.isconnected():
        return None
    print('Próba połączenia z %s...' % ssid)
    wlan_sta.connect(ssid, password)
    for retry in range(100):
        connected = wlan_sta.isconnected()
        if connected:
            break
        time.sleep(0.2)
        print('.', end='')
    if connected:
        print('\nPołączony. Konfiguracja sieci: ', wlan_sta.ifconfig())

    else:
        print('\nNiepowodzenie. Nie połączono z: ' + ssid + '\n')
    return connected
