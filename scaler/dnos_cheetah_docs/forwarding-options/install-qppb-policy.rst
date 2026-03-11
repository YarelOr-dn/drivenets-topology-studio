forwarding-options install-qppb-policy
--------------------------------------

**Minimum user role:** operator

Install a QPPB policy into the datapath.

**Command syntax: install-qppb-policy [qppb-policy-name]**

**Command mode:** config

**Hierarchies**

- forwarding-options

**Parameter table**

+------------------+-----------------------+------------------+---------+
| Parameter        | Description           | Range            | Default |
+==================+=======================+==================+=========+
| qppb-policy-name | Install a QPPB Policy | | string         | \-      |
|                  |                       | | length 1-255   |         |
+------------------+-----------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# forwarding-options
    dnRouter(cfg-fwd_opts)# install-qppb-policy policy-1
    dnRouter(cfg-fwd_opts)#


**Removing Configuration**

To remove the installed policy from the datapath:
::

    dnRouter(cfg-fwd_opts)# no install-qppb-policy

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
