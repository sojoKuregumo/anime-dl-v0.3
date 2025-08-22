# Use an official Python runtime as a parent image
FROM python:3.12

WORKDIR /app

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . /app

# Clean up old session files that might have schema issues
RUN rm -f *.session *.session-journal

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["bash", "web.sh"] # For web service 
#CMD ["bash", "start.sh"] # For worker
