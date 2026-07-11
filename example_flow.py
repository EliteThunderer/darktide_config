import argparse

# all of your old fcns go up here!
# except the ones you don't need anymore,
# like the interactive path selectors, etc.

if __name__=='__main__':
    parser = argparse.ArgumentParser(
                        prog='ProgramName',
                        description='What the program does',
                        epilog='Text at the bottom of help')

    parser.add_argument('mode',help="")
    # stick all the arguments you need here (the ones I showed and any others you want)
    
    # this variable 'args' becomes a Namespace that holds all the flags
    args = parser.parse_args()
    
    # at this point, you have all the args, 
    # so you need to do some checking to see
    # if they have a valid mode selected and 
    # that they used the right flags for the 
    # right mode.

    # After those checks, you can assume you 
    # have the same setup as before: a config
    # path, a path to a darktide config folder,
    # and a path to a mods folder. Do exactly 
    # what you did in the first one. Ask for
    # the mods list, use that to generate settings,
    # write settings, exit.

    # This file should exit when done, instead of looping
    # infinitely. You can print out your cool ascii
    # art logo at the end as a goodbye message.
