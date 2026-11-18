# One tool installed once, local extensions in each host

The graph was born in `grid_zero/tools/` with paths and notions of Grid Zero hard-coded (scenarios, the `EtatDeJeu` protocol, the `simulation_server_cmd_` commands). It becomes a separate repository, installed as a global command in editable mode (`uv tool install -e`), and everything that holds for one host only leaves the core: it is a local extension, stored in the host's repository and declared in its `graphe.toml`.

## Options set aside

- A copy of the folder in each project: each fix would have to be carried over by hand, and the copies would diverge.
- A git submodule: the same source, but an update to pull in each host, for a single user.
- Keeping Grid Zero's notions in the core behind options: the core would know things about one host, which a publication would make unreadable.
