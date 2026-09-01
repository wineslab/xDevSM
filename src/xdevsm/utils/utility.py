import ctypes
import json

from mdclogpy import Level


def debug_enabled(logger):
    """True when `logger` would actually emit a debug line.

    mdclogpy filters by level inside log(), so a call site that formats its
    message inline pays for building the string even when it is then discarded.
    On the RMR dispatch path that is per-indication work on the one thread that
    handles every indication, so the hot call sites check this first.
    """
    get_level = getattr(logger, "get_level", None)
    if get_level is None:
        return True
    return get_level() <= Level.DEBUG

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
    """
    Copies a Python bytes object into a ctypes uint8 array for the SM decoders.

    The payload is copied verbatim. It must not be run through
    decode('unicode_escape'): that treats an 0x5C octet as the start of an escape
    sequence, so APER-encoded bytes containing 0x5C are silently collapsed
    (e.g. 5c 6e -> 0a) and the shortened buffer makes the C decoder abort on
    `assert(ret.code == RC_OK)`.
    """
    if byte_string is None:
        return None
    try:
        if isinstance(byte_string, str):
            byte_string = byte_string.encode('latin-1')
        return (ctypes.c_uint8 * len(byte_string)).from_buffer_copy(byte_string)
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        print("exception in byte array: {}".format(error))
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
    

def write_routing_table(
    app_name: str,
    app_namespace: str,
    rmr_port: int,
    route_path: str,
    plt_namespace: str = None,
    a1mediator_rmr_port: int = 4562,
) -> bool:
    """
    Writes a routing table to the specified file.

    Args:
        app_name (str): name of xApp
        app_namespace (str): namespace of xApp
        rmr_port (int): port for RIC message routing
        route_path (str): path of route file to write to
        plt_namespace (str, optional): platform namespace; if provided, a route
            for A1_POLICY_RESP (mtype 20011) is added pointing to the a1mediator
            RMR service so xApps can ack policies even when the incoming message
            source-id is not RMR-resolvable (`rmr_rts` fallback).
        a1mediator_rmr_port (int): a1mediator RMR port (default 4562).

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
    if plt_namespace:
        a1_endpoint = f"service-{plt_namespace}-a1mediator-rmr.{plt_namespace}:{a1mediator_rmr_port}"
        routing_table += f"rte|20011|{a1_endpoint}\n"
    routing_table += routing_table_end

    print(routing_table)

    try:
        with open(route_path, 'w') as f:
            f.write(routing_table)
        return True
    except Exception as e:
        print(f"Error writing to file: {e}")
        return False


def decode_meid(summary):
    raw = summary.get('meid')
    if raw is None:
        return None
    return raw.decode('utf-8') if isinstance(raw, (bytes, bytearray)) else raw