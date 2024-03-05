#!/usr/bin/env python3
import builtins
import hal_py
import sys

sys.path.append("./src")
from common import *

NAME = sys.argv[0][4:-2]
LMAX = int(sys.argv[1])
LUTS = range(1, LMAX + 1)
HGL = "src/lut.hgl"

PARAMS = [ "", "",
    "tfhe_11_NTT",
    "tfhe_11_NTT_amortized",
    "tfhe_12_NTT_amortized"
][LMAX]


def adder_follow_chain(gate):
    while True:
        yield gate

        co = gate.get_fan_out_net("CO")
        if len(co.destinations) == 0:
            break

        gate, net = co.destinations[0].gate, co.destinations[0].net
        if str(gate.type) != "FA" or gate.get_fan_in_net("CI") != net:
            break


def fhedeck_net_source_name(net, inputs, groups):
    if len(net.sources) == 0:
        assert net.is_global_input_net()
        return f"ct_{inputs[net]}", f"ct_{inputs[net]}_clear"

    assert len(net.sources) == 1
    gate = net.sources[0].gate

    if str(gate.type) == "HAL_GND":
        return "0", "0"
    if str(gate.type) == "HAL_VDD":
        return "1", "1"

    gid, gidx = groups_get_index(gate, groups)
    if str(gate.type) == "FA" and net == gate.get_fan_out_net("CO"):
        gidx += 1

    if gid != None and gidx != None:
        return f"gout{gid}[{gidx}]", f"gout{gid}_clear[{gidx}]"

    return None, None


def fhedeck_print_groups(inputs, groups, ciphertext=True, cleartext=False):
    bootstraps = 0

    print(f"{TAB}std::vector<RotationPoly> decomp;")
    print(f"{TAB}std::vector<long (*)(long)> fdecomp;")
    for i in range(LMAX):
        cases = "\n"
        for j in range(1 << LMAX):
            cases += f"{TAB}{TAB}{TAB}case {j:2d}: return {(j >> i) & 1};\n"
        cases += f"{TAB}{TAB}{TAB}default: assert(0);\n"

        print((
            f"{TAB}auto decomp{i} = [](long I) -> long {{\n"
            f"{TAB}{TAB}switch (I) {{{cases}{TAB}{TAB}}};\n"
            f"{TAB}}};\n"
            f"{TAB}decomp.push_back(ctx.genrate_lut(decomp{i}));\n"
            f"{TAB}fdecomp.push_back(decomp{i});"))
    print((
        f"{TAB}auto vdecomp = [fdecomp](long I) -> std::vector<long> {{\n"
        f"{TAB}{TAB}std::vector<long> ret;\n"
        f"{TAB}{TAB}for (size_t i = 0; i < {LMAX}; ++i)\n"
        f"{TAB}{TAB}{TAB}ret.push_back(fdecomp[i](I));\n"
        f"{TAB}{TAB}return ret;\n"
        f"{TAB}}};"))
    print()

    for id, group in enumerate(groups):
        types = []
        for gate in group:
            if str(gate.type) in ["INV", "LUT1"]:
                types.append("INV")
            elif str(gate.type).startswith("LUT"):
                types.append("LUT")
            else:
                types.append(str(gate.type))
        assert all(map(lambda t: t == types[0], types))

        if "INV" in types:
            assert(len(group) == 1)
            gate = group[0]

            I = "I0" if str(gate.type) == "LUT1" else "I"
            name = fhedeck_net_source_name(gate.get_fan_in_net(I), inputs, groups)

            print(f"{TAB}std::cerr << \"\\rINV{id}   \";");
            if ciphertext:
                print(f"{TAB}std::vector<Ciphertext> gout{id};")
                if name[0] == "0":
                    print(f"{TAB}gout{id}.push_back(ctx.encrypt_public(1));")
                elif name[0] == "1":
                    print(f"{TAB}gout{id}.push_back(ctx.encrypt_public(0));")
                else:
                    print(f"{TAB}gout{id}.push_back(1 - {name[0]});")
            if cleartext:
                print(f"{TAB}std::vector<long> gout{id}_clear;")
                if name[1] == "0":
                    print(f"{TAB}gout{id}_clear.push_back(1);")
                elif name[1] == "1":
                    print(f"{TAB}gout{id}_clear.push_back(0);")
                else:
                    print(f"{TAB}gout{id}_clear.push_back(1 - {name[1]});")
            if ciphertext and cleartext:
                print(f"{TAB}assert(ctx.decrypt(&gout{id}[0]) == gout{id}_clear[0]);")
            print("")
        elif "FA" in types:
            assert len(group) < LMAX

            gins, gins_clear = [], []
            cin = fhedeck_net_source_name(group[0].get_fan_in_net("CI"), inputs, groups)
            if cin[0]:
                gins.append(cin[0])
                gins_clear.append(cin[1])

            for i, net in enumerate(group_get_nets_fa(group, 'A')):
                name = fhedeck_net_source_name(net, inputs, groups)
                gins.append(f"{1 << i} * {name[0]}")
                gins_clear.append(f"{1 << i} * {name[1]}")
            for i, net in enumerate(group_get_nets_fa(group, 'B')):
                name = fhedeck_net_source_name(net, inputs, groups)
                gins.append(f"{1 << i} * {name[0]}")
                gins_clear.append(f"{1 << i} * {name[1]}")

            print(f"{TAB}std::cerr << \"\\rFA{id}    \";");
            if ciphertext:
                print(f"{TAB}Ciphertext gin{id} = {' + '.join(gins)};")
                print(f"{TAB}std::vector<Ciphertext> gout{id} = ctx.eval_lut_amortized(&gin{id}, decomp);")
            if cleartext:
                print(f"{TAB}long gin{id}_clear = {' + '.join(gins_clear)};")
                print(f"{TAB}std::vector<long> gout{id}_clear = vdecomp(gin{id}_clear);")
            if ciphertext and cleartext:
                for i in range(len(group)):
                    print(f"{TAB}assert(ctx.decrypt(&gout{id}[{i}]) == gout{id}_clear[{i}]);")
            print("")

            bootstraps += 1
        elif "LUT" in types:
            fhedeck_print_luts(id, group)
            print("")

            gins, gins_clear = [], []
            for i, net in enumerate(group_get_nets_lut(group)):
                name = fhedeck_net_source_name(net, inputs, groups)
                gins.append(f"{1 << i} * {name[0]}")
                gins_clear.append(f"{1 << i} * {name[1]}")

            print(f"{TAB}std::cerr << \"\\rLUT{id}   \";");
            if ciphertext:
                print(f"{TAB}Ciphertext gin{id} = {' + '.join(gins)};")
                print(f"{TAB}std::vector<Ciphertext> gout{id} = ctx.eval_lut_amortized(&gin{id}, lut{id});")
            if cleartext:
                print(f"{TAB}long gin{id}_clear = {' + '.join(gins_clear)};")
                print(f"{TAB}std::vector<long> gout{id}_clear = fvec{id}(gin{id}_clear);")
            if ciphertext and cleartext:
                for i in range(len(group)):
                    print(f"{TAB}assert(ctx.decrypt(&gout{id}[{i}]) == gout{id}_clear[{i}]);")
            print("")

            bootstraps += 1
        else:
            raise TypeError

    return bootstraps


