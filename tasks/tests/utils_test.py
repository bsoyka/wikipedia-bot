from tasks import __version__
from tasks._utils import create_edit_summary


def test_create_edit_summary() -> None:
    assert (
        create_edit_summary("Fixing links", task=1)
        == f"Fixing links ([[User:BsoykaBot/Task 1|Task 1]], v{__version__}, [[User talk:BsoykaBot|report errors]])"
    )
