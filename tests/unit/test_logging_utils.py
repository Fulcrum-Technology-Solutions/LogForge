from logforge.utils.logging import parse_size


def test_parse_size_handles_units():
    assert parse_size("1KB") == 1024
    assert parse_size("2MB") == 2 * 1024 * 1024
    assert parse_size("3GB") == 3 * 1024 * 1024 * 1024
    assert parse_size("512") == 512
