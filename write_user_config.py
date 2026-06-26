import os
import re
import tkinter as tk
from tkinter import filedialog

AUTOMATED_CACHE_DIR = os.path.join(os.environ.get("APPDATA", ""), "DarktideSettingsExporter")
CACHE_FILE_PATH = os.path.join(AUTOMATED_CACHE_DIR, "exporter_cache.cfg")

def get_game_directory_and_save_path():
    if os.path.exists(CACHE_FILE_PATH):
        with open(CACHE_FILE_PATH, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines()]
            if len(lines) >= 2:
                game_dir, save_destination_dir = lines[0], lines[1]
                if os.path.exists(game_dir) and os.path.exists(save_destination_dir):
                    return game_dir, save_destination_dir
            
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    print("First-time run: Please select your Darktide directory...")
    game_dir = filedialog.askdirectory(title="1/2: Select the Darktide folder containing your user_settings.config file")
    if not game_dir:
        print("Error: No game directory selected. Exiting.")
        return None, None
    game_dir = os.path.abspath(game_dir)

    print("Please select the folder where you want the mod settings exported to...")
    save_destination_dir = filedialog.askdirectory(title="2/2: Select the folder your future mod_settings files should be saved to")
    if not save_destination_dir:
        print("Error: No save destination selected. Exiting.")
        return None, None
    save_destination_dir = os.path.abspath(save_destination_dir)

    try:
        if not os.path.exists(AUTOMATED_CACHE_DIR):
            os.makedirs(AUTOMATED_CACHE_DIR)
        with open(CACHE_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(f"{game_dir}\n")
            f.write(f"{save_destination_dir}\n")
        print("Paths successfully saved for future uses.")
        return game_dir, save_destination_dir
    except Exception as e:
        print(f"Warning: Could not write cache or save path file: {e}")
        return game_dir, save_destination_dir

def extract_subheaders(extracted_lines):
    """Parses out the top-level keys inside the extracted block."""
    mod_names = []
    pattern = re.compile(r'^\s*([a-zA-Z0-9_\-]+)\s*=')

    bracket_count = 0
    for line in extracted_lines[1:]:
        bracket_count += line.count("{")
        if bracket_count == 1 and "{" in line:
            match = pattern.match(line)
            if match:
                mod_names.append(match.group(1))

        bracket_count -= line.count("}")

    return mod_names

def write_new_shareable_settings_file(external_settings_file, target_header):
    config_folder, export_destination_folder = get_game_directory_and_save_path()
    if not config_folder or not export_destination_folder:
        return False
    
    config_path = os.path.join(config_folder, "user_settings.config")

    if not os.path.exists(config_path):
        print(f"Error: 'user_settings.config' file not found inside selected folder: {config_folder}.")
        print(f"To fix this, delete the folder at: {AUTOMATED_CACHE_DIR} and run again.")
        return False

    #if not os.path.exists(config_path):
        #print(f"Error: Config file not found at: {config_path}")
        #return False
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        extracted_lines = []
        inside_target_section = False
        bracket_count = 0
        
        for line in lines:
            if f"{target_header} =" in line or f"{target_header}=" in line:
                inside_target_section = True

            if inside_target_section:
                extracted_lines.append(line)
                bracket_count += line.count("{")
                bracket_count -= line.count("}")

                if bracket_count == 0 and len(extracted_lines) > 1:
                    break

        if not extracted_lines:
            print(f"Error: Header '{target_header}' not found in config file.")
            return False
        
        mod_names = extract_subheaders(extracted_lines)

        comment_lines = ["-- EXPORTED_MOD_LIST_START\n"]
        for name in mod_names:
            comment_lines.append(f"-- MOD: {name}\n")
        comment_lines.append("-- EXPORTED_MOD_LIST_END\n\n")

        final_output = comment_lines + extracted_lines

        export_full_path = os.path.join(export_destination_folder, external_settings_file)
        with open(export_full_path, "w", encoding="utf-8") as f:
            f.writelines(final_output)

        print(f"Successfully exported {target_header} to: {export_full_path}")
        return True
    
    except Exception as e:
        print(f"Failed to generate new shareable mod settings file: {e}")
        return False
    
if __name__ == "__main__":
    write_new_shareable_settings_file(
        external_settings_file="mod_settings_config.txt",
        target_header="mods_settings"
    )
