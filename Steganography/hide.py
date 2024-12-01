from Cryptodome.Random import get_random_bytes
from PIL import Image
import sys, os, cv2
from math import log10, sqrt
import numpy as np
from encryption import encrypt


def file_to_binary(file_path):
    with open(file_path, 'rb') as file:
        binary_data = ''.join(format(byte, '08b') for byte in file.read())
    return binary_data


def hide_binary(image_path, binary, password, output_path):
    img = Image.open(image_path)
    img = img.convert('RGB')
    width, height = img.size
    # encrypt
    salt = get_random_bytes(16)  # Cryptographically secure PRNG used to generate salt
    iv = get_random_bytes(16)
    salt_binary = ''.join(format(byte, '08b') for byte in salt)
    iv_binary = ''.join(format(byte, '08b') for byte in iv)
    binary = encrypt(binary, password, iv, salt)
    binary = iv_binary + salt_binary + binary
    end_flag = '00000000101010101111111101010101'
    binary += end_flag
    index = 0
    new_img = img.copy()
    binary_size = len(binary)

    LSB_COUNT = 1

    for lsb_index in range(LSB_COUNT):
        for x in range(width):
            for y in range(height):
                pixel = list(new_img.getpixel((x, y)))
                for c in range(3):
                    if index >= binary_size: break
                    pixel[c] = (pixel[c] & ~(1 << lsb_index)) | (int(binary[index]) << lsb_index)
                    index += 1
                new_img.putpixel((x, y), tuple(pixel))
            if index >= binary_size: break
        if index >= binary_size:
            break

    new_img.save(output_path)


def psnr(original, modified):
    original = cv2.imread(original)
    modified = cv2.imread(modified)
    mse = np.mean((original - modified) ** 2)
    if(mse == 0):
        return 100
    max_pixel = 255.0
    psnr = 20 * log10(max_pixel / sqrt(mse))
    return psnr


def mse(original, modified):
    original = cv2.imread(original)
    modified = cv2.imread(modified)
    return np.mean((original - modified) ** 2)


def get_result(input_image, secret_file, password, output_image):
    secret_binary = file_to_binary(secret_file)
    hide_binary(input_image, secret_binary, password, output_image)