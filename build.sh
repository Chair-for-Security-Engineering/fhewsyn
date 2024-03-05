#!/bin/sh

usage() {
	printf "usage: ./build.sh [-h] <command>\n\n"    1>&2
	printf "possible commands are:\n"                1>&2
	printf "  help       show help\n"                1>&2
	printf "  boolean    run yosys (Boolean mode)\n" 1>&2
	printf "  lut        run yosys (lut mode)\n"     1>&2
	printf "  lutfa      run yosys (lutfa mode)\n"   1>&2
	printf "  google     run yosys (Google mode)\n"  1>&2
	printf "  hal        run hal\n"                  1>&2
}

usage_boolean() {
	printf "usage: ./build.sh boolean [-a|-h] [design]\n\n" 1>&2
	printf "  run yosys in Boolean mode\n\n"                1>&2
	printf "possible options are:\n"                        1>&2
	printf "  -h    show help\n"                            1>&2
	printf "  -a    run for all netlists\n"                 1>&2
}

usage_lut() {
	printf "usage: ./build.sh lut [-a|-h|-2|-3|-4|-5] [design]\n\n" 1>&2
	printf "  run yosys in lut mode\n\n"                            1>&2
	printf "possible options are:\n"                                1>&2
	printf "  -h    show help\n"                                    1>&2
	printf "  -a    run for all netlists\n"                         1>&2
	printf "  -2    use maximum lut size 2\n"                       1>&2
	printf "  -3    use maximum lut size 3\n"                       1>&2
	printf "  -4    use maximum lut size 4\n"                       1>&2
	printf "  -5    use maximum lut size 5\n"                       1>&2
}

usage_lutfa() {
	printf "usage: ./build.sh lutfa [-a|-h|-2|-3|-4|-5] [design]\n\n" 1>&2
	printf "  run yosys in lutfa mode\n\n"                            1>&2
	printf "possible options are:\n"                                  1>&2
	printf "  -h    show help\n"                                      1>&2
	printf "  -a    run for all netlists\n"                           1>&2
	printf "  -2    use maximum lut size 2\n"                         1>&2
	printf "  -3    use maximum lut size 3\n"                         1>&2
	printf "  -4    use maximum lut size 4\n"                         1>&2
	printf "  -5    use maximum lut size 5\n"                         1>&2
}

usage_google() {
	printf "usage: ./build.sh google [-a|-h] [design]\n\n" 1>&2
	printf "  run yosys in Google's Boolean mode\n\n"      1>&2
	printf "possible options are:\n"                       1>&2
	printf "  -h    show help\n"                           1>&2
	printf "  -a    run for all netlists\n"                1>&2
}

usage_hal() {
	printf "usage: ./build.sh hal [-a|-h] [design]\n\n" 1>&2
	printf "  run hal\n\n"                              1>&2
	printf "possible options are:\n"                    1>&2
	printf "  -h    show help\n"                        1>&2
	printf "  -a    run for all netlists\n"             1>&2
}

