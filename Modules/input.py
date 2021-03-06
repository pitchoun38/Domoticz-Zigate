#!/usr/bin/env python3
# coding: utf-8 -*-
#
# Author: zaraki673 & pipiche38
#
"""
    Module: z_input.py

    Description: manage inputs from Zigate

"""

import Domoticz
import binascii
import time
import struct
import queue
import time
import json

from Modules.domoticz import MajDomoDevice, lastSeenUpdate
from Modules.tools import timeStamped, updSQN, DeviceExist, getSaddrfromIEEE, IEEEExist, initDeviceInList
from Modules.output import sendZigateCmd, leaveMgtReJoin, rebind_Clusters
from Modules.status import DisplayStatusCode
from Modules.readClusters import ReadCluster
from Modules.LQI import mgtLQIresp
from Modules.database import saveZigateNetworkData
from Modules.consts import ADDRESS_MODE

#from Modules.adminWidget import updateNotificationWidget, updateStatusWidget

from Classes.IAS import IAS_Zone_Management
from Classes.AdminWidgets import  AdminWidgets
from Classes.GroupMgt import GroupsManagement


def ZigateRead(self, Devices, Data):
    Domoticz.Debug("ZigateRead - decoded data : " + Data + " lenght : " + str(len(Data)) )

    FrameStart=Data[0:2]
    FrameStop=Data[len(Data)-2:len(Data)]
    if ( FrameStart != "01" and FrameStop != "03" ): 
        Domoticz.Error("ZigateRead received a non-zigate frame Data : " + Data + " FS/FS = " + FrameStart + "/" + FrameStop )
        return

    MsgType=Data[2:6]
    MsgLength=Data[6:10]
    MsgCRC=Data[10:12]

    if len(Data) > 12 :
        # We have Payload : data + rssi
        MsgData=Data[12:len(Data)-4]
        MsgRSSI=Data[len(Data)-4:len(Data)-2]
    else :
        MsgData=""
        MsgRSSI=""

    Domoticz.Debug("ZigateRead - MsgType: %s, MsgLength: %s, MsgCRC: %s, Data: %s; RSSI: %s" \
            %( MsgType, MsgLength, MsgCRC, MsgData, MsgRSSI) )

    if str(MsgType)=="004d":  # Device announce
        Domoticz.Debug("ZigateRead - MsgType 004d - Reception Device announce : " + Data)
        Decode004d(self, Devices, MsgData, MsgRSSI)
        return
        
    elif str(MsgType)=="00d1":  #
        Domoticz.Log("ZigateRead - MsgType 00d1 - Reception Touchlink status : " + Data)
        return
        
    elif str(MsgType)=="8000":  # Status
        Domoticz.Debug("ZigateRead - MsgType 8000 - reception status : " + Data)
        Decode8000_v2(self, MsgData)
        return

    elif str(MsgType)=="8001":  # Log
        Domoticz.Debug("ZigateRead - MsgType 8001 - Reception log Level : " + Data)
        Decode8001(self, MsgData)
        return

    elif str(MsgType)=="8002":  #
        Domoticz.Log("ZigateRead - MsgType 8002 - Reception Data indication : " + Data)
        Decode8002(self, MsgData)
        return

    elif str(MsgType)=="8003":  #
        Domoticz.Debug("ZigateRead - MsgType 8003 - Reception Liste des cluster de l'objet : " + Data)
        Decode8003(self, MsgData)
        return

    elif str(MsgType)=="8004":  #
        Domoticz.Debug("ZigateRead - MsgType 8004 - Reception Liste des attributs de l'objet : " + Data)
        Decode8004(self, MsgData)
        return
        
    elif str(MsgType)=="8005":  #
        Domoticz.Debug("ZigateRead - MsgType 8005 - Reception Liste des commandes de l'objet : " + Data)
        Decode8005(self, MsgData)
        return

    elif str(MsgType)=="8006":  #
        Domoticz.Debug("ZigateRead - MsgType 8006 - Reception Non factory new restart : " + Data)
        Decode8006(self, MsgData)
        return

    elif str(MsgType)=="8007":  #
        Domoticz.Log("ZigateRead - MsgType 8007 - Reception Factory new restart : " + Data)
        #Decode8007(self, MsgData)
        return

    elif str(MsgType)=="8009":  #
        Domoticz.Debug("ZigateRead - MsgType 8009 - Network State response : " + Data)
        Decode8009( self, Devices, MsgData)
        return


    elif str(MsgType)=="8010":  # Version
        Domoticz.Debug("ZigateRead - MsgType 8010 - Reception Version list : " + Data)
        Decode8010(self, MsgData)
        return

    elif str(MsgType)=="8014":  #
        Domoticz.Debug("ZigateRead - MsgType 8014 - Reception Permit join status response : " + Data)
        Decode8014(self, MsgData)
        return

    elif str(MsgType)=="8015":  #
        Domoticz.Debug("ZigateRead - MsgType 8015 - Get devices list : " + Data)
        Decode8015(self, Devices, MsgData)
        return
        
        
    elif str(MsgType)=="8024":  #
        Domoticz.Debug("ZigateRead - MsgType 8024 - Reception Network joined /formed : " + Data)
        Decode8024(self, MsgData, Data)
        return

    elif str(MsgType)=="8028":  #
        Domoticz.Log("ZigateRead - MsgType 8028 - Reception Authenticate response : " + Data)
        Decode8028(self, MsgData)
        return

    elif str(MsgType)=="8029":  #
        Domoticz.Log("ZigateRead - MsgType 8029 - Reception Out of band commissioning data response : " + Data)
        Decode8029(self, MsgData)
        return

    elif str(MsgType)=="802b":  #
        Domoticz.Log("ZigateRead - MsgType 802b - Reception User descriptor notify : " + Data)
        Decode802B(self, MsgData)
        return

    elif str(MsgType)=="802c":  #
        Domoticz.Log("ZigateRead - MsgType 802c - Reception User descriptor response : " + Data)
        Decode802C(self, MsgData)
        return

    elif str(MsgType)=="8030":  #
        Domoticz.Debug("ZigateRead - MsgType 8030 - Reception Bind response : " + Data)
        Decode8030(self, MsgData)
        return

    elif str(MsgType)=="8031":  #
        Domoticz.Debug("ZigateRead - MsgType 8031 - Reception Unbind response : " + Data)
        Decode8031(self, MsgData)
        return

    elif str(MsgType)=="8034":  #
        Domoticz.Log("ZigateRead - MsgType 8034 - Reception Coplex Descriptor response : " + Data)
        Decode8034(self, MsgData)
        return

    elif str(MsgType)=="8040":  #
        Domoticz.Log("ZigateRead - MsgType 8040 - Reception Network address response : " + Data)
        Decode8040(self, MsgData)
        return

    elif str(MsgType)=="8041":  #
        Domoticz.Log("ZigateRead - MsgType 8041 - Reception IEEE address response : " + Data)
        Decode8041(self, Devices, MsgData, MsgRSSI)
        return

    elif str(MsgType)=="8042":  #
        Domoticz.Debug("ZigateRead - MsgType 8042 - Reception Node descriptor response : " + Data)
        Decode8042(self, MsgData)
        return

    elif str(MsgType)=="8043":  # Simple Descriptor Response
        Domoticz.Debug("ZigateRead - MsgType 8043 - Reception Simple descriptor response " + Data)
        Decode8043(self, MsgData)
        return

    elif str(MsgType)=="8044":  #
        Domoticz.Debug("ZigateRead - MsgType 8044 - Reception Power descriptor response : " + Data)
        Decode8044(self, MsgData)
        return

    elif str(MsgType)=="8045":  # Active Endpoints Response
        Domoticz.Debug("ZigateRead - MsgType 8045 - Reception Active endpoint response : " + Data)
        Decode8045(self, Devices, MsgData)
        return

    elif str(MsgType)=="8046":  #
        Domoticz.Log("ZigateRead - MsgType 8046 - Reception Match descriptor response : " + Data)
        Decode8046(self, MsgData)
        return

    elif str(MsgType)=="8047":  #
        Domoticz.Log("ZigateRead - MsgType 8047 - Reception Management leave response : " + Data)
        Decode8047(self, MsgData)
        return

    elif str(MsgType)=="8048":  #
        Domoticz.Debug("ZigateRead - MsgType 8048 - Reception Leave indication : " + Data)
        Decode8048(self, Devices, MsgData, MsgRSSI)
        return

    elif str(MsgType)=="804a":  #
        Domoticz.Debug("ZigateRead - MsgType 804a - Reception Management Network Update response : " + Data)
        Decode804A(self, Devices, MsgData)
        return

    elif str(MsgType)=="804b":  #
        Domoticz.Log("ZigateRead - MsgType 804b - Reception System server discovery response : " + Data)
        Decode804B(self, MsgData)
        return

    elif str(MsgType)=="804e":  #
        Domoticz.Debug("ZigateRead - MsgType 804e - Reception Management LQI response : " + Data)
        mgtLQIresp( self, MsgData)    
        return

    elif str(MsgType)=="8060":  #
        Domoticz.Debug("ZigateRead - MsgType 8060 - Reception Add group response : " + Data)
        self.groupmgt.addGroupResponse( MsgData )
        return


    elif str(MsgType)=="8061":  #
        Domoticz.Debug("ZigateRead - MsgType 8061 - Reception Viex group response : " + Data)
        self.groupmgt.viewGroupResponse( MsgData )
        return

    elif str(MsgType)=="8062":  #
        Domoticz.Debug("ZigateRead - MsgType 8062 - Reception Get group Membership response : " + Data)
        self.groupmgt.getGroupMembershipResponse(MsgData)
        return

    elif str(MsgType)=="8063":  #
        Domoticz.Debug("ZigateRead - MsgType 8063 - Reception Remove group response : " + Data)
        self.groupmgt.removeGroupResponse( MsgData )
        return

    elif str(MsgType)=="8085":
        Domoticz.Debug("ZigateRead - MsgType 8085 - Reception Remote command : " + Data)
        Decode8085(self, Devices, MsgData, MsgRSSI)
        return

    elif str(MsgType)=="8095":
        Domoticz.Debug("ZigateRead - MsgType 8095 - Reception Remote command : " + Data)
        Decode8095(self, Devices, MsgData, MsgRSSI)
        return

    elif str(MsgType)=="80a0":  #
        Domoticz.Log("ZigateRead - MsgType 80a0 - Reception View scene response : " + Data)
        return

    elif str(MsgType)=="80a1":  #
        Domoticz.Log("ZigateRead - MsgType 80a1 - Reception Add scene response : " + Data)
        return

    elif str(MsgType)=="80a2":  #
        Domoticz.Log("ZigateRead - MsgType 80a2 - Reception Remove scene response : " + Data)
        return

    elif str(MsgType)=="80a3":  #
        Domoticz.Log("ZigateRead - MsgType 80a3 - Reception Remove all scene response : " + Data)
        return

    elif str(MsgType)=="80a4":  #
        Domoticz.Log("ZigateRead - MsgType 80a4 - Reception Store scene response : " + Data)
        return

    elif str(MsgType)=="80a6":  #
        Domoticz.Log("ZigateRead - MsgType 80a6 - Reception Scene membership response : " + Data)
        return
    elif str(MsgType)=="80a7":
        Domoticz.Debug("ZigateRead - MsgType 80a7 - Reception Remote command : " + Data)
        Decode80A7(self, Devices, MsgData, MsgRSSI)
        return


    elif str(MsgType)=="8100":  #
        Domoticz.Debug("ZigateRead - MsgType 8100 - Reception Real individual attribute response : " + Data)
        Decode8100(self, Devices, MsgData, MsgRSSI)
        return

    elif str(MsgType)=="8101":  # Default Response
        Domoticz.Debug("ZigateRead - MsgType 8101 - Default Response: " + Data)
        Decode8101(self, MsgData)
        return

    elif str(MsgType)=="8102":  # Report Individual Attribute response
        Domoticz.Debug("ZigateRead - MsgType 8102 - Report Individual Attribute response : " + Data)    
        Decode8102(self, Devices, MsgData, MsgRSSI)
        return
        
    elif str(MsgType)=="8110":  #
        Domoticz.Debug("ZigateRead - MsgType 8110 - Reception Write attribute response : " + Data)
        Decode8110( self, Devices, MsgData)
        return

    elif str(MsgType)=="8120":  #
        Domoticz.Debug("ZigateRead - MsgType 8120 - Reception Configure reporting response : " + Data)
        Decode8120( self, MsgData)
        return

    elif str(MsgType)=="8140":  #
        Domoticz.Debug("ZigateRead - MsgType 8140 - Reception Attribute discovery response : " + Data)
        Decode8140( self, MsgData)
        return

    elif str(MsgType)=="8401":  # Reception Zone status change notification
        Domoticz.Debug("ZigateRead - MsgType 8401 - Reception Zone status change notification : " + Data)
        Decode8401(self, Devices, MsgData)
        return

    elif str(MsgType)=="8501":
        Domoticz.Log("ZigateRead - MsgType 8501 - Reception Zone status change notification : " + Data)
        Decode8501(self, Devices, MsgData)
        return

    elif str(MsgType)=="8503":
        Domoticz.Log("ZigateRead - MsgType 8503 - Reception Zone status change notification : " + Data)
        Decode8503(self, Devices, MsgData)
        return

    elif str(MsgType)=="8701":  # 
        Domoticz.Debug("ZigateRead - MsgType 8701 - Reception Router discovery confirm : " + Data)
        Decode8701(self, MsgData)
        return

    elif str(MsgType)=="8702":  # APS Data Confirm Fail
        Domoticz.Debug("ZigateRead - MsgType 8702 -  Reception APS Data confirm fail : " + Data)
        Decode8702(self, MsgData)
        return

    else: # unknow or not dev function
        Domoticz.Log("ZigateRead - Unknow Message Type %s  - %s " %(MsgType, MsgData))
        return
    
    return

