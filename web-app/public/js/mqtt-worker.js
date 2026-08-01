importScripts('https://unpkg.com/mqtt/dist/mqtt.min.js');

let client = null;
let activePorts = new Set(); 

onconnect = function (e) {
    const port = e.ports[0];
    activePorts.add(port);

    port.onmessage = function (msg) {
        const { type, config, topic, payload } = msg.data;
        console.log("Got onmessage")
        
        if (type === 'CONNECT') {
            if (!client) {
                console.log("Worker: Initializing MQTT Connection...");
                client = mqtt.connect(config.brokerUrl, config.options);

                client.on('message', (t, m) => {
                    
                    activePorts.forEach(p => {
                        p.postMessage({
                            type: 'MQTT_MESSAGE',
                            topic: t,
                            payload: m.toString()
                        });
                    });
                });

                client.on('connect', () => console.log("Worker: MQTT Connected"));
                client.on('error', (err) => console.error("Worker: MQTT Error", err));
            }
        }

        if (type === 'SUBSCRIBE' && client) {
            client.subscribe(topic,{ qos: 1 });
            console.log("Worker: Subscribed to", topic);
        }
        if (type === 'PUBLISH' && client) {
            client.publish(topic, payload, { qos: 1 });
            console.log("Topic:",topic)
            console.log("payload:",payload)

        }
      
        if (type === 'UNLOAD') {
            activePorts.delete(port);
            console.log("Worker: Port removed. Remaining ports:", activePorts.size);
        }
    };

    port.start();
};