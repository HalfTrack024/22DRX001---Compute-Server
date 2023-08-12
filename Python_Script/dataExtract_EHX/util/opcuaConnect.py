from opcua import Client

class OPC_Connect: 

    def __init__(self) -> None:
        # Creates a client object and connect to the OPC UA server
        self.client = Client("opc.tcp://16131_Server:62541") 

    def open(self):
        self.client.connect()
        root = self.client.get_root_node()

    def getValue(self, nodeID):
        # Example "ns=2;s=[default]/PythonComTag"
        node = self.client.get_node(nodeid = nodeID) 
        value = node.get_value()
        
        return value

    def setValue(self, nodeID, new_value):
        status = 0
        try: 
            node = self.client.get_node(nodeid = nodeID) 
            node.set_value(new_value)
            status = 1
        except:
            status = 9
        finally:
            return status
        
    def close(self):
        self.client.disconnect()


