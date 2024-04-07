import socket
import threading
import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

SCHED_HOST = "192.168.1.111"
SCHED_PORT = 8767


def connection_handler(thread, connection, addr):
    logging.info(f"Connetion from {addr}")
    try:
        while True:
            data = connection.recv(1024)
            if data:
                logging.info(f"Thread {thread} received data from {addr}: {data} ")
                connection.send(data)

                client_socket = socket.socket()
                client_socket.connect((SCHED_HOST, SCHED_PORT))

                message = data

                client_socket.send(message)
                client_socket.close()

    except Exception:
        connection.close()


def main():
    PORT = 8765
    HOST = "0.0.0.0"
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    logging.info(f"socket binded to port: {PORT}")

    server.listen()
    logging.info("socket is listening")
    thread = 0

    while True:
        connection, addr = server.accept()

        x = threading.Thread(target=connection_handler, args=(1, connection, addr))
        x.start()
        thread += 1

    server.close()


if __name__ == "__main__":
    main()