def fhedeck_print_lut(idx, gate, id, nets):
    perm = []
    for i in range(len(gate.fan_in_nets)):
        perm.append(nets.index(gate.get_fan_in_net(f"I{i}")))
    newperm = perm[:]
    for i in range(len(nets)):
        if i not in perm:
            newperm.append(i)

    init = lut_get_init(gate)
    newinit = init * (1 << (len(newperm) - len(perm)))
    newinit = lut_permute_init(newperm, newinit)
    newinit = newinit * (1 << (LMAX - len(newperm)))

    cases = "\n"
    for i, val in enumerate(reversed(newinit)):
        cases += f"{TAB}{TAB}{TAB}case {i:2d}: return {val};\n"
    cases += f"{TAB}{TAB}{TAB}default: assert(0);\n"

    print((
        f"{TAB}auto lut{id}idx{idx} = [](long I) -> long {{\n"
        f"{TAB}{TAB}/* GATE {gate.id} ({gate.type} {gate.name} INIT 0x{int(init, 2):x} PERM {''.join(map(str, perm))}) */\n"
        f"{TAB}{TAB}switch (I) {{{cases}{TAB}{TAB}}};\n"
        f"{TAB}}};\n"
        f"{TAB}lut{id}.push_back(ctx.genrate_lut(lut{id}idx{idx}));\n"
        f"{TAB}flut{id}.push_back(lut{id}idx{idx});"))


def fhedeck_print_luts(id, group):
    print(f"{TAB}std::vector<RotationPoly> lut{id};")
    print(f"{TAB}std::vector<long (*)(long)> flut{id};")
    nets = group_get_nets_lut(group)
    assert len(nets) <= LMAX

    for idx, gate in enumerate(group):
        fhedeck_print_lut(idx, gate, id, nets)

    print((
        f"{TAB}auto fvec{id} = [flut{id}](long I) -> std::vector<long> {{\n"
        f"{TAB}{TAB}std::vector<long> ret;\n"
        f"{TAB}{TAB}for (size_t i = 0; i < {len(group)}; ++i)\n"
        f"{TAB}{TAB}{TAB}ret.push_back(flut{id}[i](I));\n"
        f"{TAB}{TAB}return ret;\n"
        f"{TAB}}};"))


