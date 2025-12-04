# Command Interpreter Rules

When the user types a Linux-style command (e.g. ls, cat, echo, rm, git log),
translate it internally into the matching GitHubAction call.

Default context:
nowner = rabruni
repo  = ai_arch
branch = main
root = /

Mappings:
- ls [path] —  listRootContents or getPathContents
- cat [path] —  getPathContents
- echo "[text]" > [path] — writeFile
- rm [path] —  deleteFile
- git log [path] —  listCommits(path)
- git branch —  listBranches