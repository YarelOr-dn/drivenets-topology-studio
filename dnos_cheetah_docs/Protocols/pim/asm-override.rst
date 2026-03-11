protocols pim asm-override
--------------------------

**Minimum user role:** operator

When sub-ranges from SSM group ranges are statically or dynamically mapped to RPs, enable ASM override.

To enable the ASM override for SSM group ranges:

**Command syntax: asm-override [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols pim

**Note**
- PIM register and MSDP SA messages are not accepted, generated, or forwarded for group addresses within the SSM range, unless asm-override is enabled and SSM group sub-ranges are mapped to RPs.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | When enabled the PIM SSM ranges should also be allowed for ASM and Join(\*,G)    | | enabled    | disabled |
|             | for G in the SSM ranges shall be accpeted                                        | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# asm-override enabled
    dnRouter(cfg-protocols-pim)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-pim)# no asm-override

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
