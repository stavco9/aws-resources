#!/bin/bash
# Update the system
sudo yum update -y

# Install Docker
# Use 'amazon-linux-extras install docker' for Amazon Linux 2
# Use 'yum install -y docker' for Amazon Linux 2023
if grep -q "Amazon Linux 2" /etc/os-release; then
    sudo amazon-linux-extras install docker -y
else
    sudo yum install -y docker
fi

# Start the Docker service
sudo service docker start

# Enable Docker to start on boot
sudo systemctl enable docker.service

# Add the ec2-user to the docker group
sudo usermod -a -G docker ec2-user

mkdir /app
echo "<html><body><h2>Hello from Nginx Docker Container!</h2></body></html>" > /app/index.html

# Install Nginx Image
docker run -d -p 8080:80 --name nginx-container -v /app:/usr/share/nginx/html nginx:mainline-alpine3.23-slim
