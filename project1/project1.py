"""Project 1: Calling All Stations - Alert Propagation Simulation."""

from parsing import read_input_path, parse_file
from simulation import run


def main() -> None:
    path = read_input_path()

    if not path.exists():
        print('FILE NOT FOUND')
        return

    cfg = parse_file(path)
    for line in run(cfg):
        print(line)


if __name__ == '__main__':
    main()
