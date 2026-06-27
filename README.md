# Darktide Config #

The Darktide_Config_Updater.exe will be found in the shared modpack folder along
with a file called mod_settings_config.txt.

Open the '.exe' to run the updater and it will search for both your local Darktide
folder to find the user_settings.config file the game references, and the
mod_settings_config.txt to read and inject the specific mod settings you want into
your local file. If it can't find one of these, it will request that you manually
select where they are located. Once that's complete, the console will open to the
main menu where you can select your actions.

To add NEW SETTINGS or UPDATE PREVIOUS SETTINGS, simply type "1" into the menu and
hit Enter to run this. This will take you to the mod selection screen where you can
scroll through the mods listed in the mod_settings_config.txt created by Mister E. 
On this screen, all mods will initially be pre-selected.

    If you want the SETTINGS FOR EVERY MOD available in the pack, simply press Enter 
    again. This will insert all of Mister E's settings for each selected mod into your
    user_settings.config file and create a '.bak' backup file in case something goes
    wrong or you decide you don't want the imported settings. *Don't delete* this unless
    you are *sure* you don't want to return to your previous config settings. After the
    task is run, press Enter to return to the menu, then type "3" to safely close the
    console.

    If you there are any SPECIFIC MODS you don't want to use, go through the list and
    deselect those you wish to exclude, then press Enter to import them. This will
    insert all of Mister E's settings for each selected mod into your
    user_settings.config file and create a '.bak' backup file in case something goes
    wrong or you decide you don't want the imported settings. *Don't delete* this unless
    you are *sure* you don't want to return to your previous config settings. After the
    task is run, press Enter to return to the menu, then type "3" to safely close the
    console.

To RESTORE YOUR PREVIOUS CONFIG and mod settings, simply type "2" into the menu and
hit Enter to run this. This will go through and restore your user_settings.config
using the most recent backup file found in the 'Darktide' folder, then it will clean
the '.bak' file to clear extra clutter in your folder. From here, press Enter to
return to the menu, at which point you can either choose to select different mods
by typing "1", or you can type "3" to safely close the console.
