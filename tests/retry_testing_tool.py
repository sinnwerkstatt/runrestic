import os
import sys
from datetime import date


# python retry_testing_tool tries sleep infix directory


def main():
    max_retry = int(sys.argv[1])
    infix = sys.argv[2]
    base_dir = sys.argv[3] or "."

    filename = (
        f"{base_dir}/retry_testing_tool_{infix}-{date.today()}-retries-{max_retry}"
    )

    try:
        last_try = int(open(filename, "r").read())
    except FileNotFoundError:
        last_try = 1

    if last_try >= max_retry:
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass
        sys.exit(0)

    print(f"{filename}: {last_try}/{max_retry}")
    open(filename, "w").write(str(last_try + 1))

    sys.exit(1)


if __name__ == "__main__":
    main()
