import os
import time
import socket
import logging
import threading
from datetime import datetime

SCHED_HOST = "192.168.1.120"
HOST = "0.0.0.0"
INCOME_MANAGER_PORT = 8765
SCHED_PORT = 8767
SERVICE_RESPONSE_PORT = 8768
REMOVE_SERVICE_PORT = 8769


logger = logging.getLogger("income_manager")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

log_dir = "/app/logs"
os.makedirs(log_dir, exist_ok=True)
current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = os.path.join(log_dir, f"{current_datetime}.log")

file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

inter_thread_message = dict()


def income_manager_connection_handler(lock, connection, addr):
    logger.info(f"Connetion from {addr}")
    try:
        while True:
            data = connection.recv(1024)
            if data:
                payload = eval(data.decode("utf-8"))
                logger.info(f"Data received from {addr}: {payload} ")

                client_socket = socket.socket()
                client_socket.connect((SCHED_HOST, SCHED_PORT))
                client_socket.send(data)
                sched_response = client_socket.recv(1024)
                client_socket.close()
                
                logger.info(f"Response from scheduler: {sched_response.decode()}")
                
                if "Request Accepted" in sched_response.decode():
                    while payload["task_name"] not in inter_thread_message:
                        time.sleep(0.1)
                    message = str(inter_thread_message[payload["task_name"]])
                    connection.send(message.encode())

                    lock.acquire()
                    del inter_thread_message[payload["task_name"]]
                    lock.release()
                else:
                    connection.send(sched_response)
                
                connection.close()
                break

    except Exception as err:
        logger.error(f"Connetion error {addr} {payload['task_name']}", str(err))
        connection.close()


def income_manager_server(lock):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, INCOME_MANAGER_PORT))
    logger.info(f"Income manager socket binded to port: {INCOME_MANAGER_PORT}")

    server.listen()
    logger.info("Income manager socket is listening")
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
    logger.info(f"Service response socket binded to port: {SERVICE_RESPONSE_PORT}")

    server.listen()
    logger.info("Service response socket is listening")

    while True:
        connection, addr = server.accept()
        data = connection.recv(1024)
        if data:
            payload = eval(data.decode("utf-8"))
            logger.info(f"Message received from {addr}: {payload}")

            lock.acquire()
            inter_thread_message[payload["task_name"]] = payload["task_response"]
            lock.release()
            
            try:
                client_socket = socket.socket()
                client_socket.connect((SCHED_HOST, REMOVE_SERVICE_PORT))
                client_socket.send(data)
                client_socket.close()
            except Exception as err:
                logger.error(f"Error during request of service removal: {str(err)}")
                client_socket.close()
            
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
