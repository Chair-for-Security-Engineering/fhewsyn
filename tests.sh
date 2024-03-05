#!/bin/sh

case "${1}" in
boolean|lut?|lut?fa);;
*) echo "usage: ./tests.sh <type>" 1>&2; exit 1;;
esac

{
	echo "[+] Generating add4-${1}" 1>&2;
	./build.sh hal add4-${1};
	echo "";

	echo "[+] Generating calculator-${1}" 1>&2;
	./build.sh hal calculator-${1};
	echo "";

	echo "[+] Generating sqrt-${1}" 1>&2;
	./build.sh hal sqrt-${1};
	echo "";
} | xclip
