Entering Remarks in Commands
----------------------------

**Minimum user role:** operator

You can add remarks in operation as well as in configuration commands by specifying a hash sign (#) before the remark. When copying the configuration using external tools/scripts, the remarks will be copied as well, but only during the configuration session and while the remarks are visible on screen.

**Example:**
dnRouter(cfg)# interface bundle-1 mtu 1514
dnRouter(cfg-if)# only comment

**Note**
The remark is not saved to the configuration file and is not visible in any show command.




