import os, pathlib
p = pathlib.Path(__file__).parent.parent / "frontend" / "index.html"
p.parent.mkdir(exist_ok=True)
print(f"Escribiendo en: {p}")