#IAS Zone
def Decode8401(self, Devices, MsgData) : # Reception Zone status change notification

    Domoticz.Log("Decode8401 - Reception Zone status change notification : " + MsgData)
    MsgSQN=MsgData[0:2]           # sequence number: uint8_t
    MsgEp=MsgData[2:4]            # endpoint : uint8_t
    MsgClusterId=MsgData[4:8]     # cluster id: uint16_t
    MsgSrcAddrMode=MsgData[8:10]  # src address mode: uint8_t
    if MsgSrcAddrMode == "02":
        MsgSrcAddr=MsgData[10:14]     # src address: uint64_t or uint16_t based on address mode
        MsgZoneStatus=MsgData[14:18]  # zone status: uint16_t
        MsgExtStatus=MsgData[18:20]   # extended status: uint8_t
        MsgZoneID=MsgData[20:22]      # zone id : uint8_t
        MsgDelay=MsgData[22:26]       # delay: data each element uint16_t
    elif MsgSrcAddrMode == "03":
        MsgSrcAddr=MsgData[10:26]     # src address: uint64_t or uint16_t based on address mode
        MsgZoneStatus=MsgData[26:30]  # zone status: uint16_t
        MsgExtStatus=MsgData[30:32]   # extended status: uint8_t
        MsgZoneID=MsgData[32:34]      # zone id : uint8_t
        MsgDelay=MsgData[34:38]       # delay: data each element uint16_t

    # 0  0  0    0  1    1    1  2  2
    # 0  2  4    8  0    4    8  0  2
    # 5a 02 0500 02 0ffd 0010 00 ff 0001
    # 5d 02 0500 02 0ffd 0011 00 ff 0001

    lastSeenUpdate( self, Devices, NwkId=MsgSrcAddrMode)
    timeStamped( self, MsgSrcAddr , 0x8401)
    updSQN( self, MsgSrcAddr, MsgSQN)

    Model = ''
    if MsgSrcAddr in self.ListOfDevices:
        if 'Model' in self.ListOfDevices[MsgSrcAddr]:
            Model =  self.ListOfDevices[MsgSrcAddr]['Model']
    else:
        Domoticz.Log("Decode8401 - receive a message for an unknown device %s : %s" %( MsgSrcAddr, MsgData))
        return

    Domoticz.Log("Decode8401 - MsgSQN: %s MsgSrcAddr: %s MsgEp:%s MsgClusterId: %s MsgZoneStatus: %s MsgExtStatus: %s MsgZoneID: %s MsgDelay: %s" \
            %( MsgSQN, MsgSrcAddr, MsgEp, MsgClusterId, MsgZoneStatus, MsgExtStatus, MsgZoneID, MsgDelay))

    if Model == "PST03A-v2.2.5" :
        ## CLD CLD
        # bit 3, battery status (0=Ok 1=to replace)
        iData = int(MsgZoneStatus,16) & 8 >> 3                 # Set batery level
        if iData == 0 :
            self.ListOfDevices[MsgSrcAddr]['Battery']="100"        # set to 100%
        else :
            self.ListOfDevices[MsgSrcAddr]['Battery']="0"
        if MsgEp == "02" :                    
            iData = int(MsgZoneStatus,16) & 1      #  For EP 2, bit 0 = "door/window status"
            # bit 0 = 1 (door is opened) ou bit 0 = 0 (door is closed)
            value = "%02d" % iData
            Domoticz.Debug("Decode8401 - PST03A-v2.2.5 door/windows status : " + value)
            MajDomoDevice(self, Devices, MsgSrcAddr, MsgEp, "0500", value)
            # Nota : tamper alarm on EP 2 are discarded
        elif  MsgEp == "01" :
            iData = (int(MsgZoneStatus,16) & 1)    # For EP 1, bit 0 = "movement"
            # bit 0 = 1 ==> movement
            if iData == 1 :    
                value = "%02d" % iData
                Domoticz.Debug("Decode8401 - PST03A-v2.2.5 mouvements alarm")
                MajDomoDevice(self, Devices, MsgSrcAddr, MsgEp, "0406", value)
            # bit 2 = 1 ==> tamper (device disassembly)
            iData = (int(MsgZoneStatus,16) & 4) >> 2
            if iData == 1 :     
                value = "%02d" % iData
                Domoticz.Debug("Decode8401 - PST03A-V2.2.5  tamper alarm")
                MajDomoDevice(self, Devices, MsgSrcAddr, MsgEp, "0006", value)
        else :
            Domoticz.Debug("Decode8401 - PST03A-v2.2.5, unknow EndPoint : " + MsgDataSrcEp)
    else :      ## default 
        alarm1 =  int(MsgZoneStatus,16) & 1 
        alarm2 =  ( int(MsgZoneStatus,16)  >> 1 ) & 1
        tamper =  ( int(MsgZoneStatus,16)  >> 2 ) & 1
        battery  = ( int(MsgZoneStatus,16) >> 3 ) & 1
        suprrprt = ( int(MsgZoneStatus,16) >> 4 ) & 1
        restrprt = ( int(MsgZoneStatus,16) >> 5 ) & 1
        trouble  = ( int(MsgZoneStatus,16) >> 6 ) & 1
        acmain   = ( int(MsgZoneStatus,16) >> 7 ) & 1
        test     = ( int(MsgZoneStatus,16) >> 8 ) & 1
        battdef  = ( int(MsgZoneStatus,16) >> 9 ) & 1

        Domoticz.Status("IAS Zone change for device:%s  - alarm1: %s, alaram2: %s, tamper: %s, battery: %s, Support Reporting: %s, restore Reporting: %s, trouble: %s, acmain: %s, test: %s, battdef: %s" \
                %( MsgSrcAddr, alarm1, alarm2, tamper, battery, suprrprt, restrprt, trouble, acmain, test, battdef))

        Domoticz.Log("Decode8401 MsgZoneStatus: %s " %MsgZoneStatus[2:4])
        value = MsgZoneStatus[2:4]
        if value == '21':
            value = '01'
        elif value == '20':
            value = '00'
        MajDomoDevice(self, Devices, MsgSrcAddr, MsgEp, "0006", value )

        if battdef or battery:
            self.ListOfDevices[MsgSrcAddr]['Battery'] = '1'

        if 'IAS' in self.ListOfDevices[MsgSrcAddr]:
            if 'ZoneStatus' in self.ListOfDevices[MsgSrcAddr]['IAS']:
                self.ListOfDevices[MsgSrcAddr]['IAS']['ZoneStatus']['alarm1'] = alarm1
                self.ListOfDevices[MsgSrcAddr]['IAS']['ZoneStatus']['alarm2'] = alarm2
                self.ListOfDevices[MsgSrcAddr]['IAS']['ZoneStatus']['tamper'] = tamper
                self.ListOfDevices[MsgSrcAddr]['IAS']['ZoneStatus']['battery'] = battery
                self.ListOfDevices[MsgSrcAddr]['IAS']['ZoneStatus']['Support Reporting'] = suprrprt
                self.ListOfDevices[MsgSrcAddr]['IAS']['ZoneStatus']['Restore Reporting'] = restrprt
                self.ListOfDevices[MsgSrcAddr]['IAS']['ZoneStatus']['trouble'] = trouble
                self.ListOfDevices[MsgSrcAddr]['IAS']['ZoneStatus']['acmain'] = acmain
                self.ListOfDevices[MsgSrcAddr]['IAS']['ZoneStatus']['test'] = test
                self.ListOfDevices[MsgSrcAddr]['IAS']['ZoneStatus']['battdef'] = battdef


    return


#Responses
def Decode8000_v2(self, MsgData) : # Status
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode8000_v2 - MsgData lenght is : " + str(MsgLen) + " out of 8")

    if MsgLen < 8 :
        Domoticz.Log("Decode8000 - uncomplete message : %s" %MsgData)
        return

    if MsgLen > 8 :
        Domoticz.Log("Decode8000 - More information . New Firmware ???")

    Status=MsgData[0:2]
    SEQ=MsgData[2:4]
    PacketType=MsgData[4:8]

    if   Status=="00" : 
        Status="Success"
    elif Status=="01" : Status="Incorrect Parameters"
    elif Status=="02" : Status="Unhandled Command"
    elif Status=="03" : Status="Command Failed"
    elif Status=="04" : Status="Busy"
    elif Status=="05" : Status="Stack Already Started"
    elif int(Status,16) >= 128 and int(Status,16) <= 244 : Status="ZigBee Error Code "+ DisplayStatusCode(Status)

    Domoticz.Debug("Decode8000_v2 - status: " + Status + " SEQ: " + SEQ + " Packet Type: " + PacketType )

    if   PacketType=="0012" : Domoticz.Log("Erase Persistent Data cmd status : " +  Status )
    elif PacketType=="0024" : Domoticz.Log("Start Network status : " +  Status )
    elif PacketType=="0026" : Domoticz.Log("Remove Device cmd status : " +  Status )
    elif PacketType=="0044" : Domoticz.Log("request Power Descriptor status : " +  Status )

    # Group Management
    if PacketType in ('0060', '0061', '0062', '0063', '0064', '0065'):
        self.groupmgt.statusGroupRequest( MsgData )

    if str(MsgData[0:2]) != "00" :
        Domoticz.Debug("Decode8000 - PacketType: %s Status: [%s] - %s" \
                %(PacketType, MsgData[0:2], Status))

    return

def Decode8001(self, MsgData) : # Reception log Level
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode8001 - MsgData lenght is : " + str(MsgLen) + " out of 2" )

    MsgLogLvl=MsgData[0:2]
    MsgDataMessage=MsgData[2:len(MsgData)]
    
    Domoticz.Status("Reception log Level 0x: " + MsgLogLvl + "Message : " + MsgDataMessage)
    return

def Decode8002(self, MsgData) : # Data indication
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode8002 - MsgData lenght is : " + str(MsgLen) + " out of 2" )

    MsgLogLvl=MsgData[0:2]
    MsgProfilID=MsgData[2:6]
    MsgClusterID=MsgData[6:10]
    MsgSourcePoint=MsgData[10:12]
    MsgEndPoint=MsgData[12:14]
    MsgSourceAddressMode=MsgData[16:18]
    if int(MsgSourceAddressMode)==0 :
        MsgSourceAddress=MsgData[18:24]  # uint16_t
        MsgDestinationAddressMode=MsgData[24:26]
        if int(MsgDestinationAddressMode)==0 : # uint16_t
            MsgDestinationAddress=MsgData[26:32]
            MsgPayloadSize=MsgData[32:34]
            MsgPayload=MsgData[34:len(MsgData)]
        else : # uint32_t
            MsgDestinationAddress=MsgData[26:42]
            MsgPayloadSize=MsgData[42:44]
            MsgPayload=MsgData[44:len(MsgData)]
    else : # uint32_t
        MsgSourceAddress=MsgData[18:34]
        MsgDestinationAddressMode=MsgData[34:36]
        if int(MsgDestinationAddressMode)==0 : # uint16_t
            MsgDestinationAddress=MsgData[36:40]
            MsgPayloadSize=MsgData[40:42]
            MsgPayload=MsgData[42:len(MsgData)]
        else : # uint32_t
            MsgDestinationAddress=MsgData[36:52]
            MsgPayloadSize=MsgData[52:54]
            MsgPayload=MsgData[54:len(MsgData)]
    
    Domoticz.Status("Reception Data indication, Source Address : " + MsgSourceAddress + " Destination Address : " + MsgDestinationAddress + " ProfilID : " + MsgProfilID + " ClusterID : " + MsgClusterID + " Payload size : " + MsgPayloadSize + " Message Payload : " + MsgPayload)
    return

