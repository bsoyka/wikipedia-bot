from tasks._utils import create_edit_summary


def test_create_edit_summary():
    assert (
        create_edit_summary("Fixing links", 1, "0.3.0")
        == "Fixing links ([[User:BsoykaBot/Task 1|Task 1]] v0.3.0, [[User talk:BsoykaBot|report errors]])"
    )
