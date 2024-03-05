#!/bin/sh

BENCH="${BENCH:-../fhedeck.git/bench}"

printf "#!/bin/sh\n\n" > "${BENCH}/run.sh"
chmod +x "${BENCH}/run.sh"

for netlist in data/*.v; do
	design="${netlist#data/}"
	design="${design%.v}"
	name="$(echo ${design} | tr '-' '_')"

	for arch in boolean lut2 lut2fa lut3 lut3fa lut4 lut4fa; do
		echo "[+] ${design}-${arch}" 1>&2
		./build.sh hal ${design}-${arch} > "${BENCH}/${name}_${arch}.cpp"

		echo "echo '[+] ${name}_${arch}'" >> "${BENCH}/run.sh"
		echo "build/bench/${name}_${arch} 2> /dev/null | grep 'BM'" >> "${BENCH}/run.sh"
	done
done
