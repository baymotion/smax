# This file is part of the smax project (http://github.com/baymotion/smax)
# and is copyrighted under GPL v3 or later.

import argparse
import smax
import smax.log
import yaml


def generate_yaml(spec):
    # When dumping to yaml, hide the fields
    # beginning with underscore.
    def hide_underscores(dumper, o):
        r = {}
        for k, v in o.__dict__.items():
            if k.startswith("_"):
                continue
            r[k] = v
        return dumper.represent_mapping(
            "tag:yaml.org,2002:python/object:%s" % (o.__class__.__name__), r
        )

    yaml.add_multi_representer(object, hide_underscores)
    y = yaml.dump(spec, default_flow_style=False)
    return y


def generate_plantuml(spec):
    r = [
        "@startuml",
    ]
    states = {}

    def state(s):
        assert s.array_name not in states
        if True:
            states[s.array_name] = True
            if s.start:
                r.append("[*] --> %s" % s.full_name)
            r.append('state "%s" as %s {' % (s.name_list[-1], s.full_name))
            for n, or_states in enumerate(s.inner_states):
                if n:
                    r.append("--")
                for and_state in or_states:
                    state(and_state)
            for t in s.transitions:
                x = [t.state.full_name]
                if t.target:
                    x.extend(["-->", t.target_state.full_name])
                if t.event or t.condition:
                    x.append(":")
                if t.condition:
                    x.append("[%s]" % t.condition)
                if t.event:
                    x.append(t.event.name)
                r.append(" ".join(x))
            for t in s.timeouts:
                x = [t.state.full_name]
                if t.target:
                    x.extend(["-->", t.target_state.full_name])
                x.append(": %s(%s)" % (t.time_spec.scale, t.time_spec.timeout))
                r.append(" ".join(x))
            r.append("}")

    for s in spec["spec"]:
        machine = s.get("machine")
        if machine is None:
            continue
        state(machine)
    r.append("@enduml")
    return "\n".join(r)


def main():
    parser = argparse.ArgumentParser(
        description="Translate a smax script to python.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable trace-level messages",
    )
    parser.add_argument(
        "--python",
        help="Write generated python code to the given filename",
    )
    parser.add_argument(
        "--yaml",
        help="Yaml filename to write",
    )
    parser.add_argument(
        "--plantuml",
        help="Plantuml state machine filename to write",
    )
    parser.add_argument(
        "input",
        help="input script; use '-' for standard input.",
    )
    args = parser.parse_args()

    smax.log.enable_trace = args.verbose

    filename = "/dev/stdin" if args.input == "-" else args.input
    source = smax.load_source(filename)
    spec, code = smax.translate(source, filename)

    if args.python:
        python_filename = "/dev/stdout" if args.python == "-" else args.python
        with open(python_filename, "wt") as f:
            f.write(code)

    if args.yaml:
        y = generate_yaml(spec)
        with open(args.yaml, "wt") as f:
            f.write(y)

    if args.plantuml:
        y = generate_plantuml(spec)
        with open(args.plantuml, "wt") as f:
            f.write(y)


main()
