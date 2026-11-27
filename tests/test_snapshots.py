"""T-0072: each sample host's links, against the snapshot committed beside it.

A change that alters a link fails here; `python tests/snapshots.py` rewrites the snapshots, and the commit gives
the reason of their diff (docs/contribution.md).
"""

from __future__ import annotations

from pathlib import Path

import pytest

import snapshots


@pytest.mark.parametrize("host", snapshots.hosts(), ids=lambda p: p.name)
def test_a_sample_host_s_links_are_its_snapshot(host: Path, tmp_path: Path):
    message = snapshots.difference(host.name, snapshots.links(host, tmp_path), snapshots.committed(host))
    assert message is None, message


def test_every_snapshot_has_its_sample_host():
    assert snapshots.orphans() == []


def test_a_link_lost_or_turned_by_name_names_its_host_and_its_line():
    committed = "a calls b sure\nb reads c sure\n"
    assert snapshots.difference("python", committed, committed) is None
    message = snapshots.difference("python", "a calls b by name\n", committed)
    assert "python" in message
    assert "- a calls b sure" in message and "+ a calls b by name" in message and "- b reads c sure" in message
