> [!WARNING]
> **This repository is no longer maintained.**
>
> SALSA has been rewritten in Rust and active development now happens at
> **[salsa-telescope/salsa](https://github.com/salsa-telescope/salsa)**.
> This repository is kept online for reference only. Parts of the old tools
> and documentation have been migrated to the new repository.

Old description below:

Code developed for the 2.3m radio telescopes SALSA in Onsala, Sweden.

The telescope can be described as four parts:
- The MD01 control unit, which is driving the az/el motors.
- The USRP, which is a digital sampler used to record data.
- The control program, communicating with the MD01 and the USRP,
  see the Control_program folder.
- The website, which is running the CMS system Drupal to handle user
  accounts, documentation and an online data archive for all users.
  The data archive is displayed using a custom Drupal Views Plugin, which
  is in the Website-folder.
