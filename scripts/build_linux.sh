poetry run nuitka \
    --onefile \
    --onefile-tempdir-spec="/tmp/ai-rom-batch-renamer" \
    --output-dir=./dist/linux \
    --output-filename="ai-rom-batch-renamer-Linux-X64" \
    --assume-yes-for-downloads \
    --show-progress \
    --include-package-data=pinyin \
    ai_rom_batch_renamer/main.py