"""The `graphe` command's entry point (pyproject.toml): `graphe hook` runs before every Bash call of the agent, so it
loads neither networkx nor the readers that every other command imports (T-0084)."""


def main(arguments: list[str] | None = None) -> int:
    import sys  # noqa: PLC0415 - this package's import stays empty: `import graphe.x` loads nothing more

    arguments = sys.argv[1:] if arguments is None else arguments
    if arguments == ["hook"]:
        from graphe.hook import hook  # noqa: PLC0415

        return hook()
    from graphe.cli import main as command  # noqa: PLC0415

    return command(arguments)
