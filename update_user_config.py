import os
import sys
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
import re
import subprocess
import ctypes

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
    """Clears the console screen across Windows and Linux/macOS systems."""
    command = 'cls' if os.name == 'nt' else 'clear'
    subprocess.run(command, shell=True, check=False)

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def find_external_settings_file(filename="mod_settings_config.txt"):
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        search_locations = [
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

def insert_custom_settings(config_folder, config_path, external_settings_file, target_header="mods_settings"):
    if not os.path.exists(external_settings_file):
        print(style_text(f"Error: Replacement text file not found at " + external_settings_file, "FAIL"))
        return
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"user_settings_{timestamp}.bak"
        backup_path = os.path.join(config_folder, backup_filename)
        shutil.copy2(config_path, backup_path)
        print(style_text(f"\n[+] Backup created safely as: " + backup_filename, "GREEN", "BOLD"))

        incoming_settings = {}
        with open(external_settings_file, 'r', encoding='utf-8', errors='ignore') as ext_file:
            for line in ext_file:
                match = re.search(r'^\s*([\w\-]+)\s*=\s*(.+?)\s*,?\s*$', line)
                if match:
                    key = match.group(1).strip()
                    val = match.group(2).strip().rstrip(',')
                    if key != target_header and val != "{":
                        incoming_settings[key] = val

        if not incoming_settings:
            print(style_text("[-] Error: No valid settings found inside your 'mod_settings' file.", "FAIL"))
            return
        
        print(style_text(f"[+] Detected incoming settings to update: " + str(list(incoming_settings.keys())), "CYAN"))

        with open(config_path, 'r', encoding='utf-8', errors='ignore') as config_file:
            full_text = config_file.read()
        
        block_pattern = rf'(^|\n)([ \t]*){target_header}\s*=\s*\{{(.*?)\n\2\}}'
        match_block = re.search(block_pattern, full_text, re.DOTALL)

        if not match_block:
            print(style_text(f"[-] Error: Could not locate the '" + target_header + "' block in your config file.", "FAIL"))
            return
        
        prefix, header_indent, block_contents = match_block.group(1), match_block.group(2), match_block.group(3)
        child_indent = header_indent + "    "

        existing_block_map = {}
        non_setting_lines = []

        for line in block_contents.splitlines():
            kv_match = re.search(r'^\s*([\w\-]+)\s*=\s*(.+?)\s*,?\s*$', line)
            if kv_match:
                k = kv_match.group(1).strip()
                v = kv_match.group(2).strip().rstrip(',')
                existing_block_map[k] = v
            elif line.strip():
                non_setting_lines.append(line)

        for key, val in incoming_settings.items():
            existing_block_map[key] = val

        rebuilt_inner_lines = []

        for comment_line in non_setting_lines:
            rebuilt_inner_lines.append(comment_line)

        for key in sorted(existing_block_map.keys()):
            rebuilt_inner_lines.append(f"{child_indent}{key} = {existing_block_map[key]},")

        new_block_string = f"{prefix}{header_indent}{target_header} = {{\n" + "\n".join(rebuilt_inner_lines) + f"\n{header_indent}}}"

        updated_full_text = full_text.replace(match_block.group(0), new_block_string)

        with open(config_path, "w", encoding="utf-8") as config_file:
            config_file.write(updated_full_text)

        print(style_text(f"[+] Successfully updated and cleaned your '" + target_header + "' block layout.", "GREEN"))
        
    except Exception as e:
        print(style_text(f"[-] An error occurred during the backup or subsequent patch: " + e, "FAIL"))

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
        print(style_text(f"[-] An error occurred during restoration: " + e, "FAIL"))

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

    #------------ TEMPORARY LOCAL TESTING CONFIG -------------
    #config_folder = os.getcwd()
    #config_path = os.path.join(config_folder, "user_settings.config")
    #external_settings_file = os.path.join(config_folder, "mod_settings_config.txt")
    #target_header = "mods_settings"
    #---------------------------------------------------------

    if not os.path.exists(config_path):
        print(style_text(f"Error: Game config file not found at " + config_path, "FAIL"))
        if "Sandbox_Test_Environment" not in config_path:
            input("\nPress Enter to exit...")
            print(style_text("\nGoodbye, varlet.", "FAIL"))
        return
    
    if not external_settings_file or not os.path.exists(external_settings_file):
        print(style_text(f"Error: Mod config text file not found anywhere.", "FAIL"))
        if "Sandbox_Test_Environment" not in config_path:
            input("\nPress Enter to exit...")
            print(style_text("\nGoodbye, varlet.", "FAIL"))
        return
    
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
            break
        else:
            print(style_text("[-] Invalid choice. Please enter 1, 2, or 3.", "FAIL"))
            input(style_text("\nPress Enter to try again...", "CYAN"))

if __name__ == "__main__":
    main()
