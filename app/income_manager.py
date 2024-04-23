import socket
import threading
import logging
import time

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

SCHED_HOST = "192.168.1.111"
HOST = "0.0.0.0"
INCOME_MANAGER_PORT = 8765
SCHED_PORT = 8767
SERVICE_RESPONSE_PORT = 8768


inter_thread_message = dict()


def income_manager_connection_handler(lock, connection, addr):
    logging.info(f"Connetion from {addr}")
    try:
        while True:
            data = connection.recv(1024)
            if data:
                payload = eval(data.decode("utf-8"))
                logging.info(f"Data received from {addr}: {payload} ")

                client_socket = socket.socket()
                client_socket.connect((SCHED_HOST, SCHED_PORT))
                client_socket.send(data)
                client_socket.close()

                while payload["task_name"] not in inter_thread_message:
                    time.sleep(0.1)

                message = str(inter_thread_message[payload["task_name"]])
                connection.send(message.encode())

                lock.acquire()
                del inter_thread_message[payload["task_name"]]
                lock.release()
                break

    except Exception:
        connection.close()


def income_manager_server(lock):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, INCOME_MANAGER_PORT))
    logging.info(f"Income manager socket binded to port: {INCOME_MANAGER_PORT}")

    server.listen()
    logging.info("Income manager socket is listening")
    thread = 0

    while True:
        connection, addr = server.accept()

        x = threading.Thread(
            target=income_manager_connection_handler, args=(lock, connection, addr)
        )
        x.start()
        thread += 1

    server.close()


def service_response_server(lock):
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
            payload = eval(data.decode("utf-8"))
            logging.info(f"Message received from {addr}: {payload}")

            lock.acquire()
            inter_thread_message[payload["task_name"]] = payload["task_response"]
            lock.release()

    server.close()


def main():
    lock = threading.Lock()

    income_manager_server_thread = threading.Thread(
        target=income_manager_server, args=(lock,)
    )

    service_response_server_thread = threading.Thread(
        target=service_response_server, args=(lock,)
    )

    income_manager_server_thread.start()
    service_response_server_thread.start()

    income_manager_server_thread.join()
    service_response_server_thread.join()

    lock.release()


if __name__ == "__main__":
    main()
