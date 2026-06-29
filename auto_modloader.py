import os
import winreg
import re

DARKTIDE_APP_ID = "1361210"

def get_steam_install_path():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Valve\Steam")
        path, _ = winreg.QueryValueEx(key, "InstallPath")
        return path
    except FileNotFoundError:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam")
            path, _ = winreg.QueryValueEx(key, "InstallPath")
            return path
        except FileNotFoundError:
            return None

def find_darktide_path():
    steam_base = get_steam_install_path()
    if not steam_base:
        print("Error: Steam installation not found in Windows Registry.")
        return None
    
    library_folders = [os.path.join(steam_base, "steamapps")]

    vdf_path = os.path.join(steam_base, "steamapps", "libraryfolders.vdf")
    if os.path.exists(vdf_path):
        with open(vdf_path, "r", encoding="utf-8") as f:
            vdf_content = f.read()
            found_paths = re.findall(r'"path"\s+"([^"]+)"', vdf_content)
            for path in found_paths:
                clean_path = os.path.join(path.replace("\\\\", "\\"), "steamapps")
                if clean_path not in library_folders:
                    library_folders.append(clean_path)

    for library in library_folders:
        manifest_name = f"appmanifest_{DARKTIDE_APP_ID}.acf"
        if os.path.exists(os.path.join(library, manifest_name)):
            game_dir = os.path.join(library, "common", "Warhammer 40,000 DARKTIDE")
            if os.path.exists(game_dir):
                return game_dir
    return None

def auto_load_mods(GAME_DIR):

    if GAME_DIR is None:
        print("Error: Could not locate Darktide on C: or D: drives.")
        print("Please verify your Steam installation path.")
        return
    
    MODS_DIR = os.path.join(GAME_DIR, "mods")
    LOAD_ORDER_FILE = os.path.join(MODS_DIR, "mod_load_order.txt")

    if not os.path.exists(MODS_DIR):
        print(f"Error: 'mods' folder not found at {MODS_DIR}")
        return
    
    found_mods = []
    for item in os.listdir(MODS_DIR):
        item_path = os.path.join(MODS_DIR, item)
        if item.startswith(".") or item.startswith("-"):
            print(f"Disabled mod skipped: {item}")
            continue
        if os.path.isdir(item_path) and item != "dmf" and item != "base":
            found_mods.append(item)


    print(f"Found {len(found_mods)} active custom mods.")

    found_mods.sort(key=str.lower)

    try:
        with open(LOAD_ORDER_FILE, "w", encoding="utf-8") as f:
            for mod in found_mods:
                f.write(f"{mod}\n")
        print(f"Successfully updated: {LOAD_ORDER_FILE}")
    except Exception as e:
        print(f"Failed to write load order file: {e}")

if __name__ == "__main__":
    detected_path = find_darktide_path()
    if detected_path:
        print(f"Game detected automatically: {detected_path}")
        auto_load_mods(detected_path)
    else:
        print("Darktide could not be located on any registered Steam library drive.")