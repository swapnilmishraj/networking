Problem statement: Extend an snmp agent so that returns a specific/custom OID value.

Solutions:
1.	With pass-through scripts --> With Python, snmp-passpersist module--> pass_persist allows you to implement an arbitrary MIB module. 
2.	Language C --> "new" API --> Net-SNMP comes with mib2c, a tool that will help you convert a MIB module into C code: after a few questions, you will get a skeleton C code you will have to complete with the logic to retrieve real objects. 
			A generated file also provides directions on what to do (with some magic command to have a step-by-step cookbook).
3. 	C with “traditional” API
4.	Python pysnmp library --> let us implement here python for now.
