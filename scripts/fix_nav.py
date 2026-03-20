"""Add info section to sidebar and nav, fix placeholder encoding"""
import re

p = 'c:/Users/eyner/OneDrive/Documentos/ingenieria/semestre 9/algoritmos/proyect Final/frontend/index.html'
text = open(p, 'r', encoding='utf-8').read()

# Add info nav item before Cuenta section
old_cuenta = '<div class="nav-lbl">Cuenta</div>'
new_cuenta = '''<div class="nav-lbl">Info</div>
 <div class="nav-item" onclick="nav(this,'info')">Informacion Legal</div>
 </div>
 <div class="nav-group">
 <div class="nav-lbl">Cuenta</div>'''
text = text.replace(old_cuenta, new_cuenta)

# Add info to nav titles
old_titles = "admin:'Panel de Admin'};"
new_titles = "admin:'Panel de Admin',info:'Informacion Legal'};"
text = text.replace(old_titles, new_titles)

# Fix placeholder encoding issue
text = text.replace('placeholder="¢¢¢¢"', 'placeholder="********"')

# Fix the password placeholder bullet encoding
text = text.replace('Â·', '-')

open(p, 'w', encoding='utf-8').write(text)
print("[OK] Added info section and fixed placeholders")
