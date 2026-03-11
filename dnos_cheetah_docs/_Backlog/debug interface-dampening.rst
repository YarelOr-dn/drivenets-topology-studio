debug interface-dampening - supported in v11.1
----------------------------------------------

**Command syntax: debug interface-dampening [parameter]**

**Description:** Debug interface dampening events

**CLI example:**
::

	
	dnRouter# configure
	dnRouter(cfg)# debug interface-dampening 
	dnRouter(cfg)# debug interface-dampening timer-expire-event
	dnRouter(cfg)# debug interface-dampening manual-clear-event 
	dnRouter(cfg)# debug interface-dampening penalty-change-event 
	dnRouter(cfg)# debug interface-dampening exceeding-suppress-event 
	dnRouter(cfg)# debug interface-dampening decay-below-reuse-event 
	
	dnRouter(cfg)# no debug interface-dampening 
	dnRouter(cfg)# no debug interface-dampening timer-expire-event
	
	
	
**Command mode:** operational/config

**TACACS role:**

TACACS role "operator" - debug logging is a persistent configuration

**Note:**

setting "debug interface-dampening" will enable all debug feature

**Help line:**

**Parameter table:**

+-----------+--------------------------+---------------------------------------+
| Parameter | Values                   | description                           |
+===========+==========================+=======================================+
| parameter | Timer-expire-event       | debug timer expire events             |
+-----------+--------------------------+---------------------------------------+
|           | Penalty-change-event     | debug penalty change events           |
+-----------+--------------------------+---------------------------------------+
|           | Manual-clear-event       | debug manual clear events             |
+-----------+--------------------------+---------------------------------------+
|           | Exceeding-suppress-event | debug exceeding suppress level events |
+-----------+--------------------------+---------------------------------------+
|           | Decay-below-reuse-event  | debug decay below reuse level events  |
+-----------+--------------------------+---------------------------------------+
