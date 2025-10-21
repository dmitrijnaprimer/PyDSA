#!/usr/bin/env python3
"""
Download data from a Rigol oscilloscope channel 1 and
dump to a .wav file.
By Ken Shirriff, http://righto.com/rigol
Modified for Python 3 and PyVISA
"""

import sys
import pyvisa # Import pyvisa instead of visa
import wave
import os

try:
    # Create a resource manager instance
    rm = pyvisa.ResourceManager() # Use '@ni' or '@py' backend as needed
except pyvisa.errors.LibraryError as e:
    print(f"Error initializing PyVISA: {e}")
    sys.exit(-1)

try:
    # Get the list of resources
    resources = rm.list_resources() # Use rm.list_resources()
    print(f"Available resources: {resources}")

    # Find USB device (adjust filter if needed)
    usb_resources = [res for res in resources if 'USB' in res]
    if len(usb_resources) != 1:
        print('Bad instrument list or multiple USB devices found:', usb_resources)
        rm.close() # Close the resource manager before exiting
        sys.exit(-1)

    scope_resource_name = usb_resources[0] # Get the first matching USB resource
    print(f"Connecting to: {scope_resource_name}")

    # Open the instrument resource
    scope = rm.open_resource(scope_resource_name, timeout=20000, chunk_size=1024000) # Use rm.open_resource(), timeout in ms

    # --- Query scope settings (optional but useful) ---
    sample_rate = float(scope.query(':ACQ:SAMP?')) # Use query() for strings/numbers
    print(f"Acquisition Sample Rate: {sample_rate} Sa/s")

    # --- Acquire Data ---
    scope.write(":STOP") # Stop acquisition
    scope.write(":WAV:POIN:MODE RAW") # Set to raw points mode
    # Read raw binary data, removing the header (first 10 bytes is common)
    rawdata_bytes = scope.query_binary_values(":WAV:DATA? CHAN1", datatype='B', header_fmt='ieee', is_big_endian=False)
    data_size = len(rawdata_bytes)
    print(f'Data size (bytes): {data_size}')

    scope.write(":KEY:FORCE") # Release Run/Stop key hold if necessary (check scope manual)
    scope.close() # Close the instrument connection

    # --- Process and Save Data ---
    # Convert raw bytes (0-255) to signed integers (-128 to 127) if needed for audio interpretation
    # This example saves the raw unsigned bytes as 8-bit audio directly.
    # If you need signed 8-bit, you might need: signed_data = [b if b < 128 else b - 256 for b in rawdata_bytes]
    # But .wav 8-bit is typically unsigned anyway. Adjust based on your needs.
    rawdata_bytes_as_bytes = bytes(rawdata_bytes) # Ensure it's a bytes object for wave.writeframes

    # Dump data to the wav file
    wav_filename = "channel1.wav"
    with wave.open(wav_filename, "wb") as wav_file: # Use 'with' for automatic file closing
        nchannels = 1
        sampwidth = 1 # 1 byte = 8 bits per sample
        comptype = "NONE"
        compname = "not compressed"
        wav_file.setparams((nchannels, sampwidth, int(sample_rate), data_size,
                            comptype, compname))
        # Data is written as unsigned 8-bit values (0-255)
        wav_file.writeframes(rawdata_bytes_as_bytes)

    print(f"Data saved to {wav_filename}")

    # Optional: Call external viewer (adjust path/command if needed)
    # os.system(f"wfm_view {wav_filename}") # Comment out if wfm_view is not available or not needed

except pyvisa.errors.VisaIOError as e:
    print(f"VISA IO Error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    rm.close() # Ensure the resource manager is closed