def Decode8003(self, MsgData) : # Device cluster list
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode8003 - MsgData lenght is : " + str(MsgLen) + " out of 2" )

    MsgSourceEP=MsgData[0:2]
    MsgProfileID=MsgData[2:6]
    MsgClusterID=MsgData[6:len(MsgData)]

    idx = 0
    clusterLst = []
    while idx < len(MsgClusterID):
        clusterLst.append(MsgClusterID[idx:idx+4] )
        idx += 4
    
    self.zigatedata['Cluster List'] = clusterLst
    Domoticz.Status("Device Cluster list, EP source : " + MsgSourceEP + \
            " ProfileID : " + MsgProfileID + " Cluster List : " + str(clusterLst) )
    return

def Decode8004(self, MsgData) : # Device attribut list
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode8004 - MsgData lenght is : " + str(MsgLen) + " out of 2" )

    MsgSourceEP=MsgData[0:2]
    MsgProfileID=MsgData[2:6]
    MsgClusterID=MsgData[6:10]
    MsgAttributList=MsgData[10:len(MsgData)]
    
    idx = 0
    attributeLst = []
    while idx < len(MsgAttributList):
        attributeLst.append(MsgAttributList[idx:idx+4] )
        idx += 4

    self.zigatedata['Device Attributs List'] = attributeLst
    Domoticz.Status("Device Attribut list, EP source : " + MsgSourceEP + \
            " ProfileID : " + MsgProfileID + " ClusterID : " + MsgClusterID + " Attribut List : " + str(attributeLst) )
    return

def Decode8005(self, MsgData) : # Command list
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode8005 - MsgData lenght is : " + str(MsgLen) + " out of 2" )

    MsgSourceEP=MsgData[0:2]
    MsgProfileID=MsgData[2:6]
    MsgClusterID=MsgData[6:10]
    MsgCommandList=MsgData[10:len(MsgData)]
    
    idx = 0
    commandLst = []
    while idx < len(MsgCommandList):
        commandLst.append(MsgCommandList[idx:idx+4] )
        idx += 4

    self.zigatedata['Device Attributs List'] = commandLst
    Domoticz.Status("Command list, EP source : " + MsgSourceEP + \
            " ProfileID : " + MsgProfileID + " ClusterID : " + MsgClusterID + " Command List : " + str( commandLst ))
    return

def Decode8006(self,MsgData) : # Non “Factory new” Restart

    Domoticz.Debug("Decode8006 - MsgData: %s" %(MsgData))

    Status = MsgData[0:2]
    if MsgData[0:2] == "00":
        Status = "STARTUP"
    elif MsgData[0:2] == "01":
        Status = "RUNNING"
    elif MsgData[0:2] == "02":
        Status = "NFN_START"
    elif MsgData[0:2] == "06":
        Status = "RUNNING"
    Domoticz.Status("Non 'Factory new' Restart status: %s" %(Status) )

def Decode8009(self,Devices, MsgData) : # Network State response (Firm v3.0d)
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode8009 - MsgData lenght is : " + str(MsgLen) + " out of 42")
    addr=MsgData[0:4]
    extaddr=MsgData[4:20]
    PanID=MsgData[20:24]
    extPanID=MsgData[24:40]
    Channel=MsgData[40:42]
    Domoticz.Debug("Decode8009: Network state - Address :" + addr + " extaddr :" + extaddr + " PanID : " + PanID + " Channel : " + str(int(Channel,16)) )

    
    if self.ZigateIEEE != extaddr:
        self.adminWidgets.updateNotificationWidget( Devices, 'Zigate IEEE: %s' %extaddr)

    self.ZigateIEEE = extaddr
    self.ZigateNWKID = addr

    self.IEEE2NWK[extaddr] = addr
    self.ListOfDevices[addr] = {}
    self.ListOfDevices[addr]['version'] = '3'
    self.ListOfDevices[addr]['IEEE'] = extaddr
    self.ListOfDevices[addr]['Ep'] = {}
    self.ListOfDevices[addr]['Ep']['01'] = {}
    self.ListOfDevices[addr]['Ep']['01']['0004'] = {}
    self.ListOfDevices[addr]['Ep']['01']['0006'] = {}
    self.ListOfDevices[addr]['Ep']['01']['0008'] = {}
    self.ListOfDevices[addr]['PowerSource'] = 'Main'

    if self.currentChannel != int(Channel,16):
        self.adminWidgets.updateNotificationWidget( Devices, 'Zigate Channel: %s' %str(int(Channel,16)))
    self.currentChannel = int(Channel,16)

    self.iaszonemgt.setZigateIEEE( extaddr )

    Domoticz.Status("Zigate addresses ieee: %s , short addr: %s" %( self.ZigateIEEE,  self.ZigateNWKID) )

    # from https://github.com/fairecasoimeme/ZiGate/issues/15 , if PanID == 0 -> Network is done
    if str(PanID) == "0" : 
        Domoticz.Status("Network state DOWN ! " )
        self.adminWidgets.updateNotificationWidget( Devices, 'Network down PanID = 0' )
        self.adminWidgets.updateStatusWidget( Devices, 'No Connection')
    else :
        Domoticz.Status("Network state UP, PANID: %s extPANID: 0x%s Channel: %s" \
                %( PanID, extPanID, int(Channel,16) ))

    self.zigatedata['IEEE'] = extaddr
    self.zigatedata['Short Address'] = addr
    self.zigatedata['Channel'] = Channel
    self.zigatedata['PANID'] = PanID
    self.zigatedata['Extended PANID'] = extPanID
    saveZigateNetworkData( self , self.zigatedata )

    return

def Decode8010(self,MsgData) : # Reception Version list
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode8010 - MsgData lenght is : " + str(MsgLen) + " out of 8")

    MajorVersNum=MsgData[0:4]
    InstaVersNum=MsgData[4:8]
    try :
        Domoticz.Debug("Decode8010 - Reception Version list : " + MsgData)
        Domoticz.Status("Major Version Num: " + MajorVersNum )
        Domoticz.Status("Installer Version Number: " + InstaVersNum )
    except :
        Domoticz.Error("Decode8010 - Reception Version list : " + MsgData)
    else:
        self.FirmwareVersion = str(InstaVersNum)
        self.FirmwareMajorVersion = str(MajorVersNum)
        self.zigatedata['Firmware Version'] =  str(MajorVersNum) + ' - ' +str(InstaVersNum)

    return

def Decode8014(self,MsgData) : # "Permit Join" status response
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode8014 - MsgData lenght is : " +MsgData + "len: "+ str(MsgLen) + " out of 2")

    Status=MsgData[0:2]
    Domoticz.Debug("Permit Join status: %s" %Status)
    if Status == "00": 
        if self.Ping['Permit'] is None:
            Domoticz.Status("Permit Join: Off")
        self.Ping['Permit'] = 'Off'
    elif Status == "01" : 
        if self.Ping['Permit'] is None:
            Domoticz.Status("Zigate in Permit Join: On")
        self.Ping['Permit'] = 'On'
    else: 
        Domoticz.Error("Decode8014 - Unexpected value "+str(MsgData))
    self.Ping['TimeStamp'] = time.time()
    self.Ping['Status'] = 'Receive'
    Domoticz.Debug("Ping - received")

    return

def Decode8015(self, Devices, MsgData) : # Get device list ( following request device list 0x0015 )
    # id: 2bytes
    # addr: 4bytes
    # ieee: 8bytes
    # power_type: 2bytes - 0 Battery, 1 AC Power
    # rssi : 2 bytes - Signal Strength between 1 - 255
    numberofdev=len(MsgData)    
    Domoticz.Status("Number of devices recently active in Zigate = " + str(round(numberofdev/26)) )
    idx=0
    while idx < (len(MsgData)):
        DevID=MsgData[idx:idx+2]
        saddr=MsgData[idx+2:idx+6]
        ieee=MsgData[idx+6:idx+22]
        power=MsgData[idx+22:idx+24]
        rssi=MsgData[idx+24:idx+26]

        if DeviceExist(self, Devices, saddr, ieee):
            Domoticz.Debug("[{:02n}".format((round(idx/26))) + "] DevID = " + DevID + " Network addr = " + saddr + " IEEE = " + ieee + " LQI = {:03n}".format((int(rssi,16))) + " Power = " + power + " HB = {:02n}".format(int(self.ListOfDevices[saddr]['Heartbeat'])) + " found in ListOfDevices")

            if rssi !="00" :
                self.ListOfDevices[saddr]['RSSI']= int(rssi,16)
            else  :
                self.ListOfDevices[saddr]['RSSI']= 12
            Domoticz.Debug("Decode8015 : RSSI set to " + str( self.ListOfDevices[saddr]['RSSI']) + "/" + str(rssi) + " for " + str(saddr) )
        else: 
            Domoticz.Status("[{:02n}".format((round(idx/26))) + "] DevID = " + DevID + " Network addr = " + saddr + " IEEE = " + ieee + " LQI = {:03n}".format(int(rssi,16)) + " Power = " + power + " not found in ListOfDevices")
        idx=idx+26

    Domoticz.Debug("Decode8015 - IEEE2NWK      : " +str(self.IEEE2NWK) )
    return

def Decode8024(self, MsgData, Data) : # Network joined / formed
    MsgLen=len(MsgData)
    MsgDataStatus=MsgData[0:2]

    if MsgDataStatus != '00':
        if MsgDataStatus == "00": 
            Domoticz.Status("Joined existing network")
        elif MsgDataStatus == "01": 
            Domoticz.Status("Formed new network")
        elif MsgDataStatus == "04":
            Domoticz.Status("Busy Node")
        else: 
            Status = DisplayStatusCode( MsgDataStatus )
            Domoticz.Log("Network joined / formed Status: %s: %s" %(MsgDataStatus, Status) )
        return
    
    if MsgLen != 24:
        Domoticz.Debug("Decode8024 - uncomplete frame, MsgData: %s, Len: %s out of 24, data received: >%s<" %(MsgData, MsgLen, Data) )
        return

    MsgShortAddress=MsgData[2:6]
    MsgExtendedAddress=MsgData[6:22]
    MsgChannel=MsgData[22:24]

    if MsgExtendedAddress != '' and MsgShortAddress != '':
        self.currentChannel = int(MsgChannel,16)
        self.ZigateIEEE = MsgExtendedAddress
        self.ZigateNWKID = MsgShortAddress
        self.iaszonemgt.setZigateIEEE( MsgExtendedAddress )

    Domoticz.Status("Zigate details IEEE: %s, NetworkID: %s, Channel: %s, Status: %s: %s" \
            %(MsgExtendedAddress, MsgShortAddress, MsgChannel, MsgDataStatus, Status) )

def Decode8028(self, MsgData) : # Authenticate response
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode8028 - MsgData lenght is : " + str(MsgLen) + " out of 2" )

    MsgGatewayIEEE=MsgData[0:16]
    MsgEncryptKey=MsgData[16:32]
    MsgMic=MsgData[32:40]
    MsgNodeIEEE=MsgData[40:56]
    MsgActiveKeySequenceNumber=MsgData[56:58]
    MsgChannel=MsgData[58:60]
    MsgShortPANid=MsgData[60:64]
    MsgExtPANid=MsgData[64:80]
    
    Domoticz.Log("ZigateRead - MsgType 8028 - Authenticate response, Gateway IEEE : " + MsgGatewayIEEE + " Encrypt Key : " + MsgEncryptKey + " Mic : " + MsgMic + " Node IEEE : " + MsgNodeIEEE + " Active Key Sequence number : " + MsgActiveKeySequenceNumber + " Channel : " + MsgChannel + " Short PAN id : " + MsgShortPANid + "Extended PAN id : " + MsgExtPANid )
    return

def Decode802B(self, MsgData) : # User Descriptor Notify
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode802B - MsgData lenght is : " + str(MsgLen) + " out of 2" )

    MsgSequenceNumber=MsgData[0:2]
    MsgDataStatus=MsgData[2:4]
    MsgNetworkAddressInterest=MsgData[4:8]
    
    Domoticz.Log("ZigateRead - MsgType 802B - User Descriptor Notify, Sequence number : " + MsgSequenceNumber + " Status : " + DisplayStatusCode( MsgDataStatus ) + " Network address of interest : " + MsgNetworkAddressInterest)
    return

def Decode802C(self, MsgData) : # User Descriptor Response
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode802C - MsgData lenght is : " + str(MsgLen) + " out of 2" )

    MsgSequenceNumber=MsgData[0:2]
    MsgDataStatus=MsgData[2:4]
    MsgNetworkAddressInterest=MsgData[4:8]
    MsgLenght=MsgData[8:10]
    MsgMData=MsgData[10:len(MsgData)]
    
    Domoticz.Log("ZigateRead - MsgType 802C - User Descriptor Notify, Sequence number : " + MsgSequenceNumber + " Status : " + DisplayStatusCode( MsgDataStatus ) + " Network address of interest : " + MsgNetworkAddressInterest + " Lenght : " + MsgLenght + " Data : " + MsgMData)
    return

