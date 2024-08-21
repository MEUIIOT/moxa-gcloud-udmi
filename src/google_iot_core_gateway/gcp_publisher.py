import datetime
import random
import ssl
import time
import socket
import paho.mqtt.client as mqtt

from google_iot_core_gateway.utils.jwt_handler import create_jwt

# Change Log 2024 August 06
""" 
Added MQTT protoocl version in __init__
https://docs.clearblade.com/iotcore/publishing-over-mqtt

Added loop_stop() under on_disconnect callback
"""
# Change Log 2024 August 12
"""
Removed loop_stop() under on_disconnect callback
Handle socket.timeout exception paho mqtt client.connect() method
Added keep alive in client.connect() method to prevent timeout 
"""

class GoogleIoTCoreMQTTPublisher:

    def __init__(self, logger, connected_devices, project_id, cloud_region, registry_id, gateway_id, private_key_file,
                 ca_cert, mqtt_bridge_hostname, mqtt_bridge_port, jwt_signing_algorithm="RS256"):
        self.logger = logger
        self._connected_devices = connected_devices
        self._project_id = project_id
        self._cloud_region = cloud_region
        self._registry_id = registry_id
        self._gateway_id = gateway_id
        self._private_key_file = private_key_file
        self._jwt_signing_algorithm = jwt_signing_algorithm
        self._ca_cert = ca_cert
        self._mqtt_bridge_hostname = mqtt_bridge_hostname
        self._mqtt_bridge_port = mqtt_bridge_port
        self._keep_alive_sec = 60
        self._minimum_backoff_time = 1
        self._maximum_backoff_time = 64
        
        self._protocol_version = mqtt.MQTTv311

        self._is_connected = False

        self.client, self._jwt_exp = self._get_client()

        self._attach_devices_to_gateway()
        

    def error_str(self, rc):
        """
        Convert a Paho error to a human readable string.
        """
        return "{}: {}".format(rc, mqtt.error_string(rc))

    def on_connect(self, client, user_data, flags, rc):
        """
        Callback for when a device connects.
        """
        self.logger.info("*************************************************************")
        self.logger.info("Connected successfully to Google Cloud IoT Core")
        self.logger.info("*************************************************************")

        # After a successful connect, reset backoff time and stop backing off.
        self._minimum_backoff_time = 1

        self._is_connected = True

    def on_disconnect(self, client, user_data, rc):
        """
        Paho callback for when a device disconnects.
        """
        if rc == 0:
            self.logger.debug(f"on_disconnect: {self.error_str(rc)}")
        else:
            self.logger.error(f"on_disconnect: {self.error_str(rc)}")
            
        # Since a disconnect occurred, the next loop iteration will wait with
        # exponential backoff.
        self._is_connected = False

    def on_publish(self, client, user_data, mid):
        """
        Paho callback when a message is sent to the broker.
        """
        self.logger.debug(f"on_publish - mid: {mid}")

    def on_message(self, client, user_data, message):
        """
        Callback when the device receives a message on a subscription.
        """
        payload = str(message.payload.decode("utf-8"))
        self.logger.debug("Received message '{}' on topic '{}' with Qos {}".format(
            payload, message.topic, str(message.qos)
        ))

    def on_subscribe(self, client, obj, mid, granted_qos):
        self.logger.debug("on_subscribed: " + str(mid) + " " + str(granted_qos))

    def on_log(self, client, user_data, level, buf):
        self.logger.debug("on_log: (%s) - %s ", level, buf)
        return

    def _get_client(self):
        """
        Create our MQTT client. The client_id is a unique string that identifies this device.
        For Google Cloud IoT Core, it must be in the format below.
        """
        client_id = "projects/{}/locations/{}/registries/{}/devices/{}".format(
            self._project_id, self._cloud_region, self._registry_id, self._gateway_id
        )
        self.logger.debug("Device client_id is '{}'".format(client_id))

        client = mqtt.Client(client_id=client_id, protocol=self._protocol_version)

        # With Google Cloud IoT Core, the username field is ignored, and the
        # password field is used to transmit a JWT to authorize the device.
        jwt, jwt_exp = create_jwt(self.logger, self._project_id, self._private_key_file, self._jwt_signing_algorithm)
        client.username_pw_set(
            username="unused",
            password=jwt
        )

        # Enable SSL/TLS support.
        client.tls_set(ca_certs=self._ca_cert, tls_version=ssl.PROTOCOL_TLSv1_2)

        # Register message callbacks. https://eclipse.org/paho/clients/python/docs/
        # describes additional callbacks that Paho supports. In this example, the
        # callbacks just print to standard out.
        client.on_connect = self.on_connect
        client.on_disconnect = self.on_disconnect
        client.on_publish = self.on_publish
        client.on_message = self.on_message
        client.on_subscribe = self.on_subscribe
        client.on_log = self.on_log

        # Connect to the Google MQTT bridge.
        self.logger.debug("Connecting to the Google IoT Cloud")
        
        try:
            client.connect(host=self._mqtt_bridge_hostname, port=self._mqtt_bridge_port, keepalive=self._keep_alive_sec)
            time.sleep(5)
        except socket.timeout:
            self.logger.error("Connection attempt timed out!")
        except socket.error as e:
            self.logger.error(f"Socket error: {e}")    
       
        
        # This is the topic that the device will receive configuration updates on.
        mqtt_config_topic = "/devices/{}/config".format(self._gateway_id)

        # Subscribe to the config topic.
        client.subscribe(mqtt_config_topic, qos=1)

        # The topic that the device will receive commands on.
        mqtt_command_topic = "/devices/{}/commands/#".format(self._gateway_id)

        # Subscribe to the commands topic, QoS 1 enables message acknowledgement.
        self.logger.debug("Subscribing to {}".format(mqtt_command_topic))
        client.subscribe(mqtt_command_topic, qos=0)

        client.loop_start()

        return client, jwt_exp

    def _attach_devices_to_gateway(self):
        for device_id, device_details in self._connected_devices.items():
            self.attach_device_to_gateway(device_id)
            self.subscribe_to_device_topics(device_id)
            time.sleep(2)

    def _reconnect(self):
        self.logger.info("*************************************************************")
        self.logger.info("Mqtt Google IoT Core Connection Closed! Reopening!")
        self.logger.info("*************************************************************")

        delay = self._minimum_backoff_time + random.randint(0, 1000) / 1000.0
        time.sleep(delay)

        if self._minimum_backoff_time < self._maximum_backoff_time:
            self._minimum_backoff_time *= 2

        self.client.loop_stop()
        self.client.disconnect()
        self.client, self._jwt_exp = self._get_client()
        self._attach_devices_to_gateway()

    def _validate_jwt_token(self):
        seconds_till_token_expires = (self._jwt_exp - datetime.datetime.utcnow()).total_seconds()
        if seconds_till_token_expires < 60:
            self.logger.info("*************************************************************")
            self.logger.info("Refreshing JWT token")
            self.logger.info("*************************************************************")
            self.client.loop_stop()
            self.client.disconnect()
            self.client, self._jwt_exp = self._get_client()
            self._attach_devices_to_gateway()

    def is_connection_open(self):
        self._validate_jwt_token()

        if self._is_connected:
            self.logger.debug("Connection to Google Cloud is active!")
            return True
        else:
            self._reconnect()

        return self._is_connected

    def subscribe_to_device_topics(self, device_id):
        # The topic devices receive configuration updates on.
        device_config_topic = "/devices/{}/config".format(device_id)
        self.client.subscribe(device_config_topic, qos=1)

    def publish(self, device_id, payload, topic="state", qos=1):
        # self.client.loop()
        device_topic = "/devices/{}/{}".format(device_id, topic)
        self.client.publish(device_topic, payload, qos=qos)

    def attach_device_to_gateway(self, device_id, auth=""):
        attach_payload = '{{"authorization" : "{}"}}'.format(auth)
        self.publish(device_id, attach_payload, topic="attach", qos=1)
