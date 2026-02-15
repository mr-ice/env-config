env-config is to be a tool to allow the operator to control their shell environment startup files

Features

1. Determine the current shell from the user's loginShell (usually from getpwent), Determine the intended shell from the parent process, SHELL environment variable, and command-line argument.  When any of these are different, determine which is the intended shell and what needs to change.  If intended is not different or specified, then use the current shell as the intended shell.

2. Determine the shell environment startup files in the user's home directory that are used by each shell family.  Do this by using strace on shell invocation with various flags and listing the files that are opened by the shell that are in the user's home directory.   Three shell families should be considered initially: tcsh, bash, and zsh.   Keep these files handy (and/or cache them) for future invocations.   Offer command-line mode to show this list.  Also show this in TUI mode.    Include other files that 'sound like' the ones that are invoked, to be displayed alongside the invoked files, in case the operator wants to explore why some files are not included.

3. Establish a global and user-level configuration file for configuration elements for this env-config tool.  Establish the elements that need to be there, and provide a command-line and TUI way to edit these elements storing operator specific ones in the operator's home directory.

4. Have three modes.  Non-interactive, Interactive command-line, and TUI mode.  If the operation and all values required to do it are provided, continue in non-interactive mode.  If some values are required to complete the operation, query the operator in interactive command-line mode. If no operation is selected, launch TUI mode.  All TUI operations must be able to be done by command-line and vice-versa.  Have the TUI launch another instance of the shell in command-line non-interactive mode to carry out operations.  Ensure that messages from said operations are displayed in the TUI.

5. If the intended shell is different from the current user's loginShell, allow an operation to change or request change of the shell.  In most macos/linux the shell can be changed, but in my intended destination the shell is in ActiveD Directory and an issue has to be raised.  Have this operation in a module that can be provided/filled in later to do the raising of an issue.

6. Have an operator to show the shell environment startup files that are for the 'current' shell and ones for the 'intended' shell.  In different colors if these are different.   Show any startup files in the user's home directory that are used by alternate shells that aren't current and intended as well (in a third color).  In TUI mode make this a default display.

7. Have controls to `backup` `archive` (backup and delete), or `restore` files from archives.   Have optional filters to exclude some files (and perhaps others to include some files).  When restoring in TUI mode have a picker with a filter that can be typed into and substrings select -- at the commandline default to the most recent archive but allow a command-line parameter to choose it by substring matching.  in TUI mode don't activate the 'restore' button until a unique archive is selected.  In command-line mode give the operator feedback if they didn't select a unique archive.   Establish on tool startup which files that are normally invoked are different from those in the most recent backup file.  Provide an indicator when showing these files whether they are backed up or not.

8. A repo url and named destination will be in the global configuration file.  In these operations default should be to ask the operator to perform the steps, unless specifically requested on the commandline or in the TUI, in which case do not verify.
   1. If the destination is not present, clone the repo to the destination.  Ensure it is on main:HEAD.
   2. If the destination exists but is not a clone of the repo, create a backup with this destination included, then remove it and do step 1.
   3. If the destination is a clone of the repo and on the 'main' branch but is not on main:HEAD, 'pull' to make it up-to-date.
   4. If the destination is a clone of the repo on a branch other than main, warn the operator but do not change it.

9. Have controls to `init` the shell environment for the user to the intended shell.  This will `archive` the files in the user's directory if they are not currently archived, then copy files from the repo destination based on the shell family into the user's home directory.

10. Have controls to pick additional optional shell initialization files from a curated list. The curated list will be found in directories in a configuration element in the global config.    The same configuration element in the user's config will append to the global list.
    1.  These files will have a one line summary of what they do, extract this to show the operator what they are choosing.
    2.  These files must have a filename of {shellrc}-{name} and they will be installed as ~/.{shellrc}-{name}.  {shellrc} here is which file they would modify from a list such as zshrc, zshenv, zprofile, zlogin, zlogout (establish a list of these in the global config as well).
    3.  Assume that the appropriate files in the repo will have a stanza to include files matching this pattern.  For example .zshenv will have the following, possibly with a check for interactive to allow output or throw it to /dev/null
```
for _rc in $HOME/.zshenv-*; do
    source $_rc
done
```

    4.  Ignore any directories in the path that are not associated with a repo and/or not on main:HEAD at the time of the selection.  Allow this to be overridden by the user's configuration so that developers can append development directories to their path.
    5.  Keep a registry of these selections and the source where they came from.


11. Have an update action which will ensure that all files in the home directory which came from remote locations are updated to the latest from those locations.  In the case of the repo destination do a direct comparision.  In the case of additional optional shell initialization files use the registry of locations to check for updates.


Make sure each feature works and has good tests before integrating it into the operator endpoint scripts and TUI.