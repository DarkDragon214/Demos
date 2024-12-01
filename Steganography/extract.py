from PIL import Image
import sys
import os
from encryption import decrypt

MAGENTA = "\033[95m"
RESET = "\033[0m"

# Define magic numbers for image formats
MAGIC_NUMBERS = {
    b'\xFF\xD8\xFF': 'jpeg',
    b'\x89PNG\r\n\x1A\n': 'png',
    b'BM': 'bmp',
    b'II*\x00': 'tiff',  # Little-endian TIFF
    b'MM\x00*': 'tiff',  # Big-endian TIFF
}


def extract_bin(image_path):
    img = Image.open(image_path)
    binary_text = ""
    width, height = img.size

    for x in range(width):
        for y in range(height):
            pixel = img.getpixel((x, y))
            for c in range(3):
                binary_text += str(pixel[c] & 1)
                if len(binary_text) % 8 == 0 and binary_text[-32:] == '00000000101010101111111101010101': # EOF code
                    return binary_text[:-32]
    return None


def bin_to_bytes(binary_text):
    byte_data = bytearray()
    for i in range(0, len(binary_text), 8):
        byte = binary_text[i:i + 8]
        byte_data.append(int(byte, 2))
    return byte_data


def find_magic_number(data):
    for magic, fmt in MAGIC_NUMBERS.items():
        if data.startswith(magic):
            return fmt
    return None


def save_data(data, output_name, format):
    if format:
        output_file_path = os.path.join("static/output", f"{output_name}.{format}")
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

        with open(output_file_path, 'wb') as file:
            file.write(data)
        return

    else:
        output_file_path = os.path.join("static/output", f"{output_name}.txt")
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

        with open(output_file_path, 'w') as file:
            file.write(data.decode('utf-8').replace('\r', ''))  # Remove carriage returns

        return

# Color user input
def get_input(prompt):
    user_input = input(prompt + MAGENTA)
    print(RESET, end='')  # Reset color after input
    if user_input.lower() == 'exit':
        print("\nExiting program.")
        sys.exit()
    return user_input


def get_stego(input_image, password):
    extracted_binary = extract_bin(input_image)
    if (not extracted_binary): # no secret file found
        return -1
    # decrypt
    iv_binary = extracted_binary[:128]  # First 128 bits for IV
    salt_binary = extracted_binary[128:256]  # Next 128 bits for salt
    encrypted_data = extracted_binary[256:]  # Remaining data is encrypted

    extracted_binary = decrypt(encrypted_data, password, iv_binary, salt_binary)
    byte_data = bin_to_bytes(extracted_binary)
    # Check for magic number
    format = find_magic_number(byte_data)
    if format == None:
        format = "txt"
    # Save data based on detected format
    save_data(byte_data, "stego-out", format)
    return f"stego-out.{format}"
