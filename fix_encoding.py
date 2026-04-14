import re

with open('.agents/ralph/loop.sh', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace read_text() with read_text(encoding='utf-8')
content = re.sub(r'\.read_text\(\)', ".read_text(encoding='utf-8')", content)

# Replace write_text(...) with write_text(..., encoding='utf-8')
content = re.sub(r'\.write_text\(([^)]+)\)', r'.write_text(\1, encoding="utf-8")', content)

with open('.agents/ralph/loop.sh', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
