import os
import sys
import time

def prompt_for_path_terminal():
    """Fallback text prompt if GUI packages are missing or fail."""
    print("\n--- Manual Path Selection ---")
    print("Please paste the absolute path to your 'Warhammer 40,000 DARKTIDE' root folder.")
    print("Example (Linux): /home/deck/.local/share/Steam/steamapps/common/Warhammer 40,000 DARKTIDE")
    print("Example (Windows): C:\\Program Files (x86)\\Steam\\steamapps\\common\\Warhammer 40,000 DARKTIDE")

    user_input = input("\nPaste path here (or press Enter to cancel): ").strip()

    user_input = user_input.strip('"\'')

    return user_input if user_input else None

def prompt_for_path_gui():
    """Attempts to open a native OS folder picker dialog."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()

        if sys.platform.startswith("win"):
            root.attributes("-topmost", True)

        chosen_path = filedialog.askdirectory(
            title=("Select your 'Warhammer 40,000 DARKTIDE' folder:")
        )

        root.destroy()
        return chosen_path
    except (ImportError, Exception):
        print("\nGraphical window tookit not available or failed to load.")
        return prompt_for_path_terminal()
    
def load_mods(game_dir):
    mods_dir = os.path.join(game_dir, "mods")
    if not os.path.exists(mods_dir) and os.path.exists(os.path.join(game_dir, "Mods")):
        mods_dir = os.path.join(game_dir, "Mods")

    if not os.path.exists(mods_dir):
        print(f"\n'mods' folder not found in program's current directory: {game_dir}")

        chosen_path = prompt_for_path_gui()

        if chosen_path:
            game_dir = os.path.abspath(chosen_path)
            mods_dir = os.path.join(game_dir, "mods")
            if not os.path.exists(mods_dir) and os.path.exists(os.path.join(game_dir, "Mods")):
                mods_dir = os.path.join(game_dir, "Mods")
        else:
            print("No folder provided. Exiting...")
            time.sleep(1.5)
            return
        
    if not os.path.exists(mods_dir):
        print(f"\nCould not locate a valid 'mods' folder inside: {game_dir}")
        print("Exiting program...")
        time.sleep(1.5)
        return
    
            # print(f"Please select your game directory...")
            # root = tk.Tk()
            # root.withdraw()
            # if sys.platform.startswith("win"):
            #     root.attributes("-topmost", True)

            # chosen_path = filedialog.askdirectory(
            #     title="Select your 'Warhammer 40,000 DARKTIDE' folder:"
            # )
            
            # root.destroy()
            # return chosen_path
    
    load_order_file = os.path.join(mods_dir, "mod_load_order.txt")
    if not os.path.exists(load_order_file) and os.path.exists(os.path.join(mods_dir, "mod_load_order")):
        load_order_file = os.path.join(mods_dir, "mod_load_order")

    found_mods = []

    for mod_name in os.listdir(mods_dir):
        mod_path = os.path.join(mods_dir, mod_name)
        if mod_name.startswith(".") or mod_name.startswith("-"):
            print(f"Disabled mod skipped: {mod_name.lstrip('.-')}")
            continue
        if os.path.isdir(mod_path) and mod_name.lower() not in ["dmf", "base"]:
            found_mods.append(mod_name)

    print(f"Found {len(found_mods)} active mods.")
    found_mods.sort(key=str.lower)

    try:
        with open(load_order_file, "w", encoding="utf-8") as f:
            for mod in found_mods:
                f.write(f"{mod}\n")
        print(f"Successfully updated your 'mod_load_order' file.")
        time.sleep(2.0)
    except Exception as e:
        print(f"Failed to write load order file: {e}")

if __name__ == "__main__":
    current_dir = os.getcwd()
    print(f"Running from directory: {current_dir}")
    load_mods(current_dir)
