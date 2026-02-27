#!/usr/bin/env python3
"""
SportPlay Repo Updater
======================
Usage:
  python update.py <path_to_new_zip>
  python update.py                     (regenerate addons.xml only)

Example:
  python update.py ~/Downloads/plugin.video.sportplay-2.3.0.zip
"""
import os, sys, shutil, hashlib, zipfile, re

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
ZIPS_DIR = os.path.join(REPO_DIR, 'zips')

def get_addon_xml_from_zip(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as z:
        for name in z.namelist():
            if name.endswith('addon.xml') and name.count('/') == 1:
                return z.read(name).decode('utf-8')
    return None

def generate_addons_xml():
    addons = []
    for folder in sorted(os.listdir(ZIPS_DIR)):
        folder_path = os.path.join(ZIPS_DIR, folder)
        if not os.path.isdir(folder_path) or folder.startswith(('.', '_')):
            continue
        zips = [f for f in os.listdir(folder_path) if f.endswith('.zip')]
        if not zips:
            continue
        zips.sort()
        latest_zip = zips[-1]
        xml_content = get_addon_xml_from_zip(os.path.join(folder_path, latest_zip))
        if xml_content:
            xml_content = re.sub(r'<\?xml[^?]*\?>\s*', '', xml_content).strip()
            addons.append(xml_content)
            print(f"  + {folder}/{latest_zip}")

    content = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'
    for addon in addons:
        content += addon + '\n'
    content += '</addons>\n'

    with open(os.path.join(REPO_DIR, 'addons.xml'), 'w', encoding='utf-8') as f:
        f.write(content)
    md5 = hashlib.md5(content.encode('utf-8')).hexdigest()
    with open(os.path.join(REPO_DIR, 'addons.xml.md5'), 'w') as f:
        f.write(md5)
    print(f"\n  addons.xml OK ({len(addons)} addons)")
    print(f"  MD5: {md5}")

def add_zip(zip_path):
    basename = os.path.basename(zip_path)
    m = re.match(r'(.+?)-\d+', basename)
    if not m:
        print(f"Cannot parse addon id from: {basename}")
        return False
    addon_id = m.group(1)
    addon_dir = os.path.join(ZIPS_DIR, addon_id)
    os.makedirs(addon_dir, exist_ok=True)
    for old in [f for f in os.listdir(addon_dir) if f.endswith('.zip')]:
        os.remove(os.path.join(addon_dir, old))
        print(f"  - Supprime {old}")
    shutil.copy2(zip_path, os.path.join(addon_dir, basename))
    print(f"  + Ajoute {basename}")
    return True

if __name__ == '__main__':
    print("=" * 45)
    print("  SportPlay Repo Updater")
    print("=" * 45)
    if len(sys.argv) > 1:
        print(f"\nAjout: {sys.argv[1]}")
        if not add_zip(sys.argv[1]):
            sys.exit(1)
    print("\nGeneration addons.xml...")
    generate_addons_xml()
    generate_indexes()
    print(f"""
{'=' * 45}
  git add -A
  git commit -m "Update"
  git push
{'=' * 45}""")

def generate_indexes():
    """Generate index.html for each directory so Kodi can browse"""
    for root, dirs, files in os.walk(ZIPS_DIR):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        links = []
        for d in sorted(dirs):
            links.append(f'<a href="{d}/">{d}/</a>')
        for f in sorted(files):
            if f == 'index.html':
                continue
            links.append(f'<a href="{f}">{f}</a>')
        html = '<html><body>\n' + '\n'.join(links) + '\n</body></html>\n'
        with open(os.path.join(root, 'index.html'), 'w') as fh:
            fh.write(html)
    
    # Root index
    links = ['<a href="zips/">zips/</a>',
             '<a href="addons.xml">addons.xml</a>',
             '<a href="addons.xml.md5">addons.xml.md5</a>']
    with open(os.path.join(REPO_DIR, 'index.html'), 'w') as fh:
        fh.write('<html><body>\n' + '\n'.join(links) + '\n</body></html>\n')
    print("  index.html OK")
