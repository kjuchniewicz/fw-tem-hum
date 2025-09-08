import ahtx0
import ujson as json
from machine import Pin, SoftI2C, unique_id
from ubinascii import hexlify
from umqtt.simple import MQTTClient
from utils import wifimgr
from utime import sleep

settings = wifimgr.read_config()

CLIENT_ID = hexlify(unique_id()).decode("utf-8")
MQTT_PORT = 1883
MQTT_TOPIC = settings["topic"]
DELAY_SEND = settings["delay_send"]
print(CLIENT_ID)

# SDA pin 23 and SCL pin 19
i2c = SoftI2C(scl=Pin(19, pull=Pin.PULL_UP), sda=Pin(23, pull=Pin.PULL_UP), freq=100000)
sensor = ahtx0.AHT10(i2c)

led = Pin(22, Pin.OUT)
led.on()


wlan = wifimgr.get_connection()
if wlan is None:
    print("Nie udało się połączenie z siecią WiFi.")
    wifimgr.restart("wlan in main")
    while True:
        pass  # you shall not pass :D


print("Połączenie z siecią WiFi.", settings["location1"], ":", settings["location2"])
led.off()


def main() -> None:
    try:
        if wlan.isconnected():
            temp = sensor.temperature
            hum = sensor.relative_humidity
            dew = sensor.dew_point()
            print("\nTemperatura: %0.2f C" % temp)
            print("Wilgotność: %0.2f %%" % hum)
            print("Punkt rosy: %0.2f C" % dew)

            msg = json.dumps(
                {
                    "temperature": temp,
                    "humidity": hum,
                    "dew_point": dew,
                    "device_id": CLIENT_ID,
                    "device_name": settings["device_name"],
                    "location1": settings["location1"],
                    "location2": settings["location2"],
                }
            )

            client = MQTTClient(
                CLIENT_ID,
                settings["broker"],
                MQTT_PORT,
                settings["broker_user"],
                settings["broker_pass"],
                60,
            )
            sleep(2)
            print("Klient utworzony")
            client.connect()
            print("Klient polaczony")
            client.publish(MQTT_TOPIC, msg)
            print("Wyslano")
            client.disconnect()
            print("Klient odlaczony")
            sleep(DELAY_SEND)
        else:
            led.on()
            wlan.disconnect()
            sleep(5)
            wifimgr.restart("inner main")

    except Exception as e:
        led.on()
        print("Błąd wewnętrzny: " + str(e))
        wlan.disconnect()
        sleep(5)
        wifimgr.restart("inner main exception")


if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            led.on()
            print("Błąd: " + str(e))
            wlan.disconnect()
            sleep(1)
            wifimgr.restart("main")


# {
#   "temperature": 24.0,
#   "humidity": 44.5,
#   "dew_point": 13.3,
#   "device_id": "690001",
#   "device_name": "sensor_001",
#   "location": "lakiernia"
# }
