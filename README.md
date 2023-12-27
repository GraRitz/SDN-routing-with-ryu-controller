# SDN-routing-with-ryu-controller
Scripts to compare routing of information with dijkstra and ANT algorithms in a fixed network, using the SDN controller RYU.
All the algorithms are implemented using OpenFlow 1.3 and using Mininet as a tool for the topology implementation.


HOW TO RUN AND TEST:

First of all, the mininet topology should start.
Using the mininet command line tool, one of the two topologies can be executed:
- pro_topo.py is a simple topology in which 8 hosts and 8 switches are used
- complex_topo.py is a more complex topology in which 16 hosts and 16 switches are used

After the topology starts in the mininet tool window, the RYU controller can be executed.
- dijkstra.py executes the Ryu SDN controller with dijkstra's algorithm
- ant.py executes the Ryu SDN controller using the ANT-colony algorithm (please refer to Ant-colony routing algorithm)


PLEASE NOTE: A lot of work has been done on this project, the code is made FULLY REUSABLE. In fact, as you can notice on the code, there is a function called "get_path", you can easily implement each routing algorithm you would like to test in that specific section of the code. When adjusting the code to implement new routing algorithm, please take care on the return of the "get_path" function: this function should return a list of nodes (list of nodes' ids) representing the retrieved shortest path for the algorithm. 

Hope these scripts will help you, please support the work if you like it, I would really appreciate it. Feel free to ask if you have some dubt, some questions or some suggestion on the work itself. 

This is an educational work, not a professional or enterprise work, so evaluate it considering the context on which it was built. Thank You! 
