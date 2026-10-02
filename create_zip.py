import os
import zipfile
import pathlib

root = pathlib.Path(__file__).resolve().parent
out_zip = root / 'smart_seedling_deploy.zip'
ignore_dirs = {'.venv', 'venv', '__pycache__', '.git', '.gemini', 'scratch', '.pytest_cache'}

print(f"Packaging project from: {root}")
count = 0
with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in root.rglob('*'):
        if any(part in ignore_dirs for part in p.parts):
            continue
        if p.name in ('smart_seedling_deploy.zip', 'create_zip.py', '.DS_Store'):
            continue
        if p.is_file():
            rel_path = p.relative_to(root)
            z.write(p, rel_path)
            count += 1

size_mb = round(os.path.getsize(out_zip) / (1024 * 1024), 2)
print(f"SUCCESS: ZIP Created: smart_seedling_deploy.zip ({size_mb} MB, {count} files)")
