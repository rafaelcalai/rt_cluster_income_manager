import socket
import threading
import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

SCHED_HOST = "192.168.1.111"
HOST = "0.0.0.0"
INCOME_MANAGER_PORT = 8765
SCHED_PORT = 8767
SERVICE_RESPONSE_PORT = 8768


def income_manager_connection_handler(thread, connection, addr):
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


def income_manager_server(thread):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, INCOME_MANAGER_PORT))
    logging.info(f"Income manager socket binded to port: {INCOME_MANAGER_PORT}")

    server.listen()
    logging.info("Income manager socket is listening")
    thread = 0

    while True:
        connection, addr = server.accept()

        x = threading.Thread(
            target=income_manager_connection_handler, args=(1, connection, addr)
        )
        x.start()
        thread += 1

    server.close()


def service_response_server(thread):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, SERVICE_RESPONSE_PORT))
    logging.info(f"Service response socket binded to port: {SERVICE_RESPONSE_PORT}")

    server.listen()
    logging.info("Service response socket is listening")
    thread = 0

    while True:
        connection, addr = server.accept()
        data = connection.recv(1024)
        if data:
            logging.info(f"Message received from {addr}: {data}")

    server.close()


def main():
    income_manager_server_thread = threading.Thread(
        target=income_manager_server, args=(1,)
    )
    service_response_server_thread = threading.Thread(
        target=service_response_server, args=(2,)
    )
    income_manager_server_thread.start()
    service_response_server_thread.start()
    income_manager_server_thread.join()
    service_response_server_thread.join()


if __name__ == "__main__":
    main()
