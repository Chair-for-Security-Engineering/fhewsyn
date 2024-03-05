#!/usr/bin/env python3
import builtins
import hal_py
import sys

sys.path.append("./src")
from common import *

NAME = sys.argv[0][4:-2]
HGL = "src/boolean.lib"


def fhedeck_net_source_name(net, inputs, gates):
    if len(net.sources) == 0:
        assert net.is_global_input_net()
        return f"ct_{inputs[net]}", f"ct_{inputs[net]}_clear"

    assert len(net.sources) == 1
    gate = net.sources[0].gate

    if str(gate.type) == "HAL_GND":
        return None, None
    if str(gate.type) == "HAL_VDD":
        return "1", "1"

    idx = gates.index(gate)
    return f"gout{idx}", f"gout{idx}_clear"


def fhedeck_print_gates(inputs, gates, ciphertext=True, cleartext=False):
    bootstraps = 0

    print((
        f"{TAB}auto fand2 = [](long i, long t) -> long {{\n"
        f"{TAB}{TAB}switch (i) {{\n"
        f"{TAB}{TAB}{TAB}case 0:  return 0;\n"
        f"{TAB}{TAB}{TAB}case 1:  return 0;\n"
        f"{TAB}{TAB}{TAB}case 2:  return 0;\n"
        f"{TAB}{TAB}{TAB}case 3:  return 1;\n"
        f"{TAB}{TAB}{TAB}default: assert(0);\n"
        f"{TAB}{TAB}}}\n"
        f"{TAB}}};\n"
        f"{TAB}RotationPoly and2 = ctx.genrate_lut(fand2);\n"))
    print((
        f"{TAB}auto fnand2 = [](long i, long t) -> long {{\n"
        f"{TAB}{TAB}switch (i) {{\n"
        f"{TAB}{TAB}{TAB}case 0:  return 1;\n"
        f"{TAB}{TAB}{TAB}case 1:  return 1;\n"
        f"{TAB}{TAB}{TAB}case 2:  return 1;\n"
        f"{TAB}{TAB}{TAB}case 3:  return 0;\n"
        f"{TAB}{TAB}{TAB}default: assert(0);\n"
        f"{TAB}{TAB}}}\n"
        f"{TAB}}};\n"
        f"{TAB}RotationPoly nand2 = ctx.genrate_lut(fnand2);\n"))
    print((
        f"{TAB}auto for2 = [](long i, long t) -> long {{\n"
        f"{TAB}{TAB}switch (i) {{\n"
        f"{TAB}{TAB}{TAB}case 0:  return 0;\n"
        f"{TAB}{TAB}{TAB}case 1:  return 1;\n"
        f"{TAB}{TAB}{TAB}case 2:  return 1;\n"
        f"{TAB}{TAB}{TAB}case 3:  return 1;\n"
        f"{TAB}{TAB}{TAB}default: assert(0);\n"
        f"{TAB}{TAB}}}\n"
        f"{TAB}}};\n"
        f"{TAB}RotationPoly or2 = ctx.genrate_lut(for2);\n"))
    print((
        f"{TAB}auto fnor2 = [](long i, long t) -> long {{\n"
        f"{TAB}{TAB}switch (i) {{\n"
        f"{TAB}{TAB}{TAB}case 0:  return 1;\n"
        f"{TAB}{TAB}{TAB}case 1:  return 0;\n"
        f"{TAB}{TAB}{TAB}case 2:  return 0;\n"
        f"{TAB}{TAB}{TAB}case 3:  return 0;\n"
        f"{TAB}{TAB}{TAB}default: assert(0);\n"
        f"{TAB}{TAB}}}\n"
        f"{TAB}}};\n"
        f"{TAB}RotationPoly nor2 = ctx.genrate_lut(fnor2);\n"))
    print((
        f"{TAB}auto fxor2 = [](long i, long t) -> long {{\n"
        f"{TAB}{TAB}switch (i) {{\n"
        f"{TAB}{TAB}{TAB}case 0:  return 0;\n"
        f"{TAB}{TAB}{TAB}case 1:  return 1;\n"
        f"{TAB}{TAB}{TAB}case 2:  return 1;\n"
        f"{TAB}{TAB}{TAB}case 3:  return 0;\n"
        f"{TAB}{TAB}{TAB}default: assert(0);\n"
        f"{TAB}{TAB}}}\n"
        f"{TAB}}};\n"
        f"{TAB}RotationPoly xor2 = ctx.genrate_lut(fxor2);\n"))
    print((
        f"{TAB}auto fxnor2 = [](long i, long t) -> long {{\n"
        f"{TAB}{TAB}switch (i) {{\n"
        f"{TAB}{TAB}{TAB}case 0:  return 1;\n"
        f"{TAB}{TAB}{TAB}case 1:  return 0;\n"
        f"{TAB}{TAB}{TAB}case 2:  return 0;\n"
        f"{TAB}{TAB}{TAB}case 3:  return 1;\n"
        f"{TAB}{TAB}{TAB}default: assert(0);\n"
        f"{TAB}{TAB}}}\n"
        f"{TAB}}};\n"
        f"{TAB}RotationPoly xnor2 = ctx.genrate_lut(fxnor2);\n"))

    for id, gate in enumerate(gates):
        type = str(gate.type)

        a = fhedeck_net_source_name(gate.get_fan_in_net("A"), inputs, gates)
        if type == "inv":
            print(f"{TAB}std::cerr << \"\\rINV{id}   \";");
            if ciphertext:
                print(f"{TAB}Ciphertext gout{id} = 1 - {a[0]};\n")
            if cleartext:
                print(f"{TAB}long gout{id}_clear = 1 - {a[1]};\n")

            continue

        b = fhedeck_net_source_name(gate.get_fan_in_net("B"), inputs, gates)
        if type == "imux2":
            s = fhedeck_net_source_name(gate.get_fan_in_net("S"), inputs, gates)
            print(f"{TAB}std::cerr << \"\\rIMUX{id}  \";");
            if ciphertext:
                print(f"{TAB}Ciphertext gin{id}A = 2 * {a[0]} + {s[0]};")
                print(f"{TAB}Ciphertext gout{id}A = ctx.eval_lut(&gin{id}A, and2);")
                print(f"{TAB}Ciphertext gin{id}B = 2 * {b[0]} + (1 - {s[0]});")
                print(f"{TAB}Ciphertext gout{id}B = ctx.eval_lut(&gin{id}B, and2);")
                print(f"{TAB}Ciphertext gout{id} = gout{id}A + gout{id}B;")
            if cleartext:
                print(f"{TAB}long gin{id}A_clear = 2 * {a[1]} + {s[1]};")
                print(f"{TAB}long gout{id}A_clear = fand2(gin{id}A_clear, 4);")
                print(f"{TAB}long gin{id}B_clear = 2 * {b[1]} + (1 - {s[1]});")
                print(f"{TAB}long gout{id}B_clear = fand2(gin{id}B_clear, 4);")
                print(f"{TAB}long gout{id}_clear = gout{id}A_clear + gout{id}B_clear;")

            bootstraps += 2
            continue

        if "yn" in type:
            if ciphertext:
                gin = f"2 * {a[0]} + (1 - {b[0]})"
            if cleartext:
                gin_clear = f"2 * {a[1]} + (1 - {b[1]})"
            lut = type.replace("yn", "")
        elif "ny" in type:
            if ciphertext:
                gin = f"2 * (1 - {a[0]}) + {b[0]}"
            if cleartext:
                gin_clear = f"2 * (1 - {a[1]}) + {b[1]}"
            lut = type.replace("ny", "")
        else:
            if ciphertext:
                gin = f"2 * {a[0]} + {b[0]}"
            if cleartext:
                gin_clear = f"2 * {a[1]} + {b[1]}"
            lut = type

        print(f"{TAB}std::cerr << \"\\rLUT{id}   \";");
        if ciphertext:
            print(f"{TAB}Ciphertext gin{id} = {gin};")
            print(f"{TAB}Ciphertext gout{id} = ctx.eval_lut(&gin{id}, {lut});")
        if cleartext:
            print(f"{TAB}auto gin{id}_clear = {gin_clear};")
            print(f"{TAB}auto gout{id}_clear = f{lut}(gin{id}_clear, 4);")

        if cleartext and ciphertext:
            print(f"{TAB}assert(ctx.decrypt(&gout{id}) == gout{id}_clear);")
        bootstraps += 1
    print("")

    return bootstraps


hal_py.plugin_manager.load_all_plugins()
netlist = hal_py.NetlistFactory.load_netlist(sys.argv[0], HGL)
sum = builtins.sum
set = builtins.set
bench_print_header()

inputs = globals_get_names(netlist.top_module.input_pins)
fhedeck_print_inputs(NAME, inputs)

gates = netlist_sort_topo(netlist)
bootstraps = fhedeck_print_gates(inputs, gates)

outputs = globals_get_names(netlist.top_module.output_pins)
fhedeck_print_outputs(inputs, gates, outputs, source=fhedeck_net_source_name)

bench_print_footer(NAME, "tfhe_11_NTT")
print(f"gates:      {len(netlist.gates):4d}", file=sys.stderr)
print(f"bootstraps: {bootstraps:4d}", file=sys.stderr)
