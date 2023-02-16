import binascii
import math
import socket
import threading
from struct import pack, unpack
import random
from time import sleep
import os
from _thread import interrupt_main


def keep_alive(stop, sock, ip_address):
    pom = 0
    no_response = 0
    while True:
        sock.settimeout(5)
        try:
            if stop():
                return
            if (pom == 0 or no_response > 0):
                sock.sendto(pack("c", str.encode("8")), ip_address)
                pom = pom + 1

            data, ip_address = sock.recvfrom(1500)
            data = data.decode()

            sleep(5)
            if (data == '8'):
                no_response = 0
                sock.sendto(pack("c", str.encode("8")), ip_address)
        except(socket.timeout):
            no_response = no_response + 1
            if (no_response < 3):
                continue
            else:
                print("\n---------")
                print("Spojenie bolo zrusene, server nereaguje.")
                print("---------")
                interrupt_main()
                return


def server_side(switch, ip_address, sock):
    data = None

    if (switch == False):
        # get port number of server
        port = input("Zadaj cislo portu pre server: ")

        # create socket for server
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # bind conversation with client
        sock.bind(("", int(port)))

        # get data from initialization packet
        data, ip_address = sock.recvfrom(1500)

        data = data.decode()

    # check if was sent an initialization packet from client
    if (data == '1' or switch == True):
        print("----------")
        print("Spojenie inicializovane z adresy: ", ip_address)
        if not (switch == True):
            sock.sendto(pack("c", str.encode("2")), ip_address)
        sock.settimeout(1000)

        pom = 0
        while True:

            while True:
                data, ip_address = sock.recvfrom(1500)
                first_byte = unpack("c", data[:1])
                if (first_byte[0] == b'8'):
                    sock.sendto(pack("c", str.encode("8")), ip_address)
                else:
                    break

            if (first_byte[0] == b'7'):
                sock.sendto(pack("c", str.encode("7")), ip_address)
                switch = True
                client_side(switch, ip_address, sock)
                exit()

            if (first_byte[0] == b'9'):
                sock.sendto(pack("c", str.encode("9")), ip_address)
                print("---------------")
                print("Program sa ukoncuje")
                print("---------------")
                exit()

            next = input("Pre interakciu servera stlac enter")
            if (next == ''):

                print("Cakam na data")
                print("----------")

                type_of_message = unpack("c", data[1:2])

                if (type_of_message[0] == b'1'):

                    number_of_fragments = unpack("h", data[4:6])

                    i = 0
                    message = ""
                    size_of_fragment = 0
                    size_of_last_fragment = 0
                    while i < number_of_fragments[0]:
                        data, ip_address = sock.recvfrom(1500)

                        client_checksum = unpack("H", data[3:5])
                        client_message = data[5:].decode()
                        client_packet_number = unpack("h", data[1:3])

                        checksum = binascii.crc_hqx(data[:3] + data[5:], 0)

                        if (i == 0):
                            size_of_fragment = len(client_message)
                        if (i == (number_of_fragments[0] - 1)):
                            size_of_last_fragment = len(client_message)

                        if (checksum == client_checksum[0]):
                            if (client_packet_number[0] == (i - 1)):
                                continue
                            print("Packet cislo", client_packet_number[0], "bol prijaty uspesne.")
                            message = message + client_message
                            sock.sendto(pack("c", str.encode("5")), ip_address)
                            i = i + 1
                        else:
                            if (client_packet_number[0] == (i - 1)):
                                continue
                            print("Packet cislo", client_packet_number[0], "bol prijaty NEUSPESNE.")
                            sock.sendto(pack("c", str.encode("6")), ip_address)

                    print("--------------")
                    print("BOLA PRIJATA NOVA SPRAVA")
                    print("Obsah prijatej spravy: ", message)
                    print("Velkost spravy: ", len(message))
                    print("Celkovy pocet packetov: ", number_of_fragments[0])
                    print("Velkost fragmentu: ", size_of_fragment)
                    print("Velkost posledneho fragmentu: ", size_of_last_fragment)
                    print("--------------")

                    pom = pom + 1

                if (type_of_message[0] == b'2'):
                    number_of_fragments = unpack("l", data[6:10])

                    file_name = data[10:].decode()

                    i = 0
                    bytes_array = bytearray()
                    size_of_fragment = 0
                    size_of_last_fragment = 0
                    while i < number_of_fragments[0]:
                        data, ip_address = sock.recvfrom(1500)

                        client_checksum = unpack("H", data[5:7])
                        client_message = data[7:]
                        client_packet_number = unpack("l", data[1:5])

                        checksum = binascii.crc_hqx(data[:5] + data[7:], 0)

                        if (i == 0):
                            size_of_fragment = len(client_message)
                        if (i == (number_of_fragments[0] - 1)):
                            size_of_last_fragment = len(client_message)

                        if (checksum == client_checksum[0]):
                            print("Packet cislo", client_packet_number[0], "bol prijaty uspesne.")
                            if (client_packet_number[0] == (i - 1)):
                                continue
                            for j in range(0, len(client_message)):
                                bytes_array.append(client_message[j])
                            sock.sendto(pack("c", str.encode("5")), ip_address)
                            i = i + 1
                        else:
                            print("Packet cislo", client_packet_number[0], "bol prijaty NEUSPESNE.")
                            sock.sendto(pack("c", str.encode("6")), ip_address)

                    f = open('recieve_files/' + file_name, "wb")
                    f.write(bytes_array)
                    file_stats = os.stat('recieve_files/' + file_name)
                    abs_path = os.path.abspath('recieve_files/' + file_name)

                    print("--------------")
                    print("BOL PRIJATY NOVY SUBORU")
                    print("Subor bol ulozeny do priecinku: recieve_files ")
                    print("Nazov suboru: ", file_name)
                    print("Velkost suboru: ", file_stats.st_size, "B")
                    print("Absolutna cesta suboru: ", abs_path)
                    print("Celkovy pocet packetov: ", number_of_fragments[0])
                    print("Velkost fragmentu: ", size_of_fragment)
                    print("Velkost posledneho fragmentu: ", size_of_last_fragment)
                    print("--------------")
                    f.close()


