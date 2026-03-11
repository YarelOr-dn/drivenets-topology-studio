system ncp security signature-validation
----------------------------------------

**Minimum user role:** operator

Enter signature validation related configuration settings.

To configure signature validation parameters:

**Command syntax: signature-validation**

**Command mode:** config

**Hierarchies**

- system ncp security

**Note**

- Notice the change in prompt.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# security
    dnRouter(cfg-system-ncp-7-security)# signature-validation
    dnRouter(cfg-system-ncp-7-security-signature-validation)#


**Removing Configuration**

To revert the signature-validation to its default value:
::

    dnRouter(cfg-system-ncp-7-security)# no signature-validation

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.2    | Command introduced |
+---------+--------------------+
