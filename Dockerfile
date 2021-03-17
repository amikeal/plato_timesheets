# Use the Selenium node image for headless operation
FROM selenium/node-chrome

# Need to install distutils in order to install pip, in order to install selenium...
RUN sudo apt-get update && sudo apt-get install -y python3-distutils

# Install pip the hard way
WORKDIR /app
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    sudo python3 get-pip.py --no-wheel --no-setuptools

# Now install the Python selenium library
RUN pip install selenium

# Copy in the code
ADD . /app

# Set environment variables for the script
ENV CHROME_PATH='/usr/bin/google-chrome'
ENV DRIVER_PATH='/usr/bin/chromedriver'

# Used for debugging / interactive REPL
#CMD ["python3"]

# Run the Python script and pass args as appropriate
ENTRYPOINT ["python3", "./timesheets.py"]