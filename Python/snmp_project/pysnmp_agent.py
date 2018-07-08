from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp
from pyasn1.codec.ber import encoder, decoder
from pysnmp.proto import api
import time, bisect
from threading import Thread

try:
    import SocketServer  # python 2
except ImportError:
    import socketserver as SocketServer  # python 3


class GEN_retT(object):
    """
   Return values for most FB's (of course not NET_COMMUNIC, NET_COMMUNIC is a bit different)
   """
    xDone = False
    xError = False
    iStatus = -1


class SNMP_ret_T(GEN_retT):
    """
   Class usable as return values for SNMP function blocks
   """
    # GET and GETNEXT only
    udValueLength = 0
    usValueASNType = 0
    abValue = []
    # GETNEXT only
    sOID = 'NoOID'


class ASNType(object):
    """
   possible types for SNMP objects
   """
    BOOLEAN = 0x01
    INTEGER = 0x02
    BIT_STR = 0x03
    OCTET_STR = 0x04
    NULL = 0x05
    OBJECT_ID = 0x06
    SEQUENCE = 0x10
    SET = 0x11

    UNIVERSAL = 0x00
    APPLICATION = 0x40
    CONTEXT = 0x80
    PRIVATE = 0xC0

    PRIMITIVE = 0x00
    CONSTRUCTOR = 0x20

    LONG_LEN = 0x80
    EXTENSION_ID = 0x1F
    BIT8 = 0x80


class SeleObjCalls(object):
    """
   global object to store snmp information
   """
    moduleType = 'Not jet collected'
    lastSetName = ()
    lastSetValue = None
    lastCommunity = None


class snmpObj:
    name = ()
    value = None

    def __init__(self, name, value, snmpCalls, moduletype=None):
        self.name = name
        self.value = value
        self.moduleType = moduletype
        self.registeredCalls = snmpCalls

    def __eq__(self, other):
        return self.name == other

    def __ne__(self, other):
        return self.name != other

    def __lt__(self, other):
        return self.name < other

    def __le__(self, other):
        return self.name <= other

    def __gt__(self, other):
        return self.name > other

    def __ge__(self, other):
        return self.name >= other

    def __call__(self, protoVer):
        if self.moduleType is not None:
            self.registeredCalls.moduleType = self.moduleType
        if isinstance(self.value, basestring):
            return api.protoModules[protoVer].OctetString(self.value)
        return api.protoModules[protoVer].Integer(self.value)

    def set(self, protoVer, newValue):
        self.value = newValue
        self.registeredCalls.lastSetName = self.name
        self.registeredCalls.lastSetValue = newValue


