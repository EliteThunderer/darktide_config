import os
import sys
import sjson
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
import re
import subprocess
import ctypes
import time

COLORS = {
    "HEADER": "\033[95m",
    "BLUE": "\033[94m",
    "CYAN": "\033[96m",
    "GREEN": "\033[92m",
    "WARNING": "\033[93m",
    "FAIL": "\033[91m",
    "END": "\033[0m",
    "BOLD": "\033[1m"
}

def init_terminal_colors():
    """Forces Windows Command Prompt to natively support ANSI color codes."""
    if os.name == 'nt':  # Check if running on Windows
        kernel32 = ctypes.windll.kernel32
        # 7 is the standard mode flag; 4 enables Virtual Terminal Processing (ANSI colors)
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

def style_text(text, *styles):
    """Wraps text in terminal styles and safely resets color codes at the end."""
    joined_styles = "".join(COLORS.get(s, "") for s in styles)
    return f"{joined_styles}{text}{COLORS['END']}"

def clear_screen():
    """Repositions the terminal cursor to the top-left to prevent screen flashing."""
    sys.stdout.write("\033[H\033[2J")
    sys.stdout.flush()

#def get_resource_path(relative_path):
    #try:
        #base_path = sys._MEIPASS
    #except AttributeError:
        #base_path = os.path.abspath(".")
    #return os.path.join(base_path, relative_path)

