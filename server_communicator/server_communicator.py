import threading
import socket
import select
import queue
import time


# Thread to handle UDP Comms.
class UDPCommsThread(threading.Thread):

    def __init__(self, server_address, udp_port, udp_send_queue, udp_rec_queue):
        # Intialise the thread.
        threading.Thread.__init__(self)

        # Set up the essentials - address and port
        self.server_address = server_address
        self.udp_port = udp_port
        self.udp_send_queue = udp_send_queue
        self.udp_rec_queue = udp_rec_queue

        print("init thread")


    def run(self):

        # Open up the socket for read/write
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.setblocking(False)

            # Just keep sending items from the send queue and into a receive queue for anything received.
            while (1):

                try:
                    # Take anything that is in the Queue and send it on to the server.
                    if self.udp_send_queue.empty() == False:
                        udp_send_str = self.udp_send_queue.get_nowait()
                        numbytes = udp_socket.sendto(bytes(udp_send_str, "utf-8"), (self.server_address, self.udp_port))

                    # Receiving data - prevents blocking.
                    input_sock, output_sock, exception_sock = select.select([udp_socket], [],[udp_socket],0.25)

                    # Check for any responses -
                    for comm_socket in input_sock:
                        if comm_socket is udp_socket:
                            udp_rec_str = udp_socket.recv(1024)
                            #print (udp_rec_str)

                            # Change the below to a receive Queue later.
                            self.udp_rec_queue.put_nowait(udp_rec_str)
                            #print(self.udp_rec_queue.qsize())

                except:
                    print("UDP Send Failure")
                    raise


        print("Exiting " + self.name)
        exit()

# Thread to handle UDP Comms.
class TCPCommsThread(threading.Thread):

    def __init__(self, server_address, tcp_port, tcp_send_queue, tcp_rec_queue):
        # Intialise the thread.
        threading.Thread.__init__(self)

        # Set up the essentials - address and port
        self.server_address = server_address
        self.tcp_port = tcp_port
        self.tcp_send_queue = tcp_send_queue
        self.tcp_rec_queue = tcp_rec_queue

    def run(self):

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:

            # Connect to server and send data
            tcp_socket.connect((self.server_address, self.tcp_port))

            while (1):

                try:
                    # send anything out that needs to be sent.
                    if not self.tcp_send_queue.empty():
                        tcp_str = self.tcp_send_queue.get_nowait()
                        tcp_socket.sendall(bytes(tcp_str + "\n", "utf-8"))

                    # Wait a short period of time for anything on TCP Socket.
                    input_sock, output_sock, exception_sock = select.select([tcp_socket], [], [tcp_socket], 0.25)

                    # Go through sockets that got input
                    for CommSocket in input_sock:
                        if CommSocket is tcp_socket:
                            tcp_rec_str = tcp_socket.recv(1024)
                            self.tcp_rec_queue.put_nowait(tcp_rec_str)
                except:
                    print("TCP Send Failure")
                    raise

class server_communicator:

    def __init__(self, server_address, udp_server_port, udp_send_queue, udp_rec_queue, tcp_server_port, tcp_send_queue, tcp_rec_queue):
        self.server_address = server_address
        self.udp_server_port = udp_server_port
        self.tcp_server_port = tcp_server_port

        self.udp_comms_thread = UDPCommsThread(server_address, udp_server_port, udp_send_queue, udp_rec_queue)

        # Start the 2 threads to deal with the Comms - UDP for attacks, skips, etc.  TCP is used for managing session, etc.
        # Both threads are set up a Daemon threads, so they will be killed when the main thread exits.
        #self.udp_comms_thread.setDaemon(True)
        self.udp_comms_thread.start()

        self.tcp_comms_thread = TCPCommsThread(server_address, tcp_server_port, tcp_send_queue, tcp_rec_queue)

        # Start the 2 threads to deal with the Comms - UDP for attacks, skips, etc.  TCP is used for managing session, etc.
        # Both threads are set up a Daemon threads, so they will be killed when the main thread exits.
        #self.udp_comms_thread.setDaemon(True)
        self.udp_comms_thread.start()



'''
class Mess:
    def __init__(self, qu):
        self.que = qu

    def print_all_items(self):
        while self.que.empty() is False:
            print(self.que.get_nowait())


if __name__ == "__main__":
    import queue

    q = queue.Queue()

    try_mess = Mess(q)

    for i in range(10):
        q.put_nowait(i)

    try_mess.print_all_items()

'''

if __name__ == "__main__":

    uq_send = queue.Queue()
    uq_rec = queue.Queue()

    for i in range(10000):
        uq_send.put_nowait("{}BS String to Search For TCPDUMP".format(i))

    tq_send = queue.Queue()
    tq_rec = queue.Queue()


    for i in range(10):
        tq_send.put_nowait(i+100)

    server_comm = server_communicator("127.0.0.1", 9999, uq_send, uq_rec, 9998, tq_send, tq_rec )

    time.sleep(5)
    print("checking out the queue")
    while uq_rec.empty() is False:
        print(uq_rec.get_nowait())

