"""
MQTT media adapter for GXDLMSReader.

This adapter mirrors the open/send/receive/close semantics that GXDLMSReader
expects from GXNet/GXSerial while publishing DLMS request frames to an MQTT
broker and delivering subscribed responses back to the DLMS client. It uses the
`paho-mqtt` client directly and does not require the separate Gurux.MQTT bridge
components; point the publish/subscribe topics at whichever broker or bridge you
run.
"""
import queue
import threading
import time
from typing import Optional

import paho.mqtt.client as mqtt


class GXMqttMedia:
    """MQTT-backed media wrapper matching GXDLMSReader expectations."""

    def __init__(
        self,
        hostName: Optional[str],
        port: int,
        publishTopic: str,
        subscribeTopic: str,
        qos: int = 1,
        keepalive: int = 60,
        clientId: Optional[str] = None,
        mqttClient=None,
    ) -> None:
        self.hostName = hostName
        self.port = port
        self.publishTopic = publishTopic
        self.subscribeTopic = subscribeTopic
        self.qos = qos
        self.keepalive = keepalive
        self.clientId = clientId
        self._client = mqttClient or mqtt.Client(client_id=clientId)
        self._client.on_message = self._on_message
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._lock = threading.RLock()
        self._queue: queue.Queue[bytes] = queue.Queue()
        self._connected = False
        self._loop_started = False
        self.eop = None

    def _on_connect(self, client, userdata, flags, rc):
        self._connected = True
        client.subscribe(self.subscribeTopic, qos=self.qos)

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False

    def _on_message(self, client, userdata, msg):
        # Store raw payload for ReceiveParameters to consume.
        self._queue.put(msg.payload)

    def isOpen(self) -> bool:
        return self._connected

    def open(self) -> None:
        if self._connected:
            return
        if self.hostName is None:
            raise ValueError("MQTT host name is not set.")
        self._client.connect(self.hostName, self.port, self.keepalive)
        self._client.loop_start()
        self._loop_started = True
        # Give the background thread time to connect and subscribe.
        timeout_at = time.time() + 5
        while not self._connected and time.time() < timeout_at:
            time.sleep(0.01)
        if not self._connected:
            raise ConnectionError("Failed to connect to MQTT broker.")

    def close(self) -> None:
        if self._loop_started:
            self._client.loop_stop()
            self._loop_started = False
        if self._connected:
            self._client.disconnect()
            self._connected = False

    def send(self, data, eop=None) -> None:
        if isinstance(data, str):
            payload = data.encode()
        else:
            payload = bytes(data)
        self._client.publish(self.publishTopic, payload, qos=self.qos)

    def receive(self, p) -> bool:
        try:
            payload = self._queue.get(timeout=p.waitTime / 1000.0)
        except queue.Empty:
            return False
        p.reply = payload
        return True

    def getSynchronous(self):
        return self._lock