def Decode8030(self, MsgData) : # Bind response
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode8030 - MsgData lenght is : " + str(MsgLen) + " out of 2" )

    MsgSequenceNumber=MsgData[0:2]
    MsgDataStatus=MsgData[2:4]
    
    if MsgLen > 4:
        # Firmware 3.1a
        MsgSrcEp = MsgData[4:6]
        MsgSrcAddrMode = MsgData[6:8]
        if MsgDataDestMode == ADDRESS_MODE['short']:
            MsgDataDestAddr=MsgData[8:12]
            MsgDataSQN=MsgData[12:14]
        elif MsgDataDestMode == ADDRESS_MODE['ieee']:
            MsgDataDestAddr=MsgData[8:24]
            MsgDataSQN=MsgData[24:26]

    if MsgDataStatus != '00':
        Domoticz.Log("Decode8030 - Bind response SQN: %s status [%s] - %s" %(MsgSequenceNumber ,MsgDataStatus, DisplayStatusCode(MsgDataStatus)) )

    Domoticz.Debug("Decode8030 - Bind response, Sequence number : " + MsgSequenceNumber + " Status : " + DisplayStatusCode( MsgDataStatus ))
    return

def Decode8031(self, MsgData) : # Unbind response
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode8031 - MsgData lenght is : " + str(MsgLen) + " out of 2" )

    MsgSequenceNumber=MsgData[0:2]
    MsgDataStatus=MsgData[2:4]

    if MsgLen > 4:
        # Firmware 3.1a
        MsgSrcEp = MsgData[4:6]
        MsgSrcAddrMode = MsgData[6:8]
        if MsgDataDestMode == ADDRESS_MODE['short']:
            MsgDataDestAddr=MsgData[8:12]
            MsgDataSQN=MsgData[12:14]
        elif MsgDataDestMode == ADDRESS_MODE['ieee']:
            MsgDataDestAddr=MsgData[8:24]
            MsgDataSQN=MsgData[24:26]

    if MsgDataStatus != '00':
        Domoticz.Debug("Decode8031 - Unbind response SQN: %s status [%s] - %s" %(MsgSequenceNumber ,MsgDataStatus, DisplayStatusCode(MsgDataStatus)) )
    
    Domoticz.Debug("ZigateRead - MsgType 8031 - Unbind response, Sequence number : " + MsgSequenceNumber + " Status : " + DisplayStatusCode( MsgDataStatus ))
    return

def Decode8034(self, MsgData) : # Complex Descriptor response
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode8034 - MsgData lenght is : " + str(MsgLen) + " out of 2" )

    MsgSequenceNumber=MsgData[0:2]
    MsgDataStatus=MsgData[2:4]
    MsgNetworkAddressInterest=MsgData[4:8]
    MsgLenght=MsgData[8:10]
    MsgXMLTag=MsgData[10:12]
    MsgCountField=MsgData[12:14]
    MsgFieldValues=MsgData[14:len(MsgData)]
    
    Domoticz.Log("Decode8034 - Complex Descriptor for: %s xmlTag: %s fieldCount: %s fieldValue: %s, Status: %s" \
            %( MsgNetworkAddressInterest, MsgXMLTag, MsgCountField, MsgFieldValues, MsgDataStatus))

    return

def Decode8040(self, MsgData) : # Network Address response
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode8040 - MsgData lenght is : " + str(MsgLen) + " out of 2" )

    MsgSequenceNumber=MsgData[0:2]
    MsgDataStatus=MsgData[2:4]
    MsgIEEE=MsgData[4:20]
    MsgShortAddress=MsgData[20:24]
    MsgNumAssocDevices=MsgData[24:26]
    MsgStartIndex=MsgData[26:28]
    MsgDeviceList=MsgData[28:len(MsgData)]
    
    Domoticz.Status("Network Address response, Sequence number : " + MsgSequenceNumber + " Status : " 
                        + DisplayStatusCode( MsgDataStatus ) + " IEEE : " + MsgIEEE + " Short Address : " + MsgShortAddress 
                        + " number of associated devices : " + MsgNumAssocDevices + " Start Index : " + MsgStartIndex + " Device List : " + MsgDeviceList)
    return

def Decode8041(self, Devices, MsgData, MsgRSSI) : # IEEE Address response
    MsgLen=len(MsgData)

    MsgSequenceNumber=MsgData[0:2]
    MsgDataStatus=MsgData[2:4]
    MsgIEEE=MsgData[4:20]
    MsgShortAddress=MsgData[20:24]
    MsgNumAssocDevices=MsgData[24:26]
    MsgStartIndex=MsgData[26:28]
    MsgDeviceList=MsgData[28:len(MsgData)]

    Domoticz.Log("Decode8041 - IEEE Address response, Sequence number : " + MsgSequenceNumber + " Status : " 
                    + DisplayStatusCode( MsgDataStatus ) + " IEEE : " + MsgIEEE + " Short Address : " + MsgShortAddress 
                    + " number of associated devices : " + MsgNumAssocDevices + " Start Index : " + MsgStartIndex + " Device List : " + MsgDeviceList)


    if ( self.pluginconf.logFORMAT == 1 ) :
        Domoticz.Log("Zigate activity for | 8041 " +str(MsgShortAddress) + " | " + str(MsgIEEE) + " | " + str(int(MsgRSSI,16)) + " | " +str(MsgSequenceNumber) +" | ")

    if self.ListOfDevices[MsgShortAddress]['Status'] == "8041" :        # We have requested a IEEE address for a Short Address, 
                                                                        # hoping that we can reconnect to an existing Device
        if DeviceExist(self, Devices, MsgShortAddress, MsgIEEE ) == True :
            Domoticz.Log("Decode 8041 - Device details : " +str(self.ListOfDevices[MsgShortAddress]) )
        else :
            Domoticz.Error("Decode 8041 - Unknown device : " +str(MsgShortAddress) + " IEEE : " +str(MsgIEEE) )
    
    return

def Decode8042(self, MsgData) : # Node Descriptor response

    MsgLen=len(MsgData)
    Domoticz.Debug("Decode8042 - MsgData lenght is : " + str(MsgLen) + " out of 34")

    sequence=MsgData[0:2]
    status=MsgData[2:4]
    addr=MsgData[4:8]
    manufacturer=MsgData[8:12]
    max_rx=MsgData[12:16]
    max_tx=MsgData[16:20]
    server_mask=MsgData[20:24]
    descriptor_capability=MsgData[24:26]
    mac_capability=MsgData[26:28]
    max_buffer=MsgData[28:30]
    bit_field=MsgData[30:34]

    Domoticz.Debug("Decode8042 - Reception Node Descriptor for : " +addr + " SEQ : " + sequence + " Status : " + status +" manufacturer :" + manufacturer + " mac_capability : "+str(mac_capability) + " bit_field : " +str(bit_field) )

    if addr not in self.ListOfDevices:
        Domoticz.Log("Decode8042 receives a message from a non existing device %s" %saddr)
        return

    mac_capability = int(mac_capability,16)
    AltPAN      =   ( mac_capability & 0x00000001 )
    DeviceType  =   ( mac_capability >> 1 ) & 1
    PowerSource =   ( mac_capability >> 2 ) & 1
    ReceiveonIdle = ( mac_capability >> 3 ) & 1

    if DeviceType == 1 : 
        DeviceType = "FFD"
    else : 
        DeviceType = "RFD"
    if ReceiveonIdle == 1 : 
        ReceiveonIdle = "On"
    else : 
        ReceiveonIdle = "Off"
    if PowerSource == 1 :
        PowerSource = "Main"
    else :
        PowerSource = "Battery"

    Domoticz.Debug("Decode8042 - Alternate PAN Coordinator = " +str(AltPAN ))    # 1 if node is capable of becoming a PAN coordinator
    Domoticz.Debug("Decode8042 - Receiver on Idle = " +str(ReceiveonIdle))     # 1 if the device does not disable its receiver to 
                                                                            # conserve power during idle periods.
    Domoticz.Debug("Decode8042 - Power Source = " +str(PowerSource))            # 1 if the current power source is mains power. 
    Domoticz.Debug("Decode8042 - Device type  = " +str(DeviceType))            # 1 if this node is a full function device (FFD). 

    bit_fieldL   = int(bit_field[2:4],16)
    bit_fieldH   = int(bit_field[0:2],16)
    LogicalType =   bit_fieldL & 0x00F
    if   LogicalType == 0 : LogicalType = "Coordinator"
    elif LogicalType == 1 : LogicalType = "Router"
    elif LogicalType == 2 : LogicalType = "End Device"
    Domoticz.Debug("Decode8042 - bit_field = " +str(bit_fieldL) +" : "+str(bit_fieldH) )
    Domoticz.Debug("Decode8042 - Logical Type = " +str(LogicalType) )

    if self.ListOfDevices[addr]['Status'] != "inDB" :
        if self.pluginconf.allowStoreDiscoveryFrames and addr in self.DiscoveryDevices :
            self.DiscoveryDevices[addr]['Manufacturer'] = manufacturer
            self.DiscoveryDevices[addr]['8042'] = MsgData
            self.DiscoveryDevices[addr]['DeviceType'] = str(DeviceType)
            self.DiscoveryDevices[addr]['LogicalType'] = str(LogicalType)
            self.DiscoveryDevices[addr]['PowerSource'] = str(PowerSource)
            self.DiscoveryDevices[addr]['ReceiveOnIdle'] = str(ReceiveonIdle)

    self.ListOfDevices[addr]['Manufacturer']=manufacturer
    self.ListOfDevices[addr]['DeviceType']=str(DeviceType)
    self.ListOfDevices[addr]['LogicalType']=str(LogicalType)
    self.ListOfDevices[addr]['PowerSource']=str(PowerSource)
    self.ListOfDevices[addr]['ReceiveOnIdle']=str(ReceiveonIdle)

    return

