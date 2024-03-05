import functools
import natsort
import collections
import re
import sys

TAB = "    "


def bench_print_header():
    print((
        f"#include <benchmark/benchmark.h>\n"
        f"#include \"fhe_context.h\"\n"
        f"using namespace fhe_deck;\n\n"))


def bench_print_footer(name, params, plaintext=4):
    func = name.replace('-', '_').lower()

    print((
        f"\nstatic void\n"
        f"BM_{func}(benchmark::State& state)\n"
        f"{{\n"
        f"{TAB}FHEContext ctx;\n"
        f"{TAB}ctx.generate_context({params});\n"
        f"{TAB}ctx.set_default_message_encoding_type(partial_domain);\n"
        f"{TAB}ctx.set_default_plaintext_space({plaintext});\n\n"
        f"{TAB}for (auto _ : state) {{\n"
        f"{TAB}{TAB}test_{func}(ctx);\n"
        f"{TAB}}}\n"
        f"}}\n\n"
        f"BENCHMARK(BM_{func})->Unit(benchmark::kSecond);\n"
        f"BENCHMARK_MAIN();"))


def edge_is_global(edge):
    return gate_is_const(edge[0]) or edge[1].is_global_input_net()


def fhedeck_print_inputs(func, inputs, ciphertext=True, cleartext=False):
    names = natsort.natsorted(inputs.values())
    counter = collections.Counter([re.match(r"([a-zA-Z_]+)\d*", v)[1] for v in names])

    args = ""
    for name, count in counter.items():
        if count <= 8:
            args += f", uint8_t {name} = 0"
        elif count <= 16:
            args += f", uint16_t {name} = 0"
        elif count <= 32:
            args += f", uint32_t {name} = 0"
        elif count <= 64:
            args += f", uint64_t {name} = 0"
        else:
            args += f", std::vector<uint64_t> {name} = {{ 0 }}"

    print(f"std::vector<long>\ntest_{func.replace('-', '_').lower()}(FHEContext& ctx{args})\n{{")
    for name, count in counter.items():
        for i, n in enumerate(filter(lambda x: x.startswith(name), names)):
            if count <= 64:
                if ciphertext:
                    print(f"{TAB}Ciphertext ct_{n} = ctx.encrypt_public(({name} >> {i}) & 1);")
                if cleartext:
                    print(f"{TAB}long ct_{n}_clear = ({name} >> {i}) & 1;")
            else:
                if ciphertext:
                    print(f"{TAB}Ciphertext ct_{n} = ctx.encrypt_public(({name}[{i // 64}] >> {i % 64}) & 1);")
                if cleartext:
                    print(f"{TAB}long ct_{n}_clear = ({name}[{i // 64}] >> {i % 64}) & 1);")
    print("")


def fhedeck_print_outputs(inputs, groups, outputs, ciphertext=True, cleartext=False, source=None):
    print(f"{TAB}std::cerr << \"\\r          \\r\";")
    print(f"{TAB}std::vector<long> test_out;")
    for net, name in natsort.natsorted(outputs.items(), key=lambda x: x[1]):
        assert len(net.sources) == 1
        gate = net.sources[0].gate

        if str(gate.type) == "HAL_GND":
            print(f"{TAB}test_out.push_back(0); /* {name} */")
        elif str(gate.type) == "HAL_GND":
            print(f"{TAB}test_out.push_back(1); /* {name} */")
        else:
            n = source(net, inputs, groups)
            if ciphertext:
                print(f"{TAB}test_out.push_back(ctx.decrypt(&{n[0]})); /* {name} */")
            if ciphertext and cleartext:
                print(f"{TAB}assert(ctx.decrypt(&{n[0]}) == {n[1]});")
            elif cleartext:
                print(f"{TAB}test_out.push_back({n[1]}); /* {name} */")
    print(f"{TAB}return test_out;\n}}")


