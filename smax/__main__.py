# This file is part of the smax project (http://github.com/pjogrady/smax)
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


def main():
    parser = argparse.ArgumentParser(
        description="Translate a smax script to python.",
    )
    parser.add_argument(
        "--output",
        help="Write the output to the given filename",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable trace-level messages",
    )
    parser.add_argument(
        "--yaml",
        help="Yaml filename to write",
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
    output_filename = "/dev/stdout" if args.output is None else args.output
    with open(output_filename, "wt") as f:
        f.write(code)
    if args.yaml:
        y = generate_yaml(spec)
        with open(args.yaml, "wt") as f:
            f.write(y)


main()