def Decode8043(self, MsgData) : # Reception Simple descriptor response
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode8043 - MsgData lenght is : " + str(MsgLen) )

    MsgDataSQN=MsgData[0:2]
    MsgDataStatus=MsgData[2:4]
    MsgDataShAddr=MsgData[4:8]
    MsgDataLenght=MsgData[8:10]
    Domoticz.Debug("Decode8043 - Reception Simple descriptor response : SQN : " + MsgDataSQN + \
            ", Status : " + DisplayStatusCode( MsgDataStatus ) + ", short Addr : " + MsgDataShAddr + ", Lenght : " + MsgDataLenght)

    updSQN( self, MsgDataShAddr, MsgDataSQN)


    if int(MsgDataLenght,16) == 0 : return

    MsgDataEp=MsgData[10:12]
    MsgDataProfile=MsgData[12:16]
    MsgDataDeviceId=MsgData[16:20]
    MsgDataBField=MsgData[20:22]
    MsgDataInClusterCount=MsgData[22:24]

    if MsgDataShAddr not in self.ListOfDevices:
        Domoticz.Log("Decode8043 - receive message for non existing device")
        return

    if int(MsgDataProfile,16) == 0xC05E and int(MsgDataDeviceId,16) == 0xE15E:
        # ZLL Commissioning EndPoint / Jaiwel
        Domoticz.Log("Decode8043 - Received ProfileID: %s, ZDeviceID: %s - skip" %(MsgDataProfile, MsgDataDeviceId))
        if MsgDataEp in self.ListOfDevices[MsgDataShAddr]['Ep']:
            del self.ListOfDevices[MsgDataShAddr]['Ep'][MsgDataEp]
        if 'NbEp' in  self.ListOfDevices[MsgDataShAddr]:
            if self.ListOfDevices[MsgDataShAddr]['NbEp'] > '1':
                self.ListOfDevices[MsgDataShAddr]['NbEp'] = int( self.ListOfDevices[MsgDataShAddr]['NbEp']) - 1
        return

    Domoticz.Status("[%s] NEW OBJECT: %s Simple Descriptor EP %s" %('-', MsgDataShAddr, MsgDataEp))

    if 'ProfileID' in self.ListOfDevices[MsgDataShAddr]:
        if self.ListOfDevices[MsgDataShAddr]['ProfileID'] != MsgDataProfile:
            Domoticz.Log("Decode8043 - Overwrite ProfileID %s with %s from Ep: %s " \
                    %( self.ListOfDevices[MsgDataShAddr]['ProfileID'] , MsgDataProfile, MsgDataEp))
    self.ListOfDevices[MsgDataShAddr]['ProfileID'] = MsgDataProfile
    Domoticz.Status("[%s] NEW OBJECT: %s ProfileID %s" %('-', MsgDataShAddr, MsgDataProfile))

    if 'ZDeviceID' in self.ListOfDevices[MsgDataShAddr]:
        if self.ListOfDevices[MsgDataShAddr]['ZDeviceID'] != MsgDataDeviceId:
            Domoticz.Log("Decode8043 - Overwrite ZDeviceID %s with %s from Ep: %s " \
                    %( self.ListOfDevices[MsgDataShAddr]['ZDeviceID'] , MsgDataProfile, MsgDataEp))
    self.ListOfDevices[MsgDataShAddr]['ZDeviceID'] = MsgDataDeviceId
    Domoticz.Status("[%s] NEW OBJECT: %s ZDeviceID %s" %('-', MsgDataShAddr, MsgDataDeviceId))

    # Decoding Cluster IN
    Domoticz.Status("[%s] NEW OBJECT: %s Cluster IN Count: %s" %('-', MsgDataShAddr, MsgDataInClusterCount))
    idx = 24
    i=1
    if int(MsgDataInClusterCount,16)>0 :
        while i <= int(MsgDataInClusterCount,16) :
            MsgDataCluster=MsgData[idx+((i-1)*4):idx+(i*4)]
            if 'ConfigSource' in self.ListOfDevices[MsgDataShAddr]:
                if self.ListOfDevices[MsgDataShAddr]['ConfigSource'] != 'DeviceConf':
                    if MsgDataCluster not in self.ListOfDevices[MsgDataShAddr]['Ep'][MsgDataEp] :
                        self.ListOfDevices[MsgDataShAddr]['Ep'][MsgDataEp][MsgDataCluster]={}
                else:
                    Domoticz.Debug("[%s] NEW OBJECT: %s we keep DeviceConf info" %('-',MsgDataShAddr))
            else: # Not 'ConfigSource'
                self.ListOfDevices[MsgDataShAddr]['ConfigSource'] = '8043'
                if MsgDataCluster not in self.ListOfDevices[MsgDataShAddr]['Ep'][MsgDataEp] :
                    self.ListOfDevices[MsgDataShAddr]['Ep'][MsgDataEp][MsgDataCluster]={}

            Domoticz.Status("[%s] NEW OBJECT: %s Cluster In %s: %s" %('-', MsgDataShAddr, i, MsgDataCluster))
            MsgDataCluster=""
            i=i+1

    # Decoding Cluster Out
    idx = 24 + int(MsgDataInClusterCount,16) *4
    MsgDataOutClusterCount=MsgData[idx:idx+2]

    Domoticz.Status("[%s] NEW OBJECT: %s Cluster OUT Count: %s" %('-', MsgDataShAddr, MsgDataOutClusterCount))
    idx += 2
    i=1
    if int(MsgDataOutClusterCount,16)>0 :
        while i <= int(MsgDataOutClusterCount,16) :
            MsgDataCluster=MsgData[idx+((i-1)*4):idx+(i*4)]
            if 'ConfigSource' in self.ListOfDevices[MsgDataShAddr]:
                if self.ListOfDevices[MsgDataShAddr]['ConfigSource'] != 'DeviceConf':
                    if MsgDataCluster not in self.ListOfDevices[MsgDataShAddr]['Ep'][MsgDataEp] :
                        self.ListOfDevices[MsgDataShAddr]['Ep'][MsgDataEp][MsgDataCluster]={}
                else:
                    Domoticz.Log("[%s] NEW OBJECT: %s we keep DeviceConf info" %('-',MsgDataShAddr))
            else: # Not 'ConfigSource'
                self.ListOfDevices[MsgDataShAddr]['ConfigSource'] = '8043'
                if MsgDataCluster not in self.ListOfDevices[MsgDataShAddr]['Ep'][MsgDataEp] :
                    self.ListOfDevices[MsgDataShAddr]['Ep'][MsgDataEp][MsgDataCluster]={}

            Domoticz.Status("[%s] NEW OBJECT: %s Cluster Out %s: %s" %('-', MsgDataShAddr, i, MsgDataCluster))
            MsgDataCluster=""
            i=i+1

    if self.pluginconf.allowStoreDiscoveryFrames and MsgDataShAddr in self.DiscoveryDevices :
        self.DiscoveryDevices[MsgDataShAddr]['ProfileID'][MsgDataProfile] = MsgDataEp
        self.DiscoveryDevices[MsgDataShAddr]['ZDeviceID'][MsgDataDeviceId] = MsgDataEp
        if self.DiscoveryDevices[MsgDataShAddr].get('8043') :
            self.DiscoveryDevices[MsgDataShAddr]['8043'][MsgDataEp] = str(MsgData)
            self.DiscoveryDevices[MsgDataShAddr]['Ep'] = dict( self.ListOfDevices[MsgDataShAddr]['Ep'] )
        else :
            self.DiscoveryDevices[MsgDataShAddr]['8043'] = {}
            self.DiscoveryDevices[MsgDataShAddr]['8043'][MsgDataEp] = str(MsgData)
            self.DiscoveryDevices[MsgDataShAddr]['Ep'] = dict( self.ListOfDevices[MsgDataShAddr]['Ep'] )
        
        if 'IEEE' in self.ListOfDevices[MsgDataShAddr]:
            _jsonFilename = self.pluginconf.pluginZData + "/DiscoveryDevice-" + str(self.ListOfDevices[MsgDataShAddr]['IEEE']) + ".json"
        else:
            _jsonFilename = self.pluginconf.pluginZData + "/DiscoveryDevice-" + str(MsgDataShAddr) + ".json"

        with open ( _jsonFilename, 'at') as json_file:
            json.dump(self.DiscoveryDevices[MsgDataShAddr],json_file, indent=4, sort_keys=True)

    if self.ListOfDevices[MsgDataShAddr]['Status'] != "inDB" :
        self.ListOfDevices[MsgDataShAddr]['Status'] = "8043"
        self.ListOfDevices[MsgDataShAddr]['Heartbeat'] = "0"
    else :
        updSQN( self, MsgDataShAddr, MsgDataSQN)

    Domoticz.Debug("Decode8043 - Processed " + MsgDataShAddr + " end results is : " + str(self.ListOfDevices[MsgDataShAddr]) )
    return

def Decode8044(self, MsgData): # Power Descriptior response
    MsgLen=len(MsgData)
    SQNum=MsgData[0:2]
    Status=MsgData[2:4]
    bit_fields=MsgData[4:8]

    # Not Short address, nor IEEE. Hard to relate to a device !

    power_mode = bit_fields[0]
    power_source = bit_fields[1]
    current_power_source = bit_fields[2]
    current_power_level = bit_fields[3]

    Domoticz.Debug("Decode8044 - SQNum = " +SQNum +" Status = " + Status + " Power mode = " + power_mode + " power_source = " + power_source + " current_power_source = " + current_power_source + " current_power_level = " + current_power_level )
    return

def Decode8045(self, Devices, MsgData) : # Reception Active endpoint response
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode8045 - MsgData lenght is : " + str(MsgLen) )

    MsgDataSQN=MsgData[0:2]
    MsgDataStatus=MsgData[2:4]
    MsgDataShAddr=MsgData[4:8]
    MsgDataEpCount=MsgData[8:10]

    MsgDataEPlist=MsgData[10:len(MsgData)]

    Domoticz.Debug("Decode8045 - Reception Active endpoint response : SQN : " + MsgDataSQN + ", Status " + DisplayStatusCode( MsgDataStatus ) + ", short Addr " + MsgDataShAddr + ", List " + MsgDataEpCount + ", Ep list " + MsgDataEPlist)

    OutEPlist=""
    
    if DeviceExist(self, Devices, MsgDataShAddr) == False:
        #Pas sur de moi, mais si le device n'existe pas, je vois pas pkoi on continuerait
        Domoticz.Error("Decode8045 - KeyError : MsgDataShAddr = " + MsgDataShAddr)
        return
    else :
        if self.ListOfDevices[MsgDataShAddr]['Status']!="inDB" :
            self.ListOfDevices[MsgDataShAddr]['Status']="8045"
        else :
            updSQN( self, MsgDataShAddr, MsgDataSQN)
            
        i=0
        while i < 2 * int(MsgDataEpCount,16) :
            tmpEp = MsgDataEPlist[i:i+2]
            if not self.ListOfDevices[MsgDataShAddr]['Ep'].get(tmpEp) :
                self.ListOfDevices[MsgDataShAddr]['Ep'][tmpEp] = {}
            i = i + 2
        self.ListOfDevices[MsgDataShAddr]['NbEp'] =  str(int(MsgDataEpCount,16))     # Store the number of EPs

        for iterEp in self.ListOfDevices[MsgDataShAddr]['Ep']:
            Domoticz.Status("[%s] NEW OBJECT: %s Request Simple Descriptor for Ep: %s" %( '-', MsgDataShAddr, iterEp))
            sendZigateCmd(self,"0043", str(MsgDataShAddr)+str(iterEp))
        if self.ListOfDevices[MsgDataShAddr]['Status']!="inDB" :
            self.ListOfDevices[MsgDataShAddr]['Heartbeat'] = "0"
            self.ListOfDevices[MsgDataShAddr]['Status'] = "0043"

        Domoticz.Debug("Decode8045 - Device : " + str(MsgDataShAddr) + " updated ListofDevices with " + str(self.ListOfDevices[MsgDataShAddr]['Ep']) )

        if self.pluginconf.allowStoreDiscoveryFrames and MsgDataShAddr in self.DiscoveryDevices :
            self.DiscoveryDevices[MsgDataShAddr]['8045'] = str(MsgData)
            self.DiscoveryDevices[MsgDataShAddr]['NbEP'] = str(int(MsgDataEpCount,16))

    return

def Decode8046(self, MsgData) : # Match Descriptor response
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode8046 - MsgData lenght is : " + str(MsgLen) )

    MsgDataSQN=MsgData[0:2]
    MsgDataStatus=MsgData[2:4]
    MsgDataShAddr=MsgData[4:8]
    MsgDataLenList=MsgData[8:10]
    MsgDataMatchList=MsgData[10:len(MsgData)]

    updSQN( self, MsgDataShAddr, MsgDataSQN)
    Domoticz.Log("Decode8046 - Match Descriptor response : SQN : " + MsgDataSQN + ", Status " + DisplayStatusCode( MsgDataStatus ) + ", short Addr " + MsgDataShAddr + ", Lenght list  " + MsgDataLenList + ", Match list " + MsgDataMatchList)
    return

def Decode8047(self, MsgData) : # Management Leave response
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode8047 - MsgData lenght is : " + str(MsgLen) + " out of 2" )

    MsgSequenceNumber=MsgData[0:2]
    MsgDataStatus=MsgData[2:4]

    Domoticz.Status("Decode8047 - Leave response, SQN: %s Status: %s - %s" \
            %( MsgSequenceNumber, MsgDataStatus, DisplayStatusCode( MsgDataStatus )))

    return

def Decode8048(self, Devices, MsgData, MsgRSSI) : # Leave indication
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode8048 - MsgData lenght is : " + str(MsgLen) + " out of 2" )

    MsgExtAddress=MsgData[0:16]
    MsgDataStatus=MsgData[16:18]
    
    Domoticz.Status("Leave indication from IEEE: %s , Status: %s " %(MsgExtAddress, MsgDataStatus))
    devName = ''
    for x in Devices:
        if Devices[x].DeviceID == MsgExtAddress:
            devName = Devices[x].Name
            break
    self.adminWidgets.updateNotificationWidget( Devices, 'Leave indication from %s for %s ' %(MsgExtAddress, devName) )

    if ( self.pluginconf.logFORMAT == 1 ) :
        Domoticz.Log("Zigate activity for | 8048 |  | " + str(MsgExtAddress) + " | " + str(int(MsgRSSI,16)) + " |  | ")

    if MsgExtAddress not in self.IEEE2NWK: # Most likely this object has been removed and we are receiving the confirmation.
        return
    sAddr = getSaddrfromIEEE( self, MsgExtAddress )

    if sAddr == '' :
        Domoticz.Log("Decode8048 - device not found with IEEE = " +str(MsgExtAddress) )
    else :
        timeStamped(self, sAddr, 0x8048)
        Domoticz.Status("device " +str(sAddr) + " annouced to leave" )
        if self.ListOfDevices[sAddr]['Status'] == 'inDB':
            self.ListOfDevices[sAddr]['Status'] = 'Left'
            self.ListOfDevices[sAddr]['Hearbeat'] = 0
            Domoticz.Status("Calling leaveMgt to request a rejoin of %s/%s " %( sAddr, MsgExtAddress))
            leaveMgtReJoin( self, sAddr, MsgExtAddress )

    return

