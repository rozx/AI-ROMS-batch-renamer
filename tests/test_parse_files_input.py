from ai_rom_batch_renamer.modules import utils as utilsModule


def test_parse_files_input_supports_semicolon_and_newline_and_dedup():
    files = "C:/roms/a.zip; C:/roms/b.zip\n'C:/roms/a.zip'\n\"C:/roms/c.zip\""

    parsed = utilsModule.parseFilesInput(files)

    assert parsed == [
        "C:/roms/a.zip",
        "C:/roms/b.zip",
        "C:/roms/c.zip",
    ]


def test_parse_files_input_empty_string():
    assert utilsModule.parseFilesInput("") == []