def gate_cmp_depth_type(a, b):
    if a[1] > b[1]:
        return 1
    elif a[1] < b[1]:
        return -1

    if str(a[0].type) == "INV":
        if str(b[0].type) == "INV":
            return 0
        else:
            return -1
    elif str(a[0].type).startswith("LUT"):
        if str(b[0].type) == "INV":
            return 1
        elif str(b[0].type).startswith("LUT"):
            w0 = int(str(a[0].type)[-1])
            w1 = int(str(b[0].type)[-1])
            if w0 > w1:
                return -1
            elif w0 == w1:
                return 0
            else:
                return 1
        else:
            return -1
    elif str(a[0].type) == "FA":
        if str(b[0].type) == "FA":
            return 0
        else:
            return -1
    else:
        return 0


def gate_get_edges_in(gate):
    edges = set()
    for net in gate.fan_in_nets:
        for source in net.sources:
            edges.add((source.gate, net, gate))

    return edges


def gate_get_edges_out(gate):
    edges = set()
    for net in gate.fan_out_nets:
        for destination in net.destinations:
            edges.add((gate, net, destination.gate))

    return edges


def gate_is_const(gate):
    return str(gate.type) in ["HAL_GND", "HAL_VDD"]


def gate_is_not_const(gate):
    return str(gate.type) not in ["HAL_GND", "HAL_VDD"]


def globals_get_names(pins):
    names = {}
    for pin in pins:
        names[pin.net] = pin.name.replace("(", "").replace(")", "")

    return names


def group_get_edges_in(group):
    edges = []
    for gate in group:
        edges += gate_get_edges_in(gate)

    filtered = []
    for s, n, d in edges:
        if s in group and d in group:
            continue
        filtered.append((s, n, d))

    return filtered


def group_get_edges_out(group):
    edges = []
    for gate in group:
        edges += gate_get_edges_out(gate)

    filtered = []
    for s, n, d in edges:
        if s in group and d in group:
            continue
        filtered.append((s, n, d))

    return filtered


def groups_get_index(gate, groups):
    for i, group in enumerate(groups):
        if gate in group:
            return i, group.index(gate)

    return None, None


def groups_sort_topo(groups):
    gwork = set()
    for group in groups:
        if all(map(edge_is_global, group_get_edges_in(group))):
            gwork.add(tuple(group))

    gsort = []
    used = set()
    while gwork:
        group = gwork.pop()
        gsort.append(group)

        for edge in group_get_edges_out(group):
            if edge in used:
                continue
            used.add(edge)

            add = True
            gid, _ = groups_get_index(edge[2], groups)
            for e in group_get_edges_in(groups[gid]):
                add = add and (edge_is_global(e) or e in used)
            if add:
                gwork.add(tuple(groups[gid]))
    assert len(gsort) == len(groups)

    return gsort


def netlist_sort_topo(netlist):
    const = list(filter(gate_is_const, netlist.gates))
    gates = list(filter(gate_is_not_const, netlist.gates))

    gwork = set()
    for gate in gates:
        if all(map(edge_is_global, gate_get_edges_in(gate))):
            gwork.add((gate, 0))

    used = set()
    gsort, gdepths = [], []
    while gwork:
        gate, depth = gwork.pop()
        gsort.append(gate)
        gdepths.append(depth)

        for edge in gate_get_edges_out(gate):
            if edge in used:
                continue
            used.add(edge)

            g, add = edge[2], True
            for e in gate_get_edges_in(g):
                add = add and (edge_is_global(e) or e in used)
            if not add:
                continue

            d = depth + 1
            for e in gate_get_edges_in(g):
                if edge_is_global(e):
                    continue
                d = max(d, gdepths[gsort.index(e[0])])
            gwork.add((g, d))
    assert len(gsort) == len(gates)

    combined = list(zip(gsort, gdepths))
    combined.sort(key=functools.cmp_to_key(gate_cmp_depth_type))

    gates = []
    for gate, depth in combined:
        gates.append(gate)

    return gates
