from bed2myra.main import iter_plate_groups


def test_even_split():
    groups = list(iter_plate_groups(["a", "b", "c", "d"], group_size=2))
    assert groups == [["a", "b"], ["c", "d"]]


def test_uneven_split_remainder_in_last_group():
    groups = list(iter_plate_groups(["a", "b", "c", "d", "e"], group_size=2))
    assert groups == [["a", "b"], ["c", "d"], ["e"]]


def test_group_size_one():
    groups = list(iter_plate_groups(["a", "b", "c"], group_size=1))
    assert groups == [["a"], ["b"], ["c"]]


def test_group_size_larger_than_list():
    groups = list(iter_plate_groups(["a", "b"], group_size=10))
    assert groups == [["a", "b"]]


def test_empty_list():
    groups = list(iter_plate_groups([], group_size=2))
    assert groups == []
