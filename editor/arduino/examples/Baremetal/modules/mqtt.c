/*
#include <ArduinoMqttClient.h>

WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);

extern "C" uint8_t connect_mqtt(char *broker, uint16_t port);
extern "C" uint8_t mqtt_send(char *topic, char *message);

uint8_t connect_mqtt(char *broker, uint16_t port)
{
    return mqttClient.connect(broker, port);
}

uint8_t mqtt_send(char *topic, char *message)
{
    mqttClient.beginMessage(topic);
    mqttClient.print(message);
    mqttClient.endMessage();

    return 1;
}
*/

#include <PubSubClient.h>
//Reference: https://www.hivemq.com/blog/mqtt-client-library-encyclopedia-arduino-pubsubclient/

#ifdef MBTCP_ETHERNET
    EthernetClient wifiClient;
#else
    WiFiClient wifiClient;
#endif
PubSubClient mqttClient(wifiClient);

extern "C" uint8_t connect_mqtt(char *broker, uint16_t port);
extern "C" uint8_t connect_mqtt_auth(char *broker, uint16_t port, char *user, char *password);
extern "C" uint8_t mqtt_send(char *topic, char *message);
extern "C" uint8_t mqtt_receive(char *topic, char *message);
extern "C" uint8_t mqtt_subscribe(char *topic);
extern "C" uint8_t mqtt_unsubscribe(char *topic);
extern "C" uint8_t mqtt_disconnect();
extern "C" void mqtt_loop();

#define STR_MAX_LEN       126
#define POOL_INCREMENT    2
#define MAX_POOL_SIZE     10

struct MQTTpool {
    char mqtt_msg[STR_MAX_LEN];
    char mqtt_topic[STR_MAX_LEN];
    uint8_t is_free = true;
};

uint8_t pool_size = 0;
struct MQTTpool **msg_pool = NULL;

void add_message_to_pool(char *topic, char *msg)
{
    // Initialize array
    if (pool_size == 0)
    {
        pool_size += POOL_INCREMENT;
        msg_pool = (struct MQTTpool **)malloc(pool_size * sizeof(struct MQTTpool *));

        if (msg_pool == NULL)
        {
            // Allocation failed! Nothing to do here
            return;
        }

        // Allocate memory for each pool item
        for (int i = 0; i < POOL_INCREMENT; i++)
        {
            msg_pool[i] = (struct MQTTpool *)malloc(sizeof(struct MQTTpool));
            if (msg_pool[i] == NULL)
            {
                // Allocation failed! Nothing to do here
                return;
            }
        }
    }

    // Add message to the pool
    uint8_t message_added = false;
    while (!message_added)
    {
        for (int i = 0; i < pool_size; i++)
        {
            if (msg_pool[i]->is_free)
            {
                strncpy(msg_pool[i]->mqtt_topic, topic, STR_MAX_LEN);
                msg_pool[i]->mqtt_topic[STR_MAX_LEN - 1] = '\0'; // Safe termination
                strncpy(msg_pool[i]->mqtt_msg, msg, STR_MAX_LEN);
                msg_pool[i]->mqtt_msg[STR_MAX_LEN - 1] = '\0'; // Safe termination
                msg_pool[i]->is_free = false;
                message_added = true;
                break;
            }
        }

        // Pool is full
        if (!message_added)
        {
            // Increase pool size
            pool_size += POOL_INCREMENT;
            if (pool_size > MAX_POOL_SIZE)
            {
                // This is bad! No more space left. We must remove one of the messages
                pool_size -= POOL_INCREMENT;
                msg_pool[0]->is_free = true;
            }
            else
            {
                // Reallocate new size
                msg_pool = (struct MQTTpool **)realloc(msg_pool, pool_size * sizeof(struct MQTTpool *));

                if (msg_pool == NULL)
                {
                    // This is VERY bad!! Let's ignore this message, remove everything and start over
                    pool_size = 0;
                    return;
                }

                // Allocate memory for each pool item
                for (int i = (pool_size - POOL_INCREMENT); i < pool_size; i++)
                {
                    msg_pool[i] = (struct MQTTpool *)malloc(sizeof(struct MQTTpool));
                    if (msg_pool[i] == NULL)
                    {
                        // Allocation failed! Nothing to do here
                        return;
                    }
                    msg_pool[i]->is_free = true;
                }
            }
        }
    }
}

void callback(char* topic, byte* payload, unsigned int length)
{
    if (length > (STR_MAX_LEN - 1))
    {
        length = (STR_MAX_LEN - 1); // truncate string to max size
    }
    payload[length] = 0; // make sure string is NULL terminated

    add_message_to_pool(topic, (char *)payload);
}

void mqtt_loop()
{
    mqttClient.loop();
}

uint8_t connect_mqtt(char *broker, uint16_t port)
{
    mqttClient.setServer(broker, port);
    mqttClient.setCallback(callback);
    return mqttClient.connect("openplc-client");
}

uint8_t connect_mqtt_auth(char *broker, uint16_t port, char *user, char *password)
{
    mqttClient.setServer(broker, port);
    mqttClient.setCallback(callback);
    return mqttClient.connect("openplc-client", user, password);
}

uint8_t mqtt_send(char *topic, char *message)
{
    /*
    mqttClient.beginMessage(topic);
    mqttClient.print(message);
    mqttClient.endMessage();

    return 1;
    */

    return mqttClient.publish(topic, message);
}

uint8_t mqtt_subscribe(char *topic)
{
    return (uint8_t)mqttClient.subscribe(topic);
}

uint8_t mqtt_receive(char *topic, char *message)
{
    // Return the first message in the pool that matches topic
    for (int i = 0; i < pool_size; i++)
    {
        // Check if there are messages in the pool
        if (!msg_pool[i]->is_free)
        {
            if (!strncmp(topic, msg_pool[i]->mqtt_topic, STR_MAX_LEN))
            {
                strncpy(message, msg_pool[i]->mqtt_msg, STR_MAX_LEN);
                msg_pool[i]->is_free = true;
                return strlen(message);
            }
        }
    }

    return 0;
}

uint8_t mqtt_unsubscribe(char *topic)
{
    return (uint8_t)mqttClient.unsubscribe(topic);
}

uint8_t mqtt_disconnect()
{
    mqttClient.disconnect();
    return 1;
}