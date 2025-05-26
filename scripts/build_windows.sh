poetry run nuitka \
    --onefile \
    --onefile-tempdir-spec="{TEMP}/ai-rom-batch-renamer" \
    --output-dir=./dist/windows \
    --output-filename="ai-rom-batch-renamer-Windows-X64.exe" \
    --windows-icon-from-ico=./icon.png \
    --assume-yes-for-downloads \
    --show-progress \
    --include-package-data=pinyin \
    ai_rom_batch_renamer/main.py