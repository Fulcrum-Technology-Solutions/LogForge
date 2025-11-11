from logforge.cli.main import cli


def main() -> None:
    """Entry point for `python -m logforge`."""
    cli.main(prog_name="logforge")  # type: ignore[attr-defined]


if __name__ == "__main__":
    main()
