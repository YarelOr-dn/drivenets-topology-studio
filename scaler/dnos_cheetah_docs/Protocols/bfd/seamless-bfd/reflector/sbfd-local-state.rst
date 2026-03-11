protocols bfd seamless-bfd reflector sbfd-local-state
-----------------------------------------------------

**Minimum user role:** operator

To set the Seamless BFD Reflector state that is sent in the response message.

**Command syntax: sbfd-local-state [sbfd-local-state]**

**Command mode:** config

**Hierarchies**

- protocols bfd seamless-bfd reflector

**Parameter table**

+------------------+--------------------------------------+----------------+---------+
| Parameter        | Description                          | Range          | Default |
+==================+======================================+================+=========+
| sbfd-local-state | set whether bfd protection is in use | | up           | up      |
|                  |                                      | | admin-down   |         |
+------------------+--------------------------------------+----------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# seamless-bfd
    dnRouter(cfg-protocols-bfd-seamless)# reflector reflector1
    dnRouter(cfg-bfd-seamless-reflector)# sbfd-local-state admin-down
    dnRouter(cfg-bfd-seamless-reflector)#


**Removing Configuration**

To restore the sbfd-local-state to its default of 'up'. 
::

    dnRouter(cfg-bfd-seamless-reflector)# no sbfd-local-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
