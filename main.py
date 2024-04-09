import ujson as json
from machine import Pin, SoftI2C, unique_id
from ubinascii import hexlify
from umqtt.simple import MQTTClient
from utime import sleep

import ahtx0
from utils import wifimgr

settings = wifimgr.read_config()

CLIENT_ID = hexlify(unique_id()).decode("utf-8")
MQTT_PORT = 1883
MQTT_TOPIC = settings["topic"]

# SDA pin 23 and SCL pin 19
i2c = SoftI2C(scl=Pin(19,pull=Pin.PULL_UP), sda=Pin(23,pull=Pin.PULL_UP),freq=100000)
sensor = ahtx0.AHT10(i2c)

led = Pin(22, Pin.OUT)
led.on()


wlan = wifimgr.get_connection()
if wlan is None:
    print('Nie udało się połączenie z siecią WiFi.')
    wifimgr.restart()
    while True:
        pass  # you shall not pass :D


led.off()

def main () -> None:

    if wlan.isconnected():
        client = MQTTClient(CLIENT_ID, settings["broker"], MQTT_PORT, settings["broker_user"], settings["broker_pass"], 60)
        client.connect()

        msg = json.dumps(
            {
                "temperature": sensor.temperature,
                "humidity": sensor.relative_humidity,
                "dew_point": sensor.dew_point(),
                "device_id": CLIENT_ID,
                "device_name": settings["device_name"],
                "location1": settings["location1"],
                "location2": settings["location2"],
            }
            )

        client.publish(MQTT_TOPIC, msg)
        print("\nTemperatura: %0.2f C" % sensor.temperature)
        print("Wilgotność: %0.2f %%" % sensor.relative_humidity)
        print("Punkt rosy: %0.2f %%" % sensor.dew_point())
        client.disconnect()
        sleep(30)
    else:
        led.on()
        wlan.disconnect()
        sleep(5)
        wifimgr.restart()


if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            led.on()
            print("Błąd: " + str(e))
            wlan.disconnect()
            sleep(5)
            wifimgr.restart()



# {
#   "temperature": 24.0,
#   "humidity": 44.5,
#   "dew_point": 13.3,
#   "device_id": "690001",
#   "device_name": "sensor_001",
#   "location": "lakiernia"
# }