def Decode804A(self, Devices, MsgData) : # Management Network Update response
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode804A - MsgData lenght is : " + str(MsgLen) + " out of 2" )

    MsgSequenceNumber=MsgData[0:2]
    MsgDataStatus=MsgData[2:4]
    MsgTotalTransmission=MsgData[4:8]
    MsgTransmissionFailures=MsgData[8:12]
    MsgScannedChannel=MsgData[12:20]
    MsgScannedChannelListCount=MsgData[20:22]
    MsgChannelListInterference=MsgData[22:len(MsgData)]

    #Decode the Channel mask received
    CHANNELS = { 11: 0x00000800,
            12: 0x00001000,
            13: 0x00002000,
            14: 0x00004000,
            15: 0x00008000,
            16: 0x00010000,
            17: 0x00020000,
            18: 0x00040000,
            19: 0x00080000,
            20: 0x00100000,
            21: 0x00200000,
            22: 0x00400000,
            23: 0x00800000,
            24: 0x01000000,
            25: 0x02000000,
            26: 0x04000000 }

    nwkscan = {}
    channelList = []
    for channel in CHANNELS:
        if int(MsgScannedChannel,16) & CHANNELS[channel]:
            channelList.append( channel )

    channelListInterferences = []
    idx = 0
    while idx < len(MsgChannelListInterference):
        channelListInterferences.append( "%X" %(int(MsgChannelListInterference[idx:idx+2],16)))
        idx += 2

    Domoticz.Status("Management Network Update. SQN: %s, Total Transmit: %s , Transmit Failures: %s , Status: %s) " \
            %(MsgSequenceNumber, int(MsgTotalTransmission,16), int(MsgTransmissionFailures,16), DisplayStatusCode(MsgDataStatus)) )

    timing = int(time.time())
    nwkscan[timing] = {}
    nwkscan[timing]['Total Tx'] = int(MsgTotalTransmission,16)
    nwkscan[timing]['Total failures'] = int(MsgTransmissionFailures,16)
    for chan, inter in zip( channelList, channelListInterferences ):
        nwkscan[timing][chan] = int(inter,16)
        Domoticz.Status("     Channel: %s Interference: : %s " %(chan, int(inter,16)))

    # Write the report onto file
    _filename =  self.pluginconf.pluginReports + 'Network_scan-' + '%02d' %self.HardwareID + '.txt'
    #Domoticz.Status("Network Scan report save on " +str(_filename))
    #with open(_filename , 'at') as file:
    #    for key in nwkscan:
    #        file.write(str(key) + ": " + str(nwkscan[key]) + "\n")

    _filename =  self.pluginconf.pluginReports + 'Network_scan-' + '%02d' %self.HardwareID 
    json_filename = _filename + ".json"
    with open( json_filename , 'at') as json_file:
        json_file.write('\n')
        json.dump( nwkscan, json_file)

    self.adminWidgets.updateNotificationWidget( Devices, 'A new Network Scan report is available' )

    return

def Decode804B(self, MsgData) : # System Server Discovery response
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode804B - MsgData lenght is : " + str(MsgLen) + " out of 2" )

    MsgSequenceNumber=MsgData[0:2]
    MsgDataStatus=MsgData[2:4]
    MsgServerMask=MsgData[4:8]
    
    Domoticz.Log("ZigateRead - MsgType 804B - System Server Discovery response, Sequence number : " + MsgSequenceNumber + " Status : " + DisplayStatusCode( MsgDataStatus ) + " Server Mask : " + MsgServerMask)
    return

#Group response
# Implemented in z_GrpMgt.py

#Reponses SCENE
def Decode80A0(self, MsgData) : # View Scene response

    MsgLen=len(MsgData)
    Domoticz.Debug("Decode80A0 - MsgData lenght is : " + str(MsgLen) + " out of 24" )

    MsgSequenceNumber=MsgData[0:2]
    MsgEP=MsgData[2:4]
    MsgClusterID=MsgData[4:8]
    MsgDataStatus=MsgData[8:10]
    MsgGroupID=MsgData[10:14]
    MsgSceneID=MsgData[14:16]
    MsgSceneTransitonTime=MsgData[16:20]
    MSgSceneNameLength=MsgData[20:22]
    MSgSceneNameLengthMax=MsgData[22:24]
    #<scene name data: data each element is uint8_t>
    #<extensions length: uint16_t>
    #<extensions max length: uint16_t>
    #<extensions data: data each element is uint8_t>
    
    Domoticz.Log("ZigateRead - MsgType 80A0 - View Scene response, Sequence number : " + MsgSequenceNumber + " EndPoint : " + MsgEP + " ClusterID : " + MsgClusterID + " Status : " + DisplayStatusCode( MsgDataStatus ) + " Group ID : " + MsgGroupID)
    return

def Decode80A1(self, MsgData) : # Add Scene response
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode80A1 - MsgData lenght is : " + str(MsgLen) + " out of 2" )

    MsgSequenceNumber=MsgData[0:2]
    MsgEP=MsgData[2:4]
    MsgClusterID=MsgData[4:8]
    MsgDataStatus=MsgData[8:10]
    MsgGroupID=MsgData[10:14]
    MsgSceneID=MsgData[14:16]
    
    Domoticz.Log("ZigateRead - MsgType 80A1 - Add Scene response, Sequence number : " + MsgSequenceNumber + " EndPoint : " + MsgEP + " ClusterID : " + MsgClusterID + " Status : " + DisplayStatusCode( MsgDataStatus ) + " Group ID : " + MsgGroupID + " Scene ID : " + MsgSceneID)
    return

def Decode80A2(self, MsgData) : # Remove Scene response
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode80A2 - MsgData lenght is : " + str(MsgLen) + " out of 2" )

    MsgSequenceNumber=MsgData[0:2]
    MsgEP=MsgData[2:4]
    MsgClusterID=MsgData[4:8]
    MsgDataStatus=MsgData[8:10]
    MsgGroupID=MsgData[10:14]
    MsgSceneID=MsgData[14:16]
    
    Domoticz.Log("ZigateRead - MsgType 80A2 - Remove Scene response, Sequence number : " + MsgSequenceNumber + " EndPoint : " + MsgEP + " ClusterID : " + MsgClusterID + " Status : " + DisplayStatusCode( MsgDataStatus ) + " Group ID : " + MsgGroupID + " Scene ID : " + MsgSceneID)
    return

def Decode80A3(self, MsgData) : # Remove All Scene response
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode80A3 - MsgData lenght is : " + str(MsgLen) + " out of 2" )

    MsgSequenceNumber=MsgData[0:2]
    MsgEP=MsgData[2:4]
    MsgClusterID=MsgData[4:8]
    MsgDataStatus=MsgData[8:10]
    MsgGroupID=MsgData[10:14]
    
    Domoticz.Log("ZigateRead - MsgType 80A3 - Remove All Scene response, Sequence number : " + MsgSequenceNumber + " EndPoint : " + MsgEP + " ClusterID : " + MsgClusterID + " Status : " + DisplayStatusCode( MsgDataStatus ) + " Group ID : " + MsgGroupID)
    return

def Decode80A4(self, MsgData) : # Store Scene response
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode80A4 - MsgData lenght is : " + str(MsgLen) + " out of 2" )

    MsgSequenceNumber=MsgData[0:2]
    MsgEP=MsgData[2:4]
    MsgClusterID=MsgData[4:8]
    MsgDataStatus=MsgData[8:10]
    MsgGroupID=MsgData[10:14]
    MsgSceneID=MsgData[14:16]
    
    Domoticz.Log("ZigateRead - MsgType 80A4 - Store Scene response, Sequence number : " + MsgSequenceNumber + " EndPoint : " + MsgEP + " ClusterID : " + MsgClusterID + " Status : " + DisplayStatusCode( MsgDataStatus ) + " Group ID : " + MsgGroupID + " Scene ID : " + MsgSceneID)
    return
    
def Decode80A6(self, MsgData) : # Scene Membership response
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode80A6 - MsgData lenght is : " + str(MsgLen) + " out of 2" )

    MsgSequenceNumber=MsgData[0:2]
    MsgEP=MsgData[2:4]
    MsgClusterID=MsgData[4:8]
    MsgDataStatus=MsgData[8:10]
    MsgCapacity=MsgData[10:12]
    MsgGroupID=MsgData[12:16]
    MsgSceneCount=MsgData[16:18]
    MsgSceneList=MsgData[18:len(MsgData)]
    
    Domoticz.Log("ZigateRead - MsgType 80A6 - Scene Membership response, Sequence number : " + MsgSequenceNumber + " EndPoint : " + MsgEP + " ClusterID : " + MsgClusterID + " Status : " + DisplayStatusCode( MsgDataStatus ) + " Group ID : " + MsgGroupID + " Scene ID : " + MsgSceneID)
    return

#Reponses Attributs
def Decode8100(self, Devices, MsgData, MsgRSSI) :  # Report Individual Attribute response
    MsgSQN=MsgData[0:2]
    MsgSrcAddr=MsgData[2:6]
    MsgSrcEp=MsgData[6:8]
    MsgClusterId=MsgData[8:12]
    MsgAttrID = MsgData[12:16]
    MsgAttrStatus = MsgData[16:18]
    MsgAttType=MsgData[18:20]
    MsgAttSize=MsgData[20:24]
    MsgClusterData=MsgData[24:len(MsgData)]

    Domoticz.Debug("Decode8100 - Report Individual Attribute : [%s:%s] ClusterID: %s AttributeID: %s Status: %s Type: %s Size: %s ClusterData: >%s<" \
            %(MsgSrcAddr, MsgSrcEp, MsgClusterId, MsgAttrID, MsgAttStatus, MsgAttType, MsgAttSize, MsgClusterData ))

    timeStamped( self, MsgSrcAddr , 0x8100)
    if ( self.pluginconf.logFORMAT == 1 ) :
        Domoticz.Log("Zigate activity for | 8100 | " +str(MsgSrcAddr) +" |  | " + str(int(MsgRSSI,16)) + " | " +str(MsgSQN) + "  | ")
    try :
        self.ListOfDevices[MsgSrcAddr]['RSSI']= int(MsgRSSI,16)
    except : 
        self.ListOfDevices[MsgSrcAddr]['RSSI']= 0

    lastSeenUpdate( self, Devices, NwkId=MsgSrcAddr)
    updSQN( self, MsgSrcAddr, MsgSQN)
    ReadCluster(self, Devices, MsgData) 

    return

def Decode8101(self, MsgData) :  # Default Response
    MsgDataSQN=MsgData[0:2]
    MsgDataEp=MsgData[2:4]
    MsgClusterId=MsgData[4:8]
    MsgDataCommand=MsgData[8:10]
    MsgDataStatus=MsgData[10:12]
    Domoticz.Debug("Decode8101 - Default response - SQN: %s, EP: %s, ClusterID: %s , DataCommand: %s, - Status: [%s] %s" \
            %(MsgDataSQN, MsgDataEp, MsgClusterId, MsgDataCommand, MsgDataStatus,  DisplayStatusCode( MsgDataStatus ) ))
    return

def Decode8102(self, Devices, MsgData, MsgRSSI) :  # Report Individual Attribute response
    MsgSQN=MsgData[0:2]
    MsgSrcAddr=MsgData[2:6]
    MsgSrcEp=MsgData[6:8]
    MsgClusterId=MsgData[8:12]
    MsgAttrID=MsgData[12:16]
    MsgAttStatus=MsgData[16:18]
    MsgAttType=MsgData[18:20]
    MsgAttSize=MsgData[20:24]
    MsgClusterData=MsgData[24:len(MsgData)]

    Domoticz.Debug("Decode8102 - Individual Attribute response : [%s:%s] ClusterID: %s AttributeID: %s Status: %s Type: %s Size: %s ClusterData: >%s<" \
            %(MsgSrcAddr, MsgSrcEp, MsgClusterId, MsgAttrID, MsgAttStatus, MsgAttType, MsgAttSize, MsgClusterData ))

    if ( self.pluginconf.logFORMAT == 1 ) :
        if 'IEEE' in self.ListOfDevices[MsgSrcAddr]:
            Domoticz.Log("Zigate activity for | 8102 | " +str(MsgSrcAddr) +" | " +str(self.ListOfDevices[MsgSrcAddr]['IEEE']) +" | " + str(int(MsgRSSI,16)) + " | " +str(MsgSQN) + "  | ")
        else:
            Domoticz.Log("Zigate activity for | 8102 | " +str(MsgSrcAddr) +" | - | " + str(int(MsgRSSI,16)) + " | " +str(MsgSQN) + "  | ")

    if DeviceExist(self, Devices, MsgSrcAddr) == True :
        try:
            self.ListOfDevices[MsgSrcAddr]['RSSI']= int(MsgRSSI,16)
        except:
            self.ListOfDevices[MsgSrcAddr]['RSSI']= 0

        Domoticz.Debug("Decode8102 : Attribute Report from " + str(MsgSrcAddr) + " SQN = " + str(MsgSQN) + " ClusterID = " 
                        + str(MsgClusterId) + " AttrID = " +str(MsgAttrID) + " Attribute Data = " + str(MsgClusterData) )

        lastSeenUpdate( self, Devices, NwkId=MsgSrcAddr)
        timeStamped( self, MsgSrcAddr , 0x8102)
        updSQN( self, MsgSrcAddr, str(MsgSQN) )
        ReadCluster(self, Devices, MsgData) 
    else :
        # This device is unknown, and we don't have the IEEE to check if there is a device coming with a new sAddr
        # Will request in the next hearbeat to for a IEEE request
        Domoticz.Error("Decode8102 - Receiving a message from unknown device : " + str(MsgSrcAddr) + " with Data : " +str(MsgData) )
        #Domoticz.Status("Decode8102 - Will try to reconnect device : " + str(MsgSrcAddr) )
        #Domoticz.Status("Decode8102 - but will most likely fail if it is battery powered device.")
        #initDeviceInList(self, MsgSrcAddr)
        #self.ListOfDevices[MsgSrcAddr]['Status']="0041"
        #self.ListOfDevices[MsgSrcAddr]['MacCapa']= "0"
    return

