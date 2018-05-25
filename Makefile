export AMPY_PORT=/dev/ttyUSB0

run:
	ampy run main.py

download: micropython-lib

micropython-lib:
	git clone https://github.com/micropython/micropython-lib