class SNMPAgent(Thread):
    """
   SNMP Agent which provides some simple SNMP objects and is started in a Thread
   """

    snmpCalls = SeleObjCalls()

    def __init__(self, serverIP, moduleType='Company_Name'):
        """
       Initializer, creates the available objects
       :param moduleType: selection which moduleType should be simulated (Company_Name, Naratec_WLAN, VDS_Switch or None)
       :return:
       """
        Thread.__init__(self)
        self.serverIP = serverIP
        self.transportDispatcher = AsynsockDispatcher()

        self.mibInstr = (snmpObj((1, 3, 6, 1, 2, 1, 1, 1, 0), 'Test passed', self.snmpCalls),
                         snmpObj((1, 3, 6, 1, 2, 1, 1, 1, 2, 0), 123, self.snmpCalls),
                         snmpObj((1, 3, 6, 1, 2, 1, 1, 2, 25, 0), 456, self.snmpCalls),
                         snmpObj((1, 3, 6, 1, 2, 1, 1, 3, 2, 0), 78910, self.snmpCalls))

        if 'Company_Name' in moduleType:
            self.mibInstr += (snmpObj((1, 3, 6, 1, 4, 1, 32405, 0), 123, self.snmpCalls, 'Company_Name'),)
        if 'Naratec_WLAN' in moduleType:
            self.mibInstr += (snmpObj((1, 3, 6, 1, 4, 1, 9272, 1001, 1, 1, 2, 0), 456, self.snmpCalls, 'Naratec_WLAN'),)
        if 'VDS_Switch' in moduleType:
            self.mibInstr += (snmpObj((1, 3, 6, 1, 4, 1, 33658, 3, 1, 1, 0), 78910, self.snmpCalls, 'VDS_Switch'),)

        self.mibInstr += (
        snmpObj((1, 3, 6, 1, 4, 1, 50000, 600, 601, 6002, 0), 'This is the Last OID', self.snmpCalls),)

        self.mibInstrIdx = {}
        for mibVar in self.mibInstr:
            self.mibInstrIdx[mibVar.name] = mibVar

        self.snmpCalls.moduleType = 'No GET registered'

    def cbFun(self, transportDispatcher, transportDomain, transportAddress, wholeMsg):
        """
       Callback for reception of SMNP frames

       :param transportDispatcher: used dispatcher
       :param transportDomain: OID of requested object
       :param transportAddress: IP and Port of received message
       :param wholeMsg: received message
       :return: empty, processed message
       """
        while wholeMsg:
            msgVer = api.decodeMessageVersion(wholeMsg)
            if msgVer in api.protoModules:
                pMod = api.protoModules[msgVer]
            else:
                print('Unsupported SNMP version %s' % msgVer)
                return
            reqMsg, wholeMsg = decoder.decode(
                wholeMsg, asn1Spec=pMod.Message(),
            )
            rspMsg = pMod.apiMessage.getResponse(reqMsg)
            rspPDU = pMod.apiMessage.getPDU(rspMsg)
            reqPDU = pMod.apiMessage.getPDU(reqMsg)
            varBinds = [];
            pendingErrors = []
            errorIndex = 0
            # GETNEXT PDU
            if reqPDU.isSameTypeWith(pMod.GetNextRequestPDU()):
                # Produce response var-binds
                for oid, val in pMod.apiPDU.getVarBinds(reqPDU):
                    errorIndex = errorIndex + 1
                    # Search next OID to report
                    nextIdx = bisect.bisect(self.mibInstr, oid)
                    if nextIdx == len(self.mibInstr):
                        # Out of MIB
                        varBinds.append((oid, val))
                        pendingErrors.append(
                            (pMod.apiPDU.setEndOfMibError, errorIndex)
                        )
                    else:
                        # Report value if OID is found
                        varBinds.append(
                            (self.mibInstr[nextIdx].name, self.mibInstr[nextIdx](msgVer))
                        )
            elif reqPDU.isSameTypeWith(pMod.GetRequestPDU()):
                for oid, val in pMod.apiPDU.getVarBinds(reqPDU):
                    if oid in self.mibInstrIdx:
                        varBinds.append((oid, self.mibInstrIdx[oid](msgVer)))
                        self.snmpCalls.lastCommunity = str(reqMsg._componentValues[1])
                    else:
                        # No such instance
                        varBinds.append((oid, val))
                        pendingErrors.append(
                            (pMod.apiPDU.setNoSuchInstanceError, errorIndex)
                        )
                        break
            elif reqPDU.isSameTypeWith(pMod.SetRequestPDU()):
                for oid, val in pMod.apiPDU.getVarBinds(reqPDU):
                    if oid in self.mibInstrIdx:
                        varBinds.append((oid, self.mibInstrIdx[oid].set(msgVer, val)))
                    else:
                        # No such instance
                        varBinds.append((oid, val))
                        pendingErrors.append(
                            (pMod.apiPDU.setNoSuchInstanceError, errorIndex)
                        )

            else:
                # Report unsupported request type
                pMod.apiPDU.setErrorStatus(rspPDU, 'genErr')
            pMod.apiPDU.setVarBinds(rspPDU, varBinds)
            # Commit possible error indices to response PDU
            for f, i in pendingErrors:
                f(rspPDU, i)
            transportDispatcher.sendMessage(
                encoder.encode(rspMsg), transportDomain, transportAddress
            )
        return wholeMsg

    def run(self):
        """
       Start of SNMP Server
       :return: None
       """
        self.transportDispatcher.registerRecvCbFun(self.cbFun)
        # UDP/IPv4
        self.transportDispatcher.registerTransport(
            udp.domainName, udp.UdpSocketTransport().openServerMode((self.serverIP, 161))
        )
        self.transportDispatcher.jobStarted(1)
        try:
            # Dispatcher will never finish as job#1 never reaches zero
            self.transportDispatcher.runDispatcher(1)
        except:
            self.transportDispatcher.closeDispatcher()
            raise

    def stop(self):
        """
       Shutdown SNMP Server by closing the dispatcher
       :return:
       """
        self.transportDispatcher.jobFinished(1)
        self.transportDispatcher.unregisterRecvCbFun(recvId=None)
        self.transportDispatcher.unregisterTransport(udp.domainName)


if __name__ == "__main__":
    print("hello")
    snmp_obj = SNMPAgent(serverIP='127.0.0.1', moduleType='xps9560')
    snmp_obj.start()
    a = raw_input('press a key to exit')
    snmp_obj.stop()
