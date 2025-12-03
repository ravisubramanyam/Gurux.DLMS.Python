# Gurux DLMS Client Example (Python)

This sample drives the Gurux DLMS/COSEM client to read meter data over different media.

## MQTT transport
The sample ships with a small `GXMqttMedia` adapter that uses the standard `paho-mqtt`
client to publish DLMS request frames and collect responses from the configured
subscribe topic. It does **not** depend on the separate `Gurux.MQTT` bridge
repository; instead, the adapter mirrors the same `open`/`send`/`receive`/`close`
semantics that `GXDLMSReader` expects from the TCP (`GXNet`) or serial
(`GXSerial`) transports while leaving the actual broker setup to the user.

If you prefer to use `Gurux.MQTT`'s bridge components, you can connect them to
any MQTT broker and point this adapter at the publish/subscribe topics exposed by
that bridge.
