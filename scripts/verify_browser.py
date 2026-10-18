"""Retired live-mutating acceptance entry point; use an owned qualification runner."""


def main():
    raise SystemExit("Legacy acceptance is retired because it wrote fixtures into the live workspace. Use scripts/qualify_local_stack.py for isolated qualification; use scripts/verify_system.py --readiness-only for observational live checks.")


if __name__ == "__main__":
    main()
