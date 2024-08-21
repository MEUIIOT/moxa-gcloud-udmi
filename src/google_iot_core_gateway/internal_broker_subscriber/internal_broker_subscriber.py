import ssl
import logging
from multiprocessing import Queue

import paho.mqtt.client as mqtt


class MosquittoMQTTSubscriber:

    def __init__(self, logger, google_iot_core_queue, 
                host="127.0.0.1", port=8883,
                ca_certs=None,
                certfile=None,
                keyfile=None,
                disable_tls_cert_verification=False,
                enable_tls=False):

        self.logger = logger
        self.google_iot_core_queue = google_iot_core_queue

        self._broker_url = host
        self._port = port
        self._trusted_root_ca = ca_certs
        self._x509_certificate  = certfile
        self._private_key = keyfile
        self._tls_insecure_set = disable_tls_cert_verification
        self._enable_tls = enable_tls

        self.client = mqtt.Client()

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish
        self.client.on_subscribe = self._on_subscribe
        self.client.on_message = self._on_message
        self.client.on_log = self._on_log
        
        if self._enable_tls:
           self.client.tls_set(ca_certs=self._trusted_root_ca,
                            certfile=self._x509_certificate,
                            keyfile=self._private_key, 
                            tls_version=ssl.PROTOCOL_TLSv1_2,
                            ciphers=None)
           # Disable certificate verification
           self.client.tls_insecure_set(self._tls_insecure_set)

           try:
               self.client.connect(self._broker_url, self._port, 60)
           except Exception as e:
               logger.error("An error occurred: {}".format(e))

        else:
             try:
                self.client.connect(self._broker_url, self._port, 60)
             except Exception as e:
                logger.error("An error occurred: {}".format(e))

    def _error_str(self, rc):
        """
        Convert a Paho error to a human readable string.
        """
        return "{}: {}".format(rc, mqtt.error_string(rc))

    def _on_connect(self, client, user_data, flags, rc):
        self.logger.debug(f"on_connect: {mqtt.connack_string(rc)}")
        self.logger.info("*************************************************************")
        self.logger.info("Connected successfully to MXcloudgate internal broker: {}".format(self._broker_url))
        self.logger.info("*************************************************************")
        self.logger.info(f"Subscribing to the internal broker")
        client.subscribe("MXcloudgate", 0)

    def _on_disconnect(self, client, user_data, flags, rc):
        self.logger.debug(f"on_disconnect: {self._error_str(rc)}")

    def _on_publish(self, client, user_data, mid):
        self.logger.debug(f"on_publish: {mid}")

    def _on_subscribe(self, client, user_data, mid, granted_qos):
        self.logger.debug("on_subscribed: " + str(mid) + " " + str(granted_qos))

    def _on_message(self, client, user_data, message):
        payload = str(message.payload.decode("utf-8"))
        self.logger.info("Received message '{}' on topic '{}' with Qos {}".format(
            payload, message.topic, str(message.qos)
        ))

        self.google_iot_core_queue.put(payload)

    def _on_log(self, client, user_data, level, buf):
        self.logger.debug("on_log: (%s) - %s ", level, buf)

    def run(self):
        self.client.loop_start()


def main():
    logger = logging.getLogger(__name__)
    messages_queue = Queue()

    int_broker_subscriber = MosquittoMQTTSubscriber(logger, messages_queue)
    int_broker_subscriber.run()


if __name__ == "__main__":
    main()
