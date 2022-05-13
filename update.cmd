set gitdir=%CD%\pgit
set path=%gitdir%\cmd;%path%
if exist .\new_editor\ rmdir /s /Q new_editor
if exist .\OpenPLC_Editor\ rmdir /s /Q OpenPLC_Editor
git clone https://github.com/thiagoralves/OpenPLC_Editor
if exist .\OpenPLC_Editor\editor\ (
  move .\OpenPLC_Editor\editor .\new_editor
  rmdir /s /Q OpenPLC_Editor
  echo "Update applied successfully"
) else (
  echo "Error cloning from repository!"
)