def client_side(switch, ip_address, sock):
    try:
        data = None

        if (switch == False):
            # get ip address and port of server
            server_ip_address = input("Zadaj IP adresu servera: ")
            server_port = input("Zadaj port servera: ")

            # connect ip address and port into one variable
            server_ip_and_port = (server_ip_address, int(server_port))

            # create socket for client
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # send packet to the server for start conversation
            sock.sendto(pack("c", str.encode("1")), server_ip_and_port)

            # get data from confirming packet
            data, ip_address = sock.recvfrom(1500)
            data = data.decode()

        # check if was sent confirming packet from server
        if (data == "2" or switch == True):
            print("----------")
            print("Uspesne spojenie so serverom: ", ip_address)
            print("----------")

            menu = ''

            while True:
                stop_threads = False
                t1 = threading.Thread(target=keep_alive, args=(lambda: stop_threads, sock, ip_address))
                t1.start()

                menu = input(
                    "Vyber si moznost: (m --> poslat spravu, f --> poslat subor, s --> vymenit si ulohy, e --> skoncit program) :")

                if (menu == "m"):
                    stop_threads = True
                    t1.join()

                    message = input("Napis spravu, ktoru chces poslat: ")

                    print("Velkost spravy: ", len(message))

                    while True:
                        size_of_fragment = input("Zadaj velkost fragmentu: ")
                        if (int(size_of_fragment) > 1467):
                            print("---------")
                            print("Velkost fragmentu je prilis velka.")
                            print("---------")
                            continue
                        else:
                            break

                    number_of_fragments = math.ceil(len(message) / int(size_of_fragment))

                    print("Pocet packetov na odoslanie: ", number_of_fragments)

                    size_of_last_fragment = len(message) % int(size_of_fragment)

                    number_of_errors = input("Zadaj kolko chyb si prajes nasimulovat: ")

                    # PRINT INFO FOR CLIENT
                    print("----------")
                    print("Bude odoslana sprava !")
                    print("Obsah spravy: ", message)
                    print("Velkost spravy: ", len(message))
                    print("Pocet packetov na odoslanie: ", number_of_fragments)
                    print("Velkost fragmentu: ", size_of_fragment)
                    print("Velkost posledneho fragmentu: ", size_of_last_fragment)
                    print("----------")

                    sock.sendto(pack("c", str.encode("3")) +
                                pack("c", str.encode("1")) + pack("h", len(message)) + pack("h", number_of_fragments),
                                ip_address)

                    # create a values for simulating errors
                    list = range(0, int(number_of_fragments))
                    randoms = random.sample(list, int(number_of_errors))
                    randoms.sort()
                    # print(randoms)

                    index = 0
                    i = 0
                    randoms_index = 0
                    pom = 0
                    number_of_except = 0

                    sock.settimeout(1000)

                    while i < number_of_fragments:
                        string = ""
                        tmp = index

                        try:
                            for element in range(int(size_of_fragment)):
                                if (index < len(message)):
                                    string += message[index]
                                    index = index + 1
                            header = pack("c", str.encode("4")) + pack("h", i)
                            checksum = binascii.crc_hqx(header + str.encode(string), 0)
                            if randoms_index < len(randoms):
                                if i == randoms[randoms_index]:
                                    checksum = checksum + 1  # test
                                    randoms_index = randoms_index + 1
                            header = header + pack("H", checksum)
                            sock.sendto(header + str.encode(string), ip_address)

                            if (pom == 0):
                                data, ip_address = sock.recvfrom(1500)

                            sock.settimeout(10)

                            data, ip_address = sock.recvfrom(1500)
                            number_of_except = 0
                            data = data.decode()

                            if (data == '5'):
                                print("Packet číslo ", i, "bol odoslaný úspešne")
                                if(i == number_of_fragments - 1):
                                    print("-----")
                                    print("Správa bola úspešne odoslaná")
                                    print("-----")
                                i = i + 1
                            else:
                                print("Packet číslo ", i, "bol odoslaný NEÚSPEŠNE")
                                index = tmp
                            pom = pom + 1

                        except(socket.timeout):
                            number_of_except = number_of_except + 1
                            if (number_of_except < 3):
                                index = tmp
                                pom = pom + 1
                                continue
                            else:
                                print("----------")
                                print("Server nereaguje, program je ukonceny")
                                exit()

                if (menu == "f"):
                    stop_threads = True
                    # t1.join()

                    path = input("Zadaj celu cestu k suboru: ")
                    name_of_file = os.path.basename(path)
                    data_size = os.path.getsize(path)

                    print("Velkost suboru: ", data_size)

                    while True:
                        size_of_fragment = input("Zadaj velkost fragmentu: ")
                        if (int(size_of_fragment) > 1465):
                            print("---------")
                            print("Velkost fragmentu je prilis velka.")
                            print("---------")
                            continue
                        else:
                            break

                    number_of_fragments = math.ceil(data_size / int(size_of_fragment))

                    print("Pocet packetov na odoslanie: ", number_of_fragments)

                    size_of_last_fragment = int(data_size) % int(size_of_fragment)

                    number_of_errors = input("Zadaj kolko chyb si prajes nasimulovat: ")

                    # PRINT INFO FOR CLIENT
                    print("----------")
                    print("Bude odoslany subor !")
                    print("Nazov suboru: ", name_of_file)
                    print("Absolutna cesta k suboru: ", path)
                    print("Velkost suboru: ", data_size)
                    print("Pocet packetov na odoslanie: ", number_of_fragments)
                    print("Velkost fragmentu: ", size_of_fragment)
                    print("Velkost posledneho fragmentu: ", size_of_last_fragment)
                    print("----------")

                    sock.sendto(pack("c", str.encode("3")) + pack("c", str.encode("2")) +
                                pack("l", data_size) + pack("l", number_of_fragments) + str.encode(name_of_file),
                                ip_address)

                    # create a values for simulating errors
                    list = range(0, int(number_of_fragments))
                    randoms = random.sample(list, int(number_of_errors))
                    randoms.sort()
                    print(randoms)

                    with open(path, "rb") as f:
                        message = f.read()

                    index = 0
                    i = 0
                    randoms_index = 0
                    pom = 0
                    number_of_except = 0
                    while i < number_of_fragments:
                        bytes_array = bytearray()
                        tmp = index

                        try:
                            for element in range(int(size_of_fragment)):
                                if (index < len(message)):
                                    bytes_array.append(message[index])
                                    index = index + 1
                            header = pack("c", str.encode("4")) + pack("l", i)
                            checksum = binascii.crc_hqx(header + bytes_array, 0)
                            if randoms_index < len(randoms):
                                if i == randoms[randoms_index]:
                                    checksum = checksum + 1  # test
                                    randoms_index = randoms_index + 1
                            header = header + pack("H", checksum)
                            sock.sendto(header + bytes_array, ip_address)

                            if (pom == 0):
                                data, ip_address = sock.recvfrom(1500)

                            sock.settimeout(10)

                            data, ip_address = sock.recvfrom(1500)
                            number_of_except = 0
                            data = data.decode()

                            if (data == '5'):
                                print("Packet číslo ", i, "bol odoslaný úspešne")
                                if (i == number_of_fragments - 1):
                                    print("-----")
                                    print("Správa bola úspešne odoslaná")
                                    print("-----")
                                i = i + 1
                            else:
                                print("Packet číslo ", i, "bol odoslaný NEÚSPEŠNE")
                                index = tmp

                            pom = pom + 1

                        except(socket.timeout):
                            number_of_except = number_of_except + 1
                            if (number_of_except < 3):
                                index = tmp
                                pom = pom + 1
                                continue
                            else:
                                print("----------")
                                print("Server nereaguje, program je ukonceny")
                                exit()

                if (menu == "s"):
                    stop_threads = True
                    t1.join()
                    sleep(1)

                    pom = 0
                    number_of_except = 0

                    while True:
                        try:
                            sock.sendto(pack("c", str.encode("7")), ip_address)

                            if (pom == 0):
                                data, ip_address = sock.recvfrom(1500)
                                pom = pom + 1

                            sock.settimeout(10)
                            data, ip_address = sock.recvfrom(1500)
                            number_of_except = 0
                            data = data.decode()
                            switch = True

                            if (data == '7'):
                                print("Vykonavam switch")
                                server_side(switch, ip_address, sock)
                                exit()

                        except(socket.timeout):
                            number_of_except = number_of_except + 1
                            if (number_of_except < 3):
                                pom = pom + 1
                                continue
                            else:
                                print("----------")
                                print("Server nereaguje, program je ukonceny")
                                print("----------")
                                exit()

                if (menu == "e"):
                    stop_threads = True
                    t1.join()

                    sleep(1)

                    pom = 0
                    number_of_except = 0
                    while True:
                        try:
                            sock.sendto(pack("c", str.encode("9")), ip_address)

                            if (pom == 0):
                                data, ip_address = sock.recvfrom(1500)

                            sock.settimeout(10)
                            data, ip_address = sock.recvfrom(1500)
                            number_of_except = 0
                            data = data.decode()

                            if (data == '9'):
                                print("---------------")
                                print("Program sa ukoncuje")
                                print("---------------")
                                exit()
                        except(socket.timeout):
                            number_of_except = number_of_except + 1
                            if (number_of_except < 3):
                                pom = pom + 1
                                continue
                            else:
                                print("----------")
                                print("Server nereaguje, program je ukonceny")
                                print("----------")
                                exit()


    except KeyboardInterrupt:
        stop_threads = True
        exit()


print("Server --> s")
print("Klient --> k")
role = input("Zadaj rolu pod ktorou chces vykonavat proces: ")

if (role == 's'):
    switch = False
    ip_address = None
    sock = None
    server_side(switch, ip_address, sock)
if (role == 'k'):
    switch = False
    ip_address = None
    sock = None
    client_side(switch, ip_address, sock)