def find_external_settings_file(filename="mod_settings_config.txt"):
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        search_locations = [
            ".",
            os.path.join(user_profile, "Downloads"),
            os.path.join(user_profile, "Desktop"),
            os.getcwd()
        ]
        for location in search_locations:
            potential_path = os.path.join(location, filename)
            if os.path.exists(potential_path):
                print(style_text(f"[+] Automatically located settings file at: " + potential_path, "CYAN"))
                return potential_path
            
    print(style_text("[-] Could not find the settings file automatically. Please select it manually...", "FAIL"))
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    chosen_path = filedialog.askopenfilename(
        title="Select the shared mod settings text file",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    return os.path.abspath(chosen_path) if chosen_path else None

def parse_mods_from_comments(external_settings_file):
    """Reads the generated comments block to find all available mods."""
    mods = []
    if not os.path.exists(external_settings_file):
        return mods
    
    with open(external_settings_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("-- MOD:"):
                mod_name = line.replace("-- MOD:", "").strip()
                if mod_name:
                    mods.append(mod_name)
            elif line.startswith("-- EXPORTED_MOD_LIST_END"):
                break
    return mods

def interactive_mod_selector(mod_list):
    """Displays an interactive console menu with checkboxes to toggle mods."""
    selected_indices = set(range(len(mod_list)))
    current_idx = 0

    MAX_VISIBLE = 15
    start_win = 0

    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

    try:
        import msvcrt
        def get_key():
            ch = msvcrt.getch()
            if ch in (b'\x00', b'\xe0'):
                ch2 = msvcrt.getch()
                if ch2 == b'H': return 'up'
                if ch2 == b'P': return 'down'
            if ch == b'\r': return 'enter'
            if ch == b' ': return 'space'
            return None
    except ImportError:
        import tty
        import termios
        def get_key():
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
                if ch == '\x1b':
                    ch2 = sys.stdin.read(2)
                    if ch2 == '[A': return 'up'
                    if ch2 == '[B': return 'down'
                if ch == '\r' or ch == '\n': return 'enter'
                if ch == ' ': return 'space'
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return None
    subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True, check=False)

    while True:
        clear_screen()
        print(style_text("=== MOD IMPORT SELECTOR ===", "HEADER", "BOLD"))
        print(style_text("Use [Up/Down] arrows to navigate, [Space] to toggle, [Enter] to confirm selections.\n", "CYAN"))

        if current_idx < start_win:
            start_win = current_idx
        elif current_idx >= start_win + MAX_VISIBLE:
            start_win = current_idx - MAX_VISIBLE + 1

        end_win = start_win + MAX_VISIBLE

        if start_win > 0:
            print(style_text("   ▲ ... more mods above ... ▲", "WARNING"))
        else:
            print("")

        for idx in range(start_win, min(end_win, len(mod_list))):
            mod = mod_list[idx]
            is_selected = idx in selected_indices
            checkbox = "[X]" if is_selected else "[ ]"
            box_style = "GREEN" if is_selected else "WARNING"

            if idx == current_idx:
                print(style_text(f" > {checkbox} {mod}", box_style, "BOLD", "BLUE"))
            else:
                print(f"   {style_text(checkbox, box_style)} {mod}")

        if end_win < len(mod_list):
            print(style_text("   ▼ ... more mods below ... ▼", "WARNING"))
        else:
            print("")

        key = get_key()
        if key == 'up':
            current_idx = max(0, current_idx - 1)
        elif key == 'down':
            current_idx = min(len(mod_list) - 1, current_idx + 1)
        elif key == 'space':
            if current_idx in selected_indices:
                selected_indices.remove(current_idx)
            else:
                selected_indices.add(current_idx)
        elif key == 'enter':
            break

    sys.stdout.write("\033[?25h")
    sys.stdout.flush()
    return [mod_list[i] for i in selected_indices]

def read_external_settings_file(external_settings_file, selected_mods):
    """Loads an SJSON file for merging with current user settings."""
    incoming_settings = {}
    if not os.path.exists(external_settings_file):
        return incoming_settings
    
    # print(external_settings_file)
    with open(external_settings_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        cleaned = "".join(line for line in lines if not line.lstrip().startswith("--"))
        incoming_settings = sjson.loads(cleaned)

    return incoming_settings

def insert_custom_settings(config_folder, config_path, external_settings_file, target_header="mods_settings"):
    if not os.path.exists(external_settings_file):
        print(style_text(f"Error: Replacement text file not found at " + external_settings_file, "FAIL"))
        return
    
    available_mods = parse_mods_from_comments(external_settings_file)
    if not available_mods:
        print(style_text("[-] Error: No structured mod comment indexes found in external file.", "FAIL"))
        return
    
    chosen_mods = interactive_mod_selector(available_mods)
    if not chosen_mods:
        print(style_text("\n[-]Configuration Update Aborted: No items checked for import.", "WARNING"))
        return
    
    print(style_text(f"\n[+] Extracting config data blocks for {len(chosen_mods)} chosen mod entries...", "CYAN"))
    incoming_settings = read_external_settings_file(external_settings_file, chosen_mods)


    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"user_settings_{timestamp}.bak"
    backup_path = os.path.join(config_folder, backup_filename)
    shutil.copy2(config_path, backup_path)
    print(style_text(f"\n[+] Backup created safely as: " + backup_filename, "GREEN", "BOLD"))
    
    with open(config_path, "r", encoding="utf-8") as f:
        original_settings = sjson.loads(f.read())
        updated_settings = original_settings
        updated_settings["mods_settings"] = incoming_settings
    

    with open(config_path, "w", encoding="utf-8") as config_file:
        config_file.write(sjson.dumps(updated_settings, indent="\t"))

    print(style_text(f"[+] Successfully merged your selected mods cleanly into '{target_header}' block layout.", "GREEN"))

def restore_from_backup(config_folder, config_path):
    try:
        files = os.listdir(config_folder)
        backups = [f for f in files if f.endswith('.bak')]

        if not backups:
            print(style_text("\n[-] No backup files found in this directory.", "FAIL"))
            return
        
        backups.sort(reverse=True)
        selected_backup = backups[0]
        selected_backup_path = os.path.join(config_folder, selected_backup)

        print(style_text(f"\n[+] Most recent backup found: " + selected_backup, "CYAN"))
        print(style_text("Restoring previous config file...", "CYAN"))

        shutil.copy2(selected_backup_path, config_path)
        print(style_text(f"[+] Successfully restored your config to: " + selected_backup, "GREEN"))

        print(style_text(f"Cleaning up: Removing used backup file...", "CYAN"))
        os.remove(selected_backup_path)
        print(style_text(f"[+] Successfully deleted " + selected_backup + " from directory.", "GREEN"))

    except Exception as e:
        print(style_text(f"[-] An error occurred during restoration: {e}", "FAIL"))

def main():
    init_terminal_colors()

    appdata_path = os.environ.get('APPDATA')
    if not appdata_path:
        print(style_text("Error: Could not locate the AppData directory.", "FAIL"))
        return

    config_folder = os.path.join(appdata_path, "Fatshark", "Darktide")
    config_path = os.path.join(config_folder, "user_settings.config")
    external_settings_file = find_external_settings_file("mod_settings_config.txt")
    target_header = "mods_settings"

    if not os.path.exists(config_path):
        print(style_text(f"Error: Game config file not found at " + config_path, "FAIL"))
        input("\nPress Enter to exit...")
        print(style_text("\nGoodbye, varlet.", "FAIL"))
        time.sleep(1.0)
        return
    
    if not external_settings_file or not os.path.exists(external_settings_file):
        print(style_text(f"Error: Mod config text file not found anywhere.", "FAIL"))
        input("\nPress Enter to exit...")
        print(style_text("\nGoodbye, varlet.", "FAIL"))
        time.sleep(1.0)
        return
    
    subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True, check=False)

    while True:
        clear_screen()
        # Custom stylized ASCII title banner
        print(style_text("================================================================", "GREEN"))
        print(style_text("  ██████╗  █████╗ ██████╗ ██╗  ██╗████████╗██╗██████╗ ███████╗", "GREEN", "BOLD"))
        print(style_text("  ██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝╚══██╔══╝██║██╔══██╗██╔════╝", "GREEN", "BOLD"))
        print(style_text("  ██║  ██║███████║██████╔╝█████╔╝    ██║   ██║██║  ██║█████╗  ", "GREEN", "BOLD"))
        print(style_text("  ██║  ██║██╔══██║██╔══██╗██╔═██╗    ██║   ██║██║  ██║██╔══╝  ", "GREEN", "BOLD"))
        print(style_text("  ██████╔╝██║  ██║██║  ██║██║  ██╗   ██║   ██║██████╔╝███████╗", "GREEN", "BOLD"))
        print(style_text("  ╚══════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝╚═════╝ ╚══════╝", "GREEN", "BOLD"))
        print(style_text("               C O N F I G   U P D A T E R              ", "GREEN", "BOLD"))
        print(style_text("================================================================", "GREEN"))
        print(f" Target File: {style_text(os.path.basename(config_path), 'BOLD')}")
        print(style_text("----------------------------------------------------------------", "GREEN"))
        print(f" [{style_text('1', 'GREEN', 'BOLD')}] Apply Custom Settings (Creates Auto-Backup)")
        print(f" [{style_text('2', 'WARNING', 'BOLD')}] Restore Config From Existing Backup")
        print(f" [{style_text('3', 'FAIL', 'BOLD')}] Exit")
        print(style_text("================================================================", "GREEN"))

        user_choice = input(style_text("Enter your choice (1-3): ", "BOLD")).strip()

        if user_choice == "1":
            insert_custom_settings(config_folder, config_path, external_settings_file, target_header)
            input(style_text("\nPress Enter to return to menu...", "CYAN"))
        elif user_choice == "2":
            restore_from_backup(config_folder, config_path)
            input(style_text("\nPress Enter to return to menu...", "CYAN"))
        elif user_choice == "3":
            print(style_text("\nGoodbye, varlet.", "FAIL"))
            time.sleep(1.0)
            break
        else:
            print(style_text("[-] Invalid choice. Please enter 1, 2, or 3.", "FAIL"))
            input(style_text("\nPress Enter to try again...", "CYAN"))

if __name__ == "__main__":
    main()
