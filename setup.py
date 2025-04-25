import os
from pathlib import Path
parent = Path(__file__).parent
filename = parent / 'frame.py'

with_console = ''  # '--noconsole'

command = f"pyinstaller \
            --onedir \
            --noconfirm {with_console} \
            --workpath ./user/build \
            --distpath ./user/dist \
            -F {filename}"
print(command)
os.system(command)
