import ctypes
import re
from sm_framework.lib.library_wrapper import wrapper, wrap_functions
from sm_framework.py_oran.ByteArray import ByteArray
from sm_framework.py_oran.kpm.KpmFunctionDef import KpmFuncDefArr
from sm_framework.py_oran.kpm.enums import format_action_def_e


encode_action_def = wrap_functions(wrapper, 'encode_action_def', ByteArray, [ctypes.POINTER(ctypes.c_char_p), ctypes.c_long])
# decode_action_def = wrap_functions(wrapper, 'get_ran_func_def_kpm', ByteArray, [ctypes.POINTER(ctypes.c_char_p)])

# TODO To be fixed
encode_ev_trigger = wrap_functions(wrapper, 'encode_ev_trigger', ByteArray, [ctypes.c_int32]) 

def _remove_undecoded_bytes(input_string):
    # Convert octet string to bytes
    
    # Initialize an empty string for the decoded output
    decoded_string = ""
    
    for byte in input_string:
        # Check if the byte is printable ASCII character
        if 32 <= byte <= 126:
            decoded_string += chr(byte)
        # Replace '\x02' with ' ' (space)
        elif byte == 0x02:
            decoded_string += " "
        # Replace '\x00' with ' ' (space)
        elif byte == 0x00:
            decoded_string += " "
    
    # Remove multiple consecutive spaces
    decoded_string = ' '.join(decoded_string.split())
    
    decoded_string = decoded_string.replace("@", "").replace("`", "")
    return decoded_string

def action_array_builder(hex_xml, ran_function_id=2, oai=True, filter=None):
    """
    Builds an action array from a given hexadecimal XML string.

    This function takes a hexadecimal string representing XML data, a RAN function id, 
    and an optional flag indicating whether the data pertains to OAI (OpenAirInterface). It converts the hex string 
    decodes into a UTF-8 string (representing XML), and then processes the XML data to build 
    an action array based on the provided RAN function identifier.

    Parameters:
    ----------
    hex_xml (str): A hexadecimal string representing XML data.
    ran_function_id (int): An identifier for the RAN function to process.
    oai (bool, optional): A flag indicating if the data is related to OAI. Defaults to True.
    filter (string, optional): Allow to filter action definition using subscting, e.g., filter=Dl only downlink parameters 
                            (useful with run_function_id_=2)
    Returns:
    ----------
    list: A list of actions derived from the XML data based on the RAN function identifier.
    """
    bytes_data = bytes.fromhex(hex_xml)
    result = []
    if ran_function_id == 2:
        if oai:
            # TODO this method is temporary - we should call an external method provided by the library
            decoded_data = _remove_undecoded_bytes(bytes_data).replace(" ", "")
            result = re.split(r'(?=DRB\.)|(?=RRU\.)', decoded_data)[1:]
            if not filter is None:
                # filter could be downlink or uplink
                result = [value for value in result if filter.lower() in value.lower()]
            
    else:
        print("ran function id not supported yet!")

    return result

def action_encoder_from_fun_obj(func_def_obj: KpmFuncDefArr, gran_period_ms=1000):
    action_encoder(action_def_dict=func_def_obj.get_dict_of_values(),gran_period_ms=gran_period_ms)

def action_encoder(action_def_dict, gran_period_ms=1000) -> ByteArray:
    """
    Encodes a list of function definitions into a format suitable for the submgr.

    This function takes a list of function definitions, converts each function definition to bytes, 
    and prepares a C-style array of C strings (null-terminated byte strings). It then calls an 
    external function `encode_action_def` (kpm sm) to encode these function definitions with the specified 
    granularity period.

    Parameters:
    - action_def_dict (dict): dictionary having format as a key and list of string (name of function definitions) 
                            as value
    - gran_period_ms (int, optional): The granularity period in milliseconds for encoding the 
      action definitions. Default value is 1000 milliseconds.

    Returns:
    - The result from the `encode_action_def` function, which processes the C-style array of 
      encoded action definitions.
    """

    result = {}
    for format in action_def_dict.keys():
        if format == format_action_def_e.FORMAT_2_ACTION_DEFINITION or format == format_action_def_e.FORMAT_5_ACTION_DEFINITION:
            print("skipping - format not supported yet ({})".format(format))
            continue
        act_gnb_bytes = [s.encode() for s in action_def_dict[format]]

        act_gnb_c = (ctypes.c_char_p * (len(action_def_dict[format]) + 1))()  # Adding 1 to include space for terminating null pointer
        act_gnb_c[:-1] = [ctypes.c_char_p(s) for s in act_gnb_bytes]  # Assigning all elements

        act_gnb_c[-1] = None

        ba : ByteArray = encode_action_def(act_gnb_c, gran_period_ms, format)
        if ba.len != 0:
            result[format] = ba
    return result


def ev_trigger_encoder(period_ev_trig: ctypes.c_uint32) -> ByteArray:
    result = encode_ev_trigger(period_ev_trig)

    return result