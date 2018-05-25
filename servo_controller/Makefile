
OTACLIDIR=../../micropython-OTA/otacli
OTASERV=$(OTACLIDIR)/../otaserv/otaserv.sh
PORT=/dev/ttyUSB0
export AMPY_PORT=$(PORT)

install: otacli.py
	make -C .. download
	make smallinstall
	ampy put ../micropython-lib/utarfile/utarfile.py
	ampy put ../micropython-lib/os.path/os/path.py ospath.py
	ampy put otacli.py

smallinstall:
	ampy put main.py
	ampy put servo.py
	ampy put config.py
	ampy put config_local.py

otacli.py: $(OTACLIDIR)/otacli.py
	cp $(OTACLIDIR)/otacli.py ./

serve: otacli.py
	$(OTASERV)

