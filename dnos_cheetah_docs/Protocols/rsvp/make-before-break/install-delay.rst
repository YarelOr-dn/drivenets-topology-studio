protocols rsvp make-before-break install-delay
----------------------------------------------

**Minimum user role:** operator

After the LSP is up and ready to be installed, you can delay the installation of the new path (LSP) in the FIB. During this time, the NCR will not switch to the new path.
To delay the path installation in the FIB:

**Command syntax: install-delay [install-delay]**

**Command mode:** config

**Hierarchies**

- protocols rsvp make-before-break

**Parameter table**

+---------------+-------------------------------------------------------------+---------+---------+
| Parameter     | Description                                                 | Range   | Default |
+===============+=============================================================+=========+=========+
| install-delay | set the time to delay the switchover to the new tunnel path | 0-65535 | 5       |
+---------------+-------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# make-before-break
    dnRouter(cfg-protocols-rsvp-mbb)# install-delay 50


**Removing Configuration**

To revert to the default delay interval:
::

    dnRouter(cfg-protocols-rsvp-mbb)# no install-delay

**Command History**

+---------+--------------------------------------------+
| Release | Modification                               |
+=========+============================================+
| 9.0     | Command introduced                         |
+---------+--------------------------------------------+
| 10.0    | Changed default value from 20 to 5 seconds |
+---------+--------------------------------------------+