cmd_boolean() {
	local all=0 ret=1
	while getopts 'ha' o; do
		case "${o}" in
		h) usage_test; return;;
		a) all=1;;
		esac
	done
	shift $((OPTIND - 1))
	OPTIND=0

	if test -n "${1}"; then ret=0
		netlist="data/${1}.v"
		sed \
			-e "s:DESIGN:${1}:" \
			-e "s:NETLIST:${netlist}:" \
			src/boolean.ys > out/run.ys
		yosys -q -s out/run.ys "${netlist}" || exit 1
	fi

	if test ${all} -eq 1; then ret=0
		for netlist in data/*.v; do
			design="${netlist#data/}"
			design="${design%.v}"
			sed \
				-e "s:DESIGN:${design}:" \
				-e "s:NETLIST:${netlist}:" \
				src/boolean.ys > out/run.ys
			yosys -q -s out/run.ys "${netlist}" || exit 1
		done
	fi

	test ${ret} -eq 1 && { usage_boolean; exit 1; }
	return 0
}

cmd_lut() {
	local all=0 ret=1 lut=3
	while getopts 'ha2345' o; do
		case "${o}" in
		h) usage_test; return;;
		a) all=1;;
		2) lut=2;;
		3) lut=3;;
		4) lut=4;;
		5) lut=5;;
		esac
	done
	shift $((OPTIND - 1))
	OPTIND=0

	if test -n "${1}"; then ret=0
		netlist="data/${1}.v"
		sed \
			-e "s:DESIGN:${1}:" \
			-e "s:LUTSIZE:${lut}:" \
			-e "s:NETLIST:${netlist}:" \
			src/lut.ys > out/run.ys
		yosys -q -s out/run.ys "${netlist}" || exit 1
	fi

	if test ${all} -eq 1; then ret=0
		for netlist in data/*.v; do
			design="${netlist#data/}"
			design="${design%.v}"
			sed \
				-e "s:DESIGN:${design}:" \
				-e "s:LUTSIZE:${lut}:" \
				-e "s:NETLIST:${netlist}:" \
				src/lut.ys > out/run.ys
			yosys -q -s out/run.ys "${netlist}" || exit 1
		done
	fi

	test ${ret} -eq 1 && { usage_lut; exit 1; }
	return 0
}

cmd_lutfa() {
	local all=0 ret=1 lut=3
	while getopts 'ha2345' o; do
		case "${o}" in
		h) usage_test; return;;
		a) all=1;;
		2) lut=2;;
		3) lut=3;;
		4) lut=4;;
		5) lut=5;;
		esac
	done
	shift $((OPTIND - 1))
	OPTIND=0

	if test -n "${1}"; then ret=0
		netlist="data/${1}.v"
		sed \
			-e "s:DESIGN:${1}:" \
			-e "s:LUTSIZE:${lut}:" \
			-e "s:NETLIST:${netlist}:" \
			src/lutfa.ys > out/run.ys
		yosys -q -s out/run.ys "${netlist}" || exit 1
	fi

	if test ${all} -eq 1; then ret=0
		for netlist in data/*.v; do
			design="${netlist#data/}"
			design="${design%.v}"
			sed \
				-e "s:DESIGN:${design}:" \
				-e "s:LUTSIZE:${lut}:" \
				-e "s:NETLIST:${netlist}:" \
				src/lutfa.ys > out/run.ys
			yosys -q -s out/run.ys "${netlist}" || exit 1
		done
	fi

	test ${ret} -eq 1 && { usage_lutfa; exit 1; }
	return 0
}

cmd_google() {
	local all=0 ret=1
	while getopts 'ha' o; do
		case "${o}" in
		h) usage_test; return;;
		a) all=1;;
		esac
	done
	shift $((OPTIND - 1))
	OPTIND=0

	if test -n "${1}"; then ret=0
		netlist="data/${1}.v"
		sed \
			-e "s:DESIGN:${1}:" \
			-e "s:NETLIST:${netlist}:" \
			src/google.ys > out/run.ys
		yosys -q -s out/run.ys "${netlist}" || exit 1
	fi

	if test ${all} -eq 1; then ret=0
		for netlist in data/*.v; do
			design="${netlist#data/}"
			design="${design%.v}"
			sed \
				-e "s:DESIGN:${design}:" \
				-e "s:NETLIST:${netlist}:" \
				src/google.ys > out/run.ys
			yosys -q -s out/run.ys "${netlist}" || exit 1
		done
	fi

	test ${ret} -eq 1 && { usage_google; exit 1; }
	return 0
}

cmd_hal() {
	local all=0 ret=1
	while getopts 'ha' o; do
		case "${o}" in
		h) usage_test; return;;
		a) all=1;;
		esac
	done
	shift $((OPTIND - 1))
	OPTIND=0

	if test -n "${1}"; then ret=0
		case "${1}" in
		*boolean*) hal --log.enabled false --python-script src/boolean.py --python-args "out/${1}.v";;
		*lut2*)    hal --log.enabled false --python-script src/lut.py --python-args "out/${1}.v 2";;
		*lut3*)    hal --log.enabled false --python-script src/lut.py --python-args "out/${1}.v 3";;
		*lut4*)    hal --log.enabled false --python-script src/lut.py --python-args "out/${1}.v 4";;
		*lut5*)    hal --log.enabled false --python-script src/lut.py --python-args "out/${1}.v 5";;
		*google*)  hal --log.enabled false --python-script src/boolean.py --python-args "out/${1}.v";;
		esac
	fi

	if test ${all} -eq 1; then ret=0
		for netlist in out/*.v; do
			design="${netlist#out/}"
			design="${design%.v}"

			echo "[+] ${design}" 1>&2
			case "${netlist}" in
			*boolean*) hal --log.enabled false --python-script src/boolean.py --python-args "${netlist}";;
			*lut2*)    hal --log.enabled false --python-script src/lut.py --python-args "${netlist} 2";;
			*lut3*)    hal --log.enabled false --python-script src/lut.py --python-args "${netlist} 3";;
			*lut4*)    hal --log.enabled false --python-script src/lut.py --python-args "${netlist} 4";;
			*lut5*)    hal --log.enabled false --python-script src/lut.py --python-args "${netlist} 5";;
			*google*)  hal --log.enabled false --python-script src/boolean.py --python-args "${netlist}";;
			esac
		done
	fi

	test ${ret} -eq 1 && { usage_hal; exit 1; }
	return 0
}

case "${1}" in
	'h'|'-h'|'help') shift; usage; exit 0;;
	'boolean')       shift; cmd_boolean "${@}";;
	'lut')           shift; cmd_lut "${@}";;
	'lutfa')         shift; cmd_lutfa "${@}";;
	'hal')           shift; cmd_hal "${@}";;
	'google')        shift; cmd_google "${@}";;
	*)               shift; usage; exit 1;;
esac
