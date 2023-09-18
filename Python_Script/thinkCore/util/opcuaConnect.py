from opcua import Client

import util.General_Help as gHelp


class OPC_Connect:

    def __init__(self) -> None:
        app_settings = gHelp.get_app_config()
        server_address = app_settings.get('IgnitionServer')
        # Creates a client object and connect to the OPC UA server
        self.client = Client(server_address)

    def open(self):
        self.client.connect()
        root = self.client.get_root_node()

    def get_value(self, node_id):
        # Example "ns=2;s=[default]/PythonComTag"
        node = self.client.get_node(nodeid=node_id)
        value = node.get_value()

        return value

    def set_value(self, nodeID, new_value):
        status = 0
        try:
            node = self.client.get_node(nodeid=nodeID)
            result = node.set_value(new_value)
            status = 1
        except:
            status = 9
        finally:
            return status

    def set_multi_values(self, tags: list):
        # Write values to multiple tags
        # example_tags = [
        #     {"node_id": "ns=2;s=Tag1", "value": 10},
        #     {"node_id": "ns=2;s=Tag2", "value": "Hello OPC UA"},
        #     # Add more tags as needed
        # ]

        # Create a list of nodes to write to
        nodes_to_write = [self.client.get_node(tag["node_id"]) for tag in tags]

        # Create a list of values to write
        values_to_write = [tag["value"] for tag in tags]

        # Write the values to the tags
        self.client.set_values(nodes_to_write, values_to_write)

        # Disconnect from the OPC UA server
        # self.client.disconnect()

    def close(self):
        self.client.disconnect()
