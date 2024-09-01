FROM fedora

# Install necessary libs 
RUN yum -y install docker
RUN dnf install python3-pip
RUN pip install docker

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY ./app /app

# Define a volume for storing logs
VOLUME /app/logs 

# Run income_manager.py when the container launches
CMD ["python", "income_manager.py"]