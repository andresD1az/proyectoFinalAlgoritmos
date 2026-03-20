"""Remove garbled emoji bytes and replace with clean ASCII alternatives"""
import re

p = 'c:/Users/eyner/OneDrive/Documentos/ingenieria/semestre 9/algoritmos/proyect Final/frontend/index.html'
text = open(p, 'r', encoding='utf-8', errors='replace').read()

# Remove all garbled emoji sequences (they show as ðŸ... patterns)
# Pattern: multi-byte sequences that produce mojibake
import re

# Remove common garbled emoji patterns
text = re.sub(r'[ðŸ][^\s<"\']{0,6}', '', text)
text = re.sub(r'â[^\s<"\']{0,4}', '', text)

# Fix double \r\r\n -> \r\n
text = text.replace('\r\r\n', '\r\n')
text = text.replace('\r\r', '\r')

# Clean up extra spaces from emoji removal
text = re.sub(r'  +', ' ', text)

open(p, 'w', encoding='utf-8').write(text)
print(f"[OK] Cleaned {p}")
print(f"     Size: {len(text)} chars")
