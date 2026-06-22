from bed2myra.main import sanitize_filename


def test_passthrough_safe_characters():
    assert sanitize_filename("modjadji-tb_1.0") == "modjadji-tb_1.0"


def test_replaces_forward_slash():
    assert sanitize_filename("pool/1") == "pool_1"


def test_replaces_backslash():
    assert sanitize_filename("plate\\name") == "plate_name"


def test_replaces_multiple_unsafe_characters():
    assert sanitize_filename('a<b>c:d"e|f?g*h') == "a_b_c_d_e_f_g_h"


def test_preserves_spaces_and_hyphens():
    assert sanitize_filename("my plate - run 1") == "my plate - run 1"


def test_empty_string():
    assert sanitize_filename("") == ""
