#

import argparse
import smax
import sys

def main():
    parser = argparser.ArgumentParser(description="Translate a smax script to python.")
    parser.add_argument("--output", help="Write the output to the given filename")
    parser.add_argument("inputs", nargs="+", help="List of input scripts; use '-' for standard input.")
    args = parser.parse_args()

    output = sys.stdout
    if args.output:
        output = open(args.output)
    try:
        for input in inputs:
            with open("/dev/stdin" if input=="-" else input, "rt") as input_file:
                s = input_file.read()
            machine_source = smax.load_source(filename)
            python_code = smax.translate(machine_source, filename)
            with open(output, "wt") as f:
                f.write(python_code)
    finally:
        output.close()

main()

