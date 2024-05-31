#!/usr/bin/env python3

import socket
import struct
import binascii

# Function to send a query to the server
def send_query(server_address, query):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(10)  # Increase the timeout duration to 10 seconds
    print(f"Sending query to {server_address}: {binascii.hexlify(query)}")
    sock.sendto(query, server_address)
    try:
        response, _ = sock.recvfrom(4096)
        print(f"Received response: {binascii.hexlify(response)}")
        return response
    except socket.timeout:
        print("Query timed out")
        return None
    finally:
        sock.close()

# Function to parse a null-terminated string
def read_null_terminated_string(data, offset):
    end = data.find(b'\x00', offset)
    if end == -1:
        raise IndexError("Null terminator not found")
    string = data[offset:end].decode('utf-8', 'ignore')
    return string, end + 1

# Function to parse the A2S_INFO response
def parse_response(response):
    if response is None:
        return None

    header = response[:4]
    if header != b'\xFF\xFF\xFF\xFF':
        print("Invalid response header")
        return None

    response_type = response[4]
    if response_type == ord('I'):
        offset = 5
        protocol = response[offset]
        offset += 1

        try:
            server_name, offset = read_null_terminated_string(response, offset)
            print(f"Server Name: {server_name}")

            map_name, offset = read_null_terminated_string(response, offset)
            print(f"Map Name: {map_name}")

            folder, offset = read_null_terminated_string(response, offset)
            print(f"Folder: {folder}")

            game, offset = read_null_terminated_string(response, offset)
            print(f"Game: {game}")

            if offset + 2 > len(response):
                print("Offset out of range after reading ID")
                return None
            id_value = struct.unpack_from('<H', response, offset)[0]
            offset += 2

            if offset + 1 > len(response):
                print("Offset out of range after reading player count")
                return None
            player_count = response[offset]
            return player_count

        except IndexError as e:
            print(f"Error parsing response: {e}")
            return None

    elif response_type == ord('A'):
        # Handle the challenge response
        challenge = response[5:]
        return challenge
    else:
        print("Invalid response type")
        return None

def main():
    server_list_file = 'serverlist/servers'  # Path to the server list file

    # Read the server list file
    try:
        with open(server_list_file, 'r') as file:
            servers = file.readlines()
    except FileNotFoundError:
        print(f"File not found: {server_list_file}")
        return

    # Initial query for A2S_INFO
    query = b'\xFF\xFF\xFF\xFF\x54Source Engine Query\x00'

    # Process each server in the list
    for server in servers:
        server = server.strip()
        if not server:
            continue

        try:
            server_ip, server_port = server.split(':')
            server_port = int(server_port)
        except ValueError:
            print(f"Invalid server entry: {server}")
            continue

        server_address = (server_ip, server_port)
        print(f"Querying server: {server_ip}:{server_port}")

        response = send_query(server_address, query)
        if response:
            parsed_response = parse_response(response)
            if isinstance(parsed_response, bytes):
                # Challenge received, send the challenge response
                challenge_query = b'\xFF\xFF\xFF\xFF\x54Source Engine Query\x00' + parsed_response
                response = send_query(server_address, challenge_query)
                if response:
                    print(f"Raw response: {binascii.hexlify(response)}")
                    player_count = parse_response(response)
                    if player_count is not None:
                        print(f"Current online player count: {player_count}")
                    else:
                        print("Failed to parse player count")
                else:
                    print("No response received from server after challenge")
            elif parsed_response is not None:
                print(f"Current online player count: {parsed_response}")
            else:
                print("Failed to parse player count")
        else:
            print("No response received from server")

if __name__ == "__main__":
    main()
