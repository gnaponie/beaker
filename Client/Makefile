
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

.PHONY: build
build:
	env PYTHONPATH=../Common:src:$${PYTHONPATH:+:$$PYTHONPATH} \
	    python setup.py build

.PHONY: install
install:
	python setup.py install -O1 --skip-build --root $(DESTDIR)

.PHONY: clean
clean:
	python setup.py clean
	rm -rf build

.PHONY: check
check:
	./run-tests.sh

.PHONY: devel
devel:
	DESTDIR="/" make install
