The graphical user interface was designed using QtDesigner and saved as SALSA_UI.ui. This
can be changed by running "designer SALSA_UI.ui". After changing the ui file it must be
parsed to a python module, i.e. the file UI.py. This is done automatically by running 
"pyuic5 SALSA_UI.ui > UI.py".

To create translation files:
1. Create UI in QtDesigner (linux command: designer) --> SALSA_UI.ui
2. Generate ts file (linux command: pylupdate5 SALSA_UI.ui -ts sv.ts)

To update translation files:
1. Use QtLinguist to translate the ts file (linu command: linguist sv.ts).
2. Possibly edit the .ts file manually in case something is wrong.
3. Convert .ts to .qm (linux command: lrelease sv.ts)
