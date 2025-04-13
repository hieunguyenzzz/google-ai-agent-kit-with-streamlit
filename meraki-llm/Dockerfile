FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install uv
RUN pip install uv

# Copy requirements from the root and install dependencies
# Note: We copy requirements.txt from the parent directory
COPY ./requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy the agent code into the container
COPY ./agent ./agent

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run the application
# Ensure the agent directory 'agent' is correctly referenced relative to the WORKDIR
CMD ["adk", "api_server"] 