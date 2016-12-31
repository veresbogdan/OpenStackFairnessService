Fairness Service
================

A service to enforce a fair resource utilization in a OpenStack infrastructure
by automatic and dynamic reallocation of the resources (CPU, RAM, Disk I/O, Network I/O)
during runtime.

----

Installation instructions
-------------------------

Execute following steps on the controller and all compute nodes:

1. Create a folder in /usr/lib/python2.7/dist-packages
2. cd into the new folder
3. ``git clone https://github.com/patanric/fairness-service.git``
4. On the Controller run the controller_manager.py as root: ``cd fairness-service/fairness/node_service`` and ``sudo python controller_manager.py ../../fairness.ini``
5. On the Compute nodes run the node_manager.py: ``cd fairness-service/fairness/node_service`` and ``python node_manager.py ../../fairness.ini``
