FROM python:3

WORKDIR /usr/src/app
RUN mkdir -p /usr/src/cfg

COPY requirements.txt ./
COPY pyvim/wcp_tests.py /usr/src/app/wcp_tests.py

RUN pip install --no-cache-dir -r requirements.txt
RUN apt update && apt install dnsutils -y

CMD [ "python", "./your-daemon-or-script.py" ]


