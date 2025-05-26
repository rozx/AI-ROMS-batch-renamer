poetry run nuitka \
    --onefile \
    --onefile-tempdir-spec="~/Library/Caches/ai-rom-batch-renamer" \
    --output-dir=./dist/mac \
    --output-filename="ai-rom-batch-renamer" \
    --macos-app-icon=./icon.png \
    --windows-icon-from-ico=./icon.png \
    --assume-yes-for-downloads \
    --show-progress \
    --include-package-data=pinyin \
    ai_rom_batch_renamer/main.py