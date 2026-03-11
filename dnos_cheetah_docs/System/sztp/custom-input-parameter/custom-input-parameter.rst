system sztp custom-input-parameter
----------------------------------

**Minimum user role:** admin

To Configure an custom input parameter that will be included in the get-bootstrap-data RPC input:

**Command syntax: custom-input-parameter [custom-input-parameter]**

**Command mode:** config

**Hierarchies**

- system sztp

**Note**

- custom input parameter MUST NOT conflict with existing input parameters according to RFC

**Parameter table**

+------------------------+------------------------------+------------------+---------+
| Parameter              | Description                  | Range            | Default |
+========================+==============================+==================+=========+
| custom-input-parameter | Name of the custom parameter | | string         | \-      |
|                        |                              | | length 1-255   |         |
+------------------------+------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# sztp
    dnRouter(cfg-system-sztp)# custom-input-parameter my-parameter
    dnRouter(cfg-system-sztp-custin)# !
    dnRouter(cfg-system-sztp)# custom-input-parameter second-parameter
    dnRouter(cfg-system-sztp-custin)# !


**Removing Configuration**

To remove the configuration of SZTP custom input parameter:
::

    dnRouter(cfg-system-sztp)# no custom-input-parameter my-parameter

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
