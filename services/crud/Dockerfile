FROM ubuntu@sha256:25895062172a2f39ae36da530f3db244b507d7ffb1c4dd42a3a487b5b446e996

WORKDIR /app

RUN apt update
RUN apt install cmake build-essential -y
RUN apt install libasio-dev -y
RUN apt install python3 -y

COPY . /app
# RUN cmake . && make

# CMD ["./crud_task", "8000", "/data.bin"]
CMD ["./runner.py", "./crud_task", "8000", "/app/data.bin"]