def Decode8110(self, Devices, MsgData) :  # Write Attribute response
    MsgSQN=MsgData[0:2]
    MsgSrcAddr=MsgData[2:6]
    MsgSrcEp=MsgData[6:8]
    MsgClusterId=MsgData[8:12]
    MsgAttrID=MsgData[12:16]
    MsgAttType=MsgData[16:18]
    MsgAttSize=MsgData[18:22]
    MsgClusterData=MsgData[22:len(MsgData)]

    Domoticz.Debug("Decode8110 - WriteAttributeResponse - MsgSQN: %s, MsgSrcAddr: %s, MsgSrcEp: %s, MsgClusterId: %s, MsgAttrID: %s, MsgAttType: %s, MsgAttSize: %s, MsgClusterData: %s" \
            %( MsgSQN, MsgSrcAddr, MsgSrcEp, MsgClusterId, MsgAttrID, MsgAttType, MsgAttSize, MsgClusterData))

    timeStamped( self, MsgSrcAddr , 0x8110)
    updSQN( self, MsgSrcAddr, MsgSQN)

    if MsgClusterId == "0500":
        self.iaszonemgt.receiveIASmessages( MsgSrcAddr, 3, MsgClusterData)

    return

def Decode8120(self, MsgData) :  # Configure Reporting response

    Domoticz.Debug("Decode8120 - Configure reporting response : %s" %MsgData)
    if len(MsgData) < 14:
        Domoticz.Error("Decode8120 - uncomplet message %s " %MsgData)
        return

    MsgSQN=MsgData[0:2]
    MsgSrcAddr=MsgData[2:6]
    MsgSrcEp=MsgData[6:8]
    MsgClusterId=MsgData[8:12]
    RemainData = MsgData[12:len(MsgData)]

    Domoticz.Debug("Decode8120 - SQN: %s, SrcAddr: %s, SrcEP: %s, ClusterID: %s, RemainData: %s" %(MsgSQN, MsgSrcAddr, MsgSrcEp, MsgClusterId, RemainData))


    if MsgSrcAddr not in self.ListOfDevices:
        Domoticz.Error("Decode8120 - receiving Configure reporting response from unknow  %s" %MsgSrcAddr)
        return


    elif len(MsgData) == 14: # Firmware < 3.0f
        MsgDataStatus=MsgData[12:14]
    else:
        MsgAttribute = []
        nbattribute = int(( len(MsgData) - 14 ) // 4)
        idx = 0
        while idx < nbattribute :
            MsgAttribute.append( MsgData[(12+(idx*4)):(12+(idx*4))+4] )
            idx += 1
        Domoticz.Debug("nbAttribute: %s, idx: %s" %(nbattribute, idx))
        MsgDataStatus = MsgData[(12+(nbattribute*4)):(12+(nbattribute*4)+2)]
        Domoticz.Debug("Decode8120 - Attributes : %s status: %s " %(str(MsgAttribute), MsgDataStatus))

    Domoticz.Debug("Decode8120 - Configure Reporting response - ClusterID: %s, MsgSrcAddr: %s, MsgSrcEp:%s , Status: %s - %s" \
       %(MsgClusterId, MsgSrcAddr, MsgSrcEp, MsgDataStatus, DisplayStatusCode( MsgDataStatus) ))

    timeStamped( self, MsgSrcAddr , 0x8120)
    updSQN( self, MsgSrcAddr, MsgSQN)

    if 'ConfigureReporting' in self.ListOfDevices[MsgSrcAddr]:
        if 'Ep' in self.ListOfDevices[MsgSrcAddr]['ConfigureReporting']:
            if MsgSrcEp in self.ListOfDevices[MsgSrcAddr]['ConfigureReporting']['Ep']:
                if str(MsgClusterId) not in self.ListOfDevices[MsgSrcAddr]['ConfigureReporting']['Ep'][MsgSrcEp]:
                    self.ListOfDevices[MsgSrcAddr]['ConfigureReporting']['Ep'][MsgSrcEp][str(MsgClusterId)] = {}
            else:
                self.ListOfDevices[MsgSrcAddr]['ConfigureReporting']['Ep'][MsgSrcEp] = {}
                self.ListOfDevices[MsgSrcAddr]['ConfigureReporting']['Ep'][MsgSrcEp][str(MsgClusterId)] = {}
        else:
            self.ListOfDevices[MsgSrcAddr]['ConfigureReporting']['Ep'] = {}
            self.ListOfDevices[MsgSrcAddr]['ConfigureReporting']['Ep'][MsgSrcEp] = {}
            self.ListOfDevices[MsgSrcAddr]['ConfigureReporting']['Ep'][MsgSrcEp][str(MsgClusterId)] = {}
    else:
        self.ListOfDevices[MsgSrcAddr]['ConfigureReporting'] = {}
        self.ListOfDevices[MsgSrcAddr]['ConfigureReporting']['Ep'] = {}
        self.ListOfDevices[MsgSrcAddr]['ConfigureReporting']['Ep'][MsgSrcEp] = {}
        self.ListOfDevices[MsgSrcAddr]['ConfigureReporting']['Ep'][MsgSrcEp][str(MsgClusterId)] = {}

    self.ListOfDevices[MsgSrcAddr]['ConfigureReporting']['Ep'][MsgSrcEp][MsgClusterId] = MsgDataStatus

    if MsgDataStatus != '00':
        # Looks like that this Device doesn't handle Configure Reporting, so let's flag it as such, so we won't do it anymore
        Domoticz.Debug("Decode8120 - Configure Reporting response - ClusterID: %s, MsgSrcAddr: %s, MsgSrcEp:%s , Status: %s - %s" \
            %(MsgClusterId, MsgSrcAddr, MsgSrcEp, MsgDataStatus, DisplayStatusCode( MsgDataStatus) ))
    return

def Decode8140(self, MsgData) :  # Attribute Discovery response
    MsgComplete=MsgData[0:2]
    MsgAttType=MsgData[2:4]
    MsgAttID=MsgData[4:8]
    
    if len(MsgData) > 8:
        MsgSrcAddr = MsgData[8:12]
        MsgSrcEp = MsgData[12:14]
        MsgClusterID = MsgData[14:18]

        Domoticz.Debug("Decode8140 - Attribute Discovery Response - %s/%s - Cluster: %s - Attribute: %s - Attribute Type: %s"
            %( MsgSrcAddr, MsgSrcEp, MsgClusterID, MsgAttID, MsgAttType))

        if 'Attributes List' not in  self.ListOfDevices[MsgSrcAddr]:
            self.ListOfDevices[MsgSrcAddr]['Attributes List'] = {}
            self.ListOfDevices[MsgSrcAddr]['Attributes List']['Ep'] = {}
        if MsgSrcEp not in self.ListOfDevices[MsgSrcAddr]['Attributes List']['Ep']:
            self.ListOfDevices[MsgSrcAddr]['Attributes List']['Ep'][MsgSrcEp] = {}
        if MsgClusterID not in  self.ListOfDevices[MsgSrcAddr]['Attributes List']['Ep'][MsgSrcEp]:
            self.ListOfDevices[MsgSrcAddr]['Attributes List']['Ep'][MsgSrcEp][MsgClusterID] = {}
        if MsgAttID not in self.ListOfDevices[MsgSrcAddr]['Attributes List']['Ep'][MsgSrcEp][MsgClusterID]:
            self.ListOfDevices[MsgSrcAddr]['Attributes List']['Ep'][MsgSrcEp][MsgClusterID][MsgAttID] = MsgAttType

        if self.pluginconf.allowStoreDiscoveryFrames and MsgSrcAddr in self.DiscoveryDevices :
            if 'Attribute Discovery' not in  self.DiscoveryDevices[MsgSrcAddr]:
                self.DiscoveryDevices[MsgSrcAddr]['Attribute Discovery'] = {}
                self.DiscoveryDevices[MsgSrcAddr]['Attribute Discovery']['Ep'] = {}
            if MsgSrcEp not in  self.DiscoveryDevices[MsgSrcAddr]['Attribute Discovery']['Ep']:
                self.DiscoveryDevices[MsgSrcAddr]['Attribute Discovery']['Ep'][MsgSrcEp] = {}
            if MsgClusterID not in self.DiscoveryDevices[MsgSrcAddr]['Attribute Discovery']['Ep'][MsgSrcEp]:
                self.DiscoveryDevices[MsgSrcAddr]['Attribute Discovery']['Ep'][MsgSrcEp][MsgClusterID] = {}
            if MsgAttID not in self.DiscoveryDevices[MsgSrcAddr]['Attribute Discovery']['Ep'][MsgSrcEp][MsgClusterID]:
                self.DiscoveryDevices[MsgSrcAddr]['Attribute Discovery']['Ep'][MsgSrcEp][MsgClusterID] = {}
                self.DiscoveryDevices[MsgSrcAddr]['Attribute Discovery']['Ep'][MsgSrcEp][MsgClusterID][MsgAttID] = MsgAttType

            if 'IEEE' in self.ListOfDevices[MsgSrcAddr]:
                _jsonFilename = self.pluginconf.pluginZData + "/DiscoveryDevice-" + str(self.ListOfDevices[MsgSrcAddr]['IEEE']) + ".json"
            else:
                _jsonFilename = self.pluginconf.pluginZData + "/DiscoveryDevice-" + str(MsgSrcAddr) + ".json"
            with open ( _jsonFilename, 'at') as json_file:
                json.dump(self.DiscoveryDevices[MsgSrcAddr],json_file, indent=4, sort_keys=True)

    return

# OTA and Remote decoding kindly authorized by https://github.com/ISO-B
def Decode8501(self, Devices, MsgData, MsgRSSI) : # OTA image block request

    MsgSQN = MsgData[0:2]
    MsgEP = MsgData[2:4]
    MsgClusterId = MsgData[4:8]
    MsgaddrMode = MsgData[8:10]
    MsgIEEE = MsgData[10:26]
    MsgSrcAddr = MsgData[26:30]
    MsgFileOffset = MsgData[30:34]
    MsgImageVersion = MsgData[34:38]
    MsgImageType = MsgData[38:42]
    MsgManufCode = MsgData[42:46]
    MsgBlockRequestDelay = MsgData[46:50]
    MsgMaxDataSize = MsgData[50:52]
    MsgFieldControl = MsgData[52:54]

    Domoticz.Log("Decode8501 - OTA image Block request - %s/%s %s Offset: %s version: %s Type: %s Code: %s Delay: %s MaxSize: %s Control: %s"
            %(MsgSrcAddr, MsgEP, MsgClusterId, MsgFileOffset, MsgImageVersion, MsgImageType, MsgManufCode, MsgBlockRequestDelay, MsgMaxDataSize, MsgFieldControl))


    return

def Decode8503(self, Devices, MsgData, MsgRSSI) : # OTA image block request
    'OTA upgrade request'

    MsgSQN = MsgData[0:2]
    MsgEP = MsgData[2:4]
    MsgClusterId = MsgData[4:8]
    MsgSrcAddr = MsgData[8:12]
    MsgImageVersion = MsgData[12:16]
    MsgImageType = MsgData[16:20]
    MsgManufCode = MsgData[20:24]
    MsgStatus = MsgData[24:26]

    Domoticz.Log("Decode8503 - OTA upgrade request - %s/%s %s Version: %s Type: %s Code: %s Status: %s"
            %(MsgSrcAddr, MsgEP, MsgClusterId, MsgImageVersion, MsgImageType, MsgManufCode, MsgStatus))

#Router Discover
def Decode8701(self, MsgData) : # Reception Router Disovery Confirm Status
    MsgLen=len(MsgData)
    Domoticz.Debug("Decode8701 - MsgLen = " + str(MsgLen))

    if MsgLen==0 :
        return
    else:
        # This is the reverse of what is documented. Suspecting that we got a BigEndian uint16 instead of 2 uint8
        Status=MsgData[2:4]
        NwkStatus=MsgData[0:2]
    
    Domoticz.Debug("Decode8701 - Route discovery has been performed, status: %s Nwk Status: %s " \
            %( Status, NwkStatus))

    if NwkStatus != "00" :
        Domoticz.Debug("Decode8701 - Route discovery has been performed, status: %s - %s Nwk Status: %s - %s " \
                %( Status, DisplayStatusCode( Status ), NwkStatus, DisplayStatusCode(NwkStatus)))

    return

#Réponses APS
def Decode8702(self, MsgData) : # Reception APS Data confirm fail

    MsgLen=len(MsgData)
    if MsgLen==0: 
        return

    MsgDataStatus=MsgData[0:2]
    MsgDataSrcEp=MsgData[2:4]
    MsgDataDestEp=MsgData[4:6]
    MsgDataDestMode=MsgData[6:8]

    if self.FirmwareVersion.lower() <= '030f':
        MsgDataDestAddr=MsgData[8:24]
        MsgDataSQN=MsgData[24:26]
    else:    # Fixed by https://github.com/fairecasoimeme/ZiGate/issues/161
        if int(MsgDataDestMode,16) == ADDRESS_MODE['short']:
            MsgDataDestAddr=MsgData[8:12]
            MsgDataSQN=MsgData[12:14]
        elif int(MsgDataDestMode,16) == ADDRESS_MODE['group']:
            MsgDataDestAddr=MsgData[8:12]
            MsgDataSQN=MsgData[12:14]
        elif int(MsgDataDestMode,16) == ADDRESS_MODE['ieee']:
            MsgDataDestAddr=MsgData[8:24]
            MsgDataSQN=MsgData[24:26]
        else:
            Domoticz.Error("Decode8702 - Unexpected addmode %s for data %s" %(MsgDataDestMode, MsgData))
            return

    timeStamped( self, MsgDataDestAddr , 0x8702)
    updSQN( self, MsgDataDestAddr, MsgDataSQN)
    if self.pluginconf.enableAPSFailureLoging:
        Domoticz.Log("Decode8702 - SQN: %s AddrMode: %s DestAddr: %s SrcEP: %s DestEP: %s Status: %s - %s" \
            %( MsgDataSQN, MsgDataDestMode, MsgDataDestAddr, MsgDataSrcEp, MsgDataDestEp, MsgDataStatus, DisplayStatusCode( MsgDataStatus )))
    return

#Device Announce
def Decode004d(self, Devices, MsgData, MsgRSSI) : # Reception Device announce
    MsgSrcAddr=MsgData[0:4]
    MsgIEEE=MsgData[4:20]
    MsgMacCapa=MsgData[20:22]

    if MsgSrcAddr in self.ListOfDevices:
        if self.ListOfDevices[MsgSrcAddr]['Status'] in ( '004d', '0045', '0043', '8045', '8043'):
            # Let's skip it has this is a duplicate message from the device
            return

    Domoticz.Status("Device Annoucement ShortAddr: %s, IEEE: %s " %( MsgSrcAddr, MsgIEEE))

    if ( self.pluginconf.logFORMAT == 1 ) :
        Domoticz.Log("Zigate activity for | 004d | " +str(MsgSrcAddr) +" | " + str(MsgIEEE) + " | " + str(int(MsgRSSI,16)) + " |  | ")

    # Test if Device Exist, if Left then we can reconnect, otherwise initialize the ListOfDevice for this entry
    if not DeviceExist(self, Devices, MsgSrcAddr, MsgIEEE):
        if MsgIEEE in self.IEEE2NWK :
            if self.IEEE2NWK[MsgIEEE] :
                Domoticz.Log("Decode004d - self.IEEE2NWK[MsgIEEE] = " +str(self.IEEE2NWK[MsgIEEE]) )
        self.IEEE2NWK[MsgIEEE] = MsgSrcAddr
        if not IEEEExist( self, MsgIEEE ):
            initDeviceInList(self, MsgSrcAddr)
            Domoticz.Debug("Decode004d - Looks like it is a new device sent by Zigate")
            self.CommiSSionning = True
            self.ListOfDevices[MsgSrcAddr]['MacCapa'] = MsgMacCapa
            self.ListOfDevices[MsgSrcAddr]['IEEE'] = MsgIEEE
        else:
            # we are getting a Dupplicate. Most-likely the Device is existing and we have to reconnect.
            if not DeviceExist(self, Devices, MsgSrcAddr,MsgIEEE):
                Domoticz.Log("Decode004d - Paranoia .... NwkID: %s, IEEE: % -> %s " %(MsgSrcAddr, MsgIEEE, str(self.ListOfDevices[MsgSrcAddr])))
        # We will request immediatly the List of EndPoints
        self.ListOfDevices[MsgSrcAddr]['Heartbeat'] = "0"
        self.ListOfDevices[MsgSrcAddr]['Status'] = "0045"
        sendZigateCmd(self,"0045", str(MsgSrcAddr))             # Request list of EPs

        Domoticz.Debug("Decode004d - " + str(MsgSrcAddr) + " Info: " +str(self.ListOfDevices[MsgSrcAddr]) )

    else:
        # Device exist
        # We will also reset ReadAttributes
        if self.pluginconf.allowReBindingClusters:
            Domoticz.Log("Decode004d - rebind clusters for %s" %MsgSrcAddr)
            rebind_Clusters( self, MsgSrcAddr)

            if 'ReadAttributes' in self.ListOfDevices[MsgSrcAddr]:
                del self.ListOfDevices[MsgSrcAddr]['ReadAttributes']
    
            if 'ConfigureReporting' in self.ListOfDevices[MsgSrcAddr]:
                del self.ListOfDevices[MsgSrcAddr]['ConfigureReporting']
                self.ListOfDevices[MsgSrcAddr]['Hearbeat'] = 0

    timeStamped( self, MsgSrcAddr , 0x004d)

    if self.pluginconf.allowStoreDiscoveryFrames:
        self.DiscoveryDevices[MsgSrcAddr] = {}
        self.DiscoveryDevices[MsgSrcAddr]['004d']={}
        self.DiscoveryDevices[MsgSrcAddr]['8043']={}
        self.DiscoveryDevices[MsgSrcAddr]['8045']={}
        self.DiscoveryDevices[MsgSrcAddr]['Ep']={}
        self.DiscoveryDevices[MsgSrcAddr]['MacCapa']={}
        self.DiscoveryDevices[MsgSrcAddr]['IEEE']={}
        self.DiscoveryDevices[MsgSrcAddr]['ProfileID']={}
        self.DiscoveryDevices[MsgSrcAddr]['ZDeviceID']={}
        self.DiscoveryDevices[MsgSrcAddr]['004d'] = str(MsgData)
        self.DiscoveryDevices[MsgSrcAddr]['IEEE'] = str(MsgIEEE)
        self.DiscoveryDevices[MsgSrcAddr]['MacCapa'] = str(MsgMacCapa)
    
    return

def Decode8085(self, Devices, MsgData, MsgRSSI) :
    'Remote button pressed'

    MsgSQN = MsgData[0:2]
    MsgEP = MsgData[2:4]
    MsgClusterId = MsgData[4:8]
    unknown_ = MsgData[8:10]
    MsgSrcAddr = MsgData[10:14]
    MsgCmd = MsgData[14:16]

    TYPE_ACTIONS = {
            '01':'hold_down',
            '02':'click_down',
            '03':'release_down',
            '05':'hold_up',
            '06':'click_up',
            '07':'release_up'
            }

    if self.ListOfDevices[MsgSrcAddr]['Model'] == 'TRADFRI remote control':
        """
        Ikea Remote 5 buttons round.
            ( cmd, cluster )
            ( 0x01, 0x0008 ) - Down Push 
            ( 0x02, 0x0008 ) - Down Click
            ( 0x03, 0x0008 ) - Down Release 
            ( 0x05, 0x0008 ) - Up Push 
            ( 0x06, 0x0008 ) - Up Click
            ( 0x07, 0x0008 ) - Up Release 
        """
        if MsgClusterId == '0008':
            if MsgCmd in TYPE_ACTIONS:
                selector = TYPE_ACTIONS[MsgCmd]
                Domoticz.Debug("Decode8085 - Selector: %s" %selector)
                MajDomoDevice(self, Devices, MsgSrcAddr, MsgEP, "rmt1", selector )
            else:
                Domoticz.Log("Decode8085 - SQN: %s, Addr: %s, Ep: %s, Cluster: %s, Cmd: %s, Unknown: %s" \
                        %(MsgSQN, MsgSrcAddr, MsgEP, MsgClusterId, MsgCmd, unknown_))
        else:
            Domoticz.Log("Decode8085 - SQN: %s, Addr: %s, Ep: %s, Cluster: %s, Cmd: %s, Unknown: %s" \
                    %(MsgSQN, MsgSrcAddr, MsgEP, MsgClusterId, MsgCmd, unknown_))


def Decode8095(self, Devices, MsgData, MsgRSSI) :
    'Remote button pressed ON/OFF'

    MsgSQN = MsgData[0:2]
    MsgEP = MsgData[2:4]
    MsgClusterId = MsgData[4:8]
    unknown_ = MsgData[8:10]
    MsgSrcAddr = MsgData[10:14]
    MsgCmd = MsgData[14:16]

    if MsgSrcAddr not in self.ListOfDevices:
        return
    if 'Model' not in self.ListOfDevices[MsgSrcAddr]:
        return

    if self.ListOfDevices[MsgSrcAddr]['Model'] == 'TRADFRI remote control':
        """
            Ikea Remote 5 buttons round.
             ( cmd, directioni, cluster )
             ( 0x02, 0x0006) - click middle button - Action Toggle On/Off Off/on
        """
        if MsgClusterId == '0006' and MsgCmd == '02': 
            MajDomoDevice(self, Devices, MsgSrcAddr, MsgEP, "rmt1", 'toggle' )
        else:
            Domoticz.Log("Decode8095 - SQN: %s, Addr: %s, Ep: %s, Cluster: %s, Cmd: %s, Unknown: %s " %(MsgSQN, MsgSrcAddr, MsgEP, MsgClusterId, MsgCmd, unknown_))
    else:
       Domoticz.Log("Decode8095 - SQN: %s, Addr: %s, Ep: %s, Cluster: %s, Cmd: %s, Unknown: %s " %(MsgSQN, MsgSrcAddr, MsgEP, MsgClusterId, MsgCmd, unknown_))


def Decode80A7(self, Devices, MsgData, MsgRSSI) :
    'Remote button pressed (LEFT/RIGHT)'

    MsgSQN = MsgData[0:2]
    MsgEP = MsgData[2:4]
    MsgClusterId = MsgData[4:8]
    MsgCmd = MsgData[8:10]
    MsgDirection = MsgData[10:12]
    unkown_ = MsgData[12:18]
    MsgSrcAddr = MsgData[18:22]

    # Ikea Remote 5 buttons round.
    #  ( cmd, directioni, cluster )
    #  ( 0x07, 0x00, 0005 )  Click right button
    #  ( 0x07, 0x01, 0005 )  Click left button

    TYPE_DIRECTIONS = {
            '00':'right',
            '01':'left',
            '02':'middle'
            }
    TYPE_ACTIONS = {
            '07':'click',
            '08':'hold',
            '09':'release'
            }

    if MsgSrcAddr not in self.ListOfDevices:
        return
    if 'Model' not in self.ListOfDevices[MsgSrcAddr]:
        return

    if MsgClusterId == '0005':
        if MsgDirection not in TYPE_DIRECTIONS:
            # Might be in the case of Release Left or Right
            Domoticz.Log("Decode80A7 - Addr: %s, Ep: %s, Cluster: %s, Cmd: %s, Direction: %s, Unknown_ %s" \
                    %(MsgSrcAddr, MsgEP, MsgClusterId, MsgCmd, MsgDirection, unkown_))

        elif MsgCmd in TYPE_ACTIONS and MsgDirection in TYPE_DIRECTIONS:
            selector = TYPE_DIRECTIONS[MsgDirection] + '_' + TYPE_ACTIONS[MsgCmd]
            MajDomoDevice(self, Devices, MsgSrcAddr, MsgEP, "rmt1", selector )
            Domoticz.Debug("Decode80A7 - selector: %s" %selector)

            if self.groupmgt:
                if TYPE_DIRECTIONS[MsgDirection] in ( 'right', 'left'):
                    self.groupmgt.manageIkeaTradfriRemoteLeftRight( MsgSrcAddr, TYPE_DIRECTIONS[MsgDirection])
        else:
            Domoticz.Log("Decode80A7 - SQN: %s, Addr: %s, Ep: %s, Cluster: %s, Cmd: %s, Direction: %s, Unknown_ %s" \
                    %(MsgSQN, MsgSrcAddr, MsgEP, MsgClusterId, MsgCmd, MsgDirection, unkown_))
    else:
        Domoticz.Log("Decode80A7 - SQN: %s, Addr: %s, Ep: %s, Cluster: %s, Cmd: %s, Direction: %s, Unknown_ %s" \
                %(MsgSQN, MsgSrcAddr, MsgEP, MsgClusterId, MsgCmd, MsgDirection, unkown_))




