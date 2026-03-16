import ctypes
import json

def read_file(filename):
    try:
        with open(filename, 'r') as f:
            data = f.read()
            if len(data) == 0:
                return None
            return data
    except IOError as error:
        return None

def get_c_byte_array_from_py_byte_string(byte_string: bytes):
    try:
        byte_data = bytes(byte_string.decode('unicode_escape').encode('latin-1'))
        byte_array = (ctypes.c_uint8 * len(byte_data)).from_buffer_copy(byte_data)

        return byte_array
    except:
        print("exception in byte array")
        return None

def extract_config_fields(config_file_path) -> tuple:
    """
    Extracts the 'app_name' and 'APP_NAMESPACE' fields from a config file.
    
    Args:
        config_file_path (str): Path to the config file
        
    Returns:
        tuple: (app_name, app_namespace) containing the extracted fields
        
    Raises:
        FileNotFoundError: If the config file doesn't exist
        KeyError: If required fields are missing from the config
        json.JSONDecodeError: If the file isn't valid JSON
    """
    try:
        with open(config_file_path, 'r') as f:
            config = json.load(f)
        
        # Extract the required fields
        app_name = config['name']
        app_namespace = config['APP_NAMESPACE']
        
        return app_name, app_namespace
        
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {config_file_path}")
    except KeyError as e:
        raise KeyError(f"Required field missing in config: {e}")
    except json.JSONDecodeError:
        raise json.JSONDecodeError(f"Invalid JSON format in config file: {config_file_path}")
    

def write_routing_table(app_name: str, app_namespace: str, rmr_port: int, route_path: str) -> bool:
    """
    Writes a routing table to the specified file.
    
    Args:
        app_name (str): name of xApp
        app_namespace (str): namespace of xApp
        rmr_port (int): port for RIC message routing
        route_file_path (str): path of route file to write to
    
    Returns:
        bool: True if the file was written successfully, False otherwise
    """

    xapp_port = rmr_port
    message_type_list = [12011, 12012, 12021, 12022, 12050]

    routing_table_start = "newrt|start\n"
    routing_table_end = "newrt|end"

    routing_table = routing_table_start
    for m in message_type_list:
        route = f"rte|{m}|service-{app_namespace}-{app_name}-rmr.{app_namespace}:{xapp_port}\n"
        routing_table += route
    routing_table += routing_table_end

    print(routing_table)
    
    try:
        with open(route_path, 'w') as f:
            f.write(routing_table)
        return True
    except Exception as e:
        print(f"Error writing to file: {e}")
        return False
