import importlib
import sys


def main() -> int:
    try:
        module = importlib.import_module("slop_check.slop_structure_lint")
    except ModuleNotFoundError as error:
        if error.name == "slop_check":
            print(
                "Package 'slop_check' is not installed. Run via `uv run --project skills/slop-check slop-structure-lint`.",
                file=sys.stderr,
            )
            return 1
        raise
    return module.main()


if __name__ == "__main__":
    sys.exit(main())
