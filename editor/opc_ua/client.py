# opcua/client.py



import os

from editors.ConfTreeNodeEditor import ConfTreeNodeEditor
from PLCControler import LOCATION_CONFNODE, LOCATION_VAR_INPUT, LOCATION_VAR_OUTPUT
from .opcua_client_maker import OPCUAClientPanel, OPCUAClientModel, UA_IEC_types, authParams

import util.paths as paths

# Paths to open62541 assume that 
# - open62541 directory is aside beremiz directory
# - open62541 was just built (not installed)

Open62541Path = paths.ThirdPartyPath("open62541")
Open62541LibraryPath = os.path.join(Open62541Path,"build","bin") 
Open62541IncludePaths = [os.path.join(Open62541Path, *dirs) for dirs in [
    ("plugins","include"),
    ("build","src_generated"),
    ("include",),
    ("arch",)]]

# Tests need to use other default hosts
OPCUA_DEFAULT_HOST = os.environ.get("OPCUA_DEFAULT_HOST", "127.0.0.1")

class OPCUAClientEditor(ConfTreeNodeEditor):
    CONFNODEEDITOR_TABS = [
        (_("OPC-UA Client"), "CreateOPCUAClient_UI")]

    def Log(self, msg):
        self.Controler.GetCTRoot().logger.write(msg)

    def CreateOPCUAClient_UI(self, parent):
        return OPCUAClientPanel(parent, self.Controler.GetModelData(), self.Log, self.Controler.GetConfig)

class OPCUAClient(object):
    XSD = """<?xml version="1.0" encoding="ISO-8859-1" ?>
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="OPCUAClient">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="AuthType" minOccurs="0">
              <xsd:complexType>
                <xsd:choice minOccurs="0">
                  <xsd:element name="x509">
                    <xsd:complexType>
                      <xsd:sequence>
                        <xsd:element name="Policy">
                          <xsd:annotation>
                            <xsd:documentation>Default to Basic256Sha256 if not specified</xsd:documentation>
                          </xsd:annotation>
                          <xsd:complexType>
                            <xsd:choice minOccurs="0">
                              <xsd:element name="Basic256Sha256"/>
                              <xsd:element name="Basic128Rsa15"/>
                              <xsd:element name="Basic256"/>
                            </xsd:choice>
                          </xsd:complexType>
                        </xsd:element>
                        <xsd:element name="Mode">
                          <xsd:complexType>
                            <xsd:choice minOccurs="0">
                              <xsd:element name="SignAndEncrypt"/>
                              <xsd:element name="Sign"/>
                            </xsd:choice>
                          </xsd:complexType>
                        </xsd:element>
                      </xsd:sequence>
                      <xsd:attribute name="Certificate" type="xsd:string" use="optional" default="certificate.pem"/>
                      <xsd:attribute name="PrivateKey" type="xsd:string" use="optional" default="private_key.pem"/>
                    </xsd:complexType>
                  </xsd:element>
                  <xsd:element name="UserPassword">
                    <xsd:complexType>
                      <xsd:attribute name="User" type="xsd:string" use="optional"/>
                      <xsd:attribute name="Password" type="xsd:string" use="optional"/>
                    </xsd:complexType>
                  </xsd:element>
                </xsd:choice>
              </xsd:complexType>
            </xsd:element>
          </xsd:sequence>
          <xsd:attribute name="Server_URI" type="xsd:string" use="optional" default="opc.tcp://"""+OPCUA_DEFAULT_HOST+""":4840"/>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
    """

    EditorType = OPCUAClientEditor

    def __init__(self):
        self.modeldata = OPCUAClientModel(self.Log, self.CTNMarkModified)

        filepath = self.GetFileName()
        if os.path.isfile(filepath):
            self.modeldata.LoadCSV(filepath)

    def Log(self, msg):
        self.GetCTRoot().logger.write(msg)

    def GetModelData(self):
        return self.modeldata

    def GetConfig(self):
        def cfg(path): 
            try:
                attr=self.GetParamsAttributes("OPCUAClient."+path)
            except ValueError:
                return None
            return attr["value"]

        AuthType = cfg("AuthType")
        res = dict(URI=cfg("Server_URI"), AuthType=AuthType)

        paramList = authParams.get(AuthType, None)
        if paramList:
            for name,default in paramList:
                value = cfg("AuthType."+name)
                if value == "" or value is None:
                    value = default
                # cryptomaterial is expected to be in project's user provide file directory
                if name in ["Certificate","PrivateKey"]:
                    value = os.path.join(self.GetCTRoot()._getProjectFilesPath(), value)
                res[name] = value

        return res

    def GetFileName(self):
        return os.path.join(self.CTNPath(), 'selected.csv')

    def OnCTNSave(self, from_project_path=None):
        self.modeldata.SaveCSV(self.GetFileName())
        return True

    def CTNGenerate_C(self, buildpath, locations):
        current_location = self.GetCurrentLocation()
        locstr = "_".join(map(str, current_location))
        c_path = os.path.join(buildpath, "opcua_client__%s.c" % locstr)

        c_code = '#include "beremiz.h"\n'
        c_code += self.modeldata.GenerateC(c_path, locstr, self.GetConfig())

        with open(c_path, 'w') as c_file:
            c_file.write(c_code)

        LDFLAGS = ['"' + os.path.join(Open62541LibraryPath, "libopen62541.a") + '"', '-lcrypto']

        CFLAGS = ' '.join(['-I"' + path + '"' for path in Open62541IncludePaths])

        # Note: all user provided files are systematicaly copied, including cryptomaterial

        return [(c_path, CFLAGS)], LDFLAGS, True

    def GetVariableLocationTree(self):
        current_location = self.GetCurrentLocation()
        locstr = "_".join(map(str, current_location))
        name = self.BaseParams.getName()
        entries = []
        for direction, data in self.modeldata.items():
            iec_direction_prefix = {"input": "__I", "output": "__Q"}[direction]
            for row in data:
                dname, ua_nsidx, ua_nodeid_type, _ua_node_id, ua_type, iec_number = row
                iec_type, C_type, iec_size_prefix, ua_type_enum, ua_type = UA_IEC_types[ua_type]
                c_loc_name = iec_direction_prefix + iec_size_prefix + locstr + "_" + str(iec_number)
                entries.append({
                    "name": dname,
                    "type": {"input": LOCATION_VAR_INPUT, "output": LOCATION_VAR_OUTPUT}[direction],
                    "size": {"X":1, "B":8, "W":16, "D":32, "L":64}[iec_size_prefix],
                    "IEC_type": iec_type,
                    "var_name": c_loc_name,
                    "location": iec_size_prefix + ".".join([str(i) for i in current_location]) + "." + str(iec_number),
                    "description": "",
                    "children": []})
        return {"name": name,
                "type": LOCATION_CONFNODE,
                "location": ".".join([str(i) for i in current_location]) + ".x",
                "children": entries}

