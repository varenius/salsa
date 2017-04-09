# SALSA project
----------------------------------------------------------------------------------------

Code developed for the 2.3m radio telescopes SALSA in Onsala, Sweden.

The telescope can be described as four parts:
- The RIO, which is a controller board running code (see the DMC folder),
  to control the rotors, i.e. move the telescope.
- The USRP, which is a digital sampler used to record data.
- The control program, communicating with the RIO and the USRP,
  see the Control_program folder.
- The website, which is running the CMS system Drupal to handle user
  accounts, documentation and an online data archive for all users.
  The data archive is displayed using a custom Drupal Views Plugin, which
  is in the Website-folder.
  