def gate_get_idx(gate, groups):
    for id, group in enumerate(groups):
        for idx, g in enumerate(group):
            if gate == g:
                return id, idx


def gate_is_half_adder(gate):
    return str(gate.type) == "FA" and net_is_global_input(gate.get_fan_in_net("CI"))


def gates_group_adders(gates):
    adders = []
    for gate in filter(gate_is_half_adder, gates):
        for i, add in enumerate(adder_follow_chain(gate)):
            if i % (LMAX - 1) == 0:
                adders.append([])
            adders[-1].append(add)

    minidx, maxidx = [], []
    for adder in adders:
        minidx.append(min(map(gates.index, adder)))
        maxidx.append(max(map(gates.index, adder)))

    gadders = []
    for i, gate in enumerate(gates):
        for imin, imax, adder in zip(minidx, maxidx, adders):
            if gate in adder:
                if i == imin:
                    gadders.append(adder)
                break
        else:
            gadders.append(gate)

    return gadders


def gates_group_luts(gates):
    groups = []
    invidx = 0

    for gate in gates:
        if isinstance(gate, list):
            groups.append(gate)
            continue

        if str(gate.type) == "LUT1":
            assert lut_get_init(gate) == "01"

        if str(gate.type) in ["INV", "LUT1"]:
            I = "I0" if str(gate.type) == "LUT1" else "I"
            i = gate.get_fan_in_net(I)

            if net_is_global_input(i):
                groups.insert(invidx, [gate])
                invidx += 1
            else:
                id, _ = gate_get_idx(i.sources[0].gate, groups)
                groups.insert(id + 1, [gate])
            continue

        if not str(gate.type).startswith("LUT"):
            raise TypeError

        for i, group in enumerate(groups):
            if lut_is_fan_in_subset(gate, group):
                groups[i].append(gate)
                break
        else:
            groups.append([gate])

    return groups


def group_get_nets_fa(group, net):
    nets = []
    for gate in group:
        if str(gate.type) == "FA":
            nets.append(gate.get_fan_in_net(net))

    return nets


def group_get_nets_lut(group):
    nets = set()
    for gate in group:
        if str(gate.type).startswith("LUT"):
            for net in gate.fan_in_nets:
                nets.add(net)

    return sorted(nets, key=lambda n: n.id)


def groups_print(groups, file=sys.stdout):
    for i, group in enumerate(groups):
        print(f"group {i:03d}:", file=file)
        for gate in sorted(group, key=id):
            print(f"  {gate.id:4d}, {gate.type}", file=file)


def lut_get_init(gate):
    return bin(int(gate.get_init_data()[0], 16))[2:].zfill(1 << len(gate.fan_in_nets))


def lut_permute_init(perm, init):
    newinit = ""
    for i in range(len(init)):
        idx = 0
        for j, p in enumerate(perm):
            idx |= ((i >> p) & 1) << j
        newinit += init[idx]
    return newinit


def lut_is_fan_in_subset(gate, group):
    if not group:
        return False

    for g in group:
        if not str(g.type).startswith("LUT"):
            return False
        if not set(gate.fan_in_nets).issubset(set(g.fan_in_nets)):
            return False

    return True


def net_is_global_input(net):
    if net.is_global_input_net():
        return True

    assert len(net.sources) == 1
    return str(net.sources[0].gate.type) in ["HAL_GND", "HAL_VDD"]


hal_py.plugin_manager.load_all_plugins()
netlist = hal_py.NetlistFactory.load_netlist(sys.argv[0], HGL)
sum = builtins.sum
set = builtins.set
bench_print_header()

inputs = globals_get_names(netlist.top_module.input_pins)
fhedeck_print_inputs(NAME, inputs)

gates = netlist_sort_topo(netlist)
groups = gates_group_adders(gates)
groups = gates_group_luts(groups)
groups = groups_sort_topo(groups)
bootstraps = fhedeck_print_groups(inputs, groups)

outputs = globals_get_names(netlist.top_module.output_pins)
fhedeck_print_outputs(inputs, groups, outputs, source=fhedeck_net_source_name)

bench_print_footer(NAME, PARAMS, 1 << LMAX)
print(f"gates:      {len(gates):4d}", file=sys.stderr)
print(f"bootstraps: {bootstraps:4d}", file=sys.stderr)

# sanity checks
assert len(gates) == sum(map(len, groups))
