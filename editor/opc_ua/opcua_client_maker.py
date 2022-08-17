from __future__ import print_function
from __future__ import absolute_import

import csv

from opcua import Client
from opcua import ua

import wx
from wx.lib.agw.hypertreelist import HyperTreeList as TreeListCtrl
import wx.dataview as dv


UA_IEC_types = dict(
#   pyopcua | IEC61131|  C  type  | sz |  open62541  enum  | open62541
    Boolean = ("BOOL" , "uint8_t" , "X", "UA_TYPES_BOOLEAN", "UA_Boolean"),
    SByte   = ("SINT" , "int8_t"  , "B", "UA_TYPES_SBYTE"  , "UA_SByte"  ),
    Byte    = ("USINT", "uint8_t" , "B", "UA_TYPES_BYTE"   , "UA_Byte"   ),
    Int16   = ("INT"  , "int16_t" , "W", "UA_TYPES_INT16"  , "UA_Int16"  ),
    UInt16  = ("UINT" , "uint16_t", "W", "UA_TYPES_UINT16" , "UA_UInt16" ),
    Int32   = ("DINT" , "uint32_t", "D", "UA_TYPES_INT32"  , "UA_Int32"  ),
    UInt32  = ("UDINT", "int32_t" , "D", "UA_TYPES_UINT32" , "UA_UInt32" ),
    Int64   = ("LINT" , "int64_t" , "L", "UA_TYPES_INT64"  , "UA_Int64"  ),
    UInt64  = ("ULINT", "uint64_t", "L", "UA_TYPES_UINT64" , "UA_UInt64" ),
    Float   = ("REAL" , "float"   , "D", "UA_TYPES_FLOAT"  , "UA_Float"  ),
    Double  = ("LREAL", "double"  , "L", "UA_TYPES_DOUBLE" , "UA_Double" ),
)

UA_NODE_ID_types = {
    "int"   : ("UA_NODEID_NUMERIC", "{}"  ),
    "str"   : ("UA_NODEID_STRING" , '"{}"'),
    "UUID"  : ("UA_NODEID_UUID"   , '"{}"'),
}

lstcolnames  = [  "Name", "NSIdx", "IdType", "Id", "Type", "IEC"]
lstcolwidths = [     100,      50,      100,  100,    100,    50]
lstcoltypess = [     str,     int,      str,  str,    str,   int]

directions = ["input", "output"]

class OPCUASubListModel(dv.PyDataViewIndexListModel):
    def __init__(self, data, log):
        dv.PyDataViewIndexListModel.__init__(self, len(data))
        self.data = data
        self.log = log

    def GetColumnType(self, col):
        return "string"

    def GetValueByRow(self, row, col):
        return str(self.data[row][col])

    # This method is called when the user edits a data item in the view.
    def SetValueByRow(self, value, row, col):
        expectedtype = lstcoltypess[col]

        try:
            v = expectedtype(value)
        except ValueError: 
            self.log("String {} is invalid for type {}\n".format(value,expectedtype.__name__))
            return False

        if col == lstcolnames.index("IdType") and v not in UA_NODE_ID_types:
            self.log("{} is invalid for IdType\n".format(value))
            return False

        self.data[row][col] = v
        return True

    # Report how many columns this model provides data for.
    def GetColumnCount(self):
        return len(lstcolnames)

    # Report the number of rows in the model
    def GetCount(self):
        #self.log.write('GetCount')
        return len(self.data)

    # Called to check if non-standard attributes should be used in the
    # cell at (row, col)
    def GetAttrByRow(self, row, col, attr):
        if col == 5:
            attr.SetColour('blue')
            attr.SetBold(True)
            return True
        return False


    def DeleteRows(self, rows):
        # make a copy since we'll be sorting(mutating) the list
        # use reverse order so the indexes don't change as we remove items
        rows = sorted(rows, reverse=True)

        for row in rows:
            # remove it from our data structure
            del self.data[row]
            # notify the view(s) using this model that it has been removed
            self.RowDeleted(row)


    def AddRow(self, value):
        if self.data.append(value):
            # notify views
            self.RowAppended()
    
    def ResetData(self):
        self.Reset(len(self.data))

OPCUAClientDndMagicWord = "text/beremiz-opcuaclient"

class NodeDropTarget(wx.DropTarget):

    def __init__(self, parent):
        data = wx.CustomDataObject(OPCUAClientDndMagicWord)
        wx.DropTarget.__init__(self, data)
        self.ParentWindow = parent

    def OnDrop(self, x, y):
        self.ParentWindow.OnNodeDnD()
        return True

class OPCUASubListPanel(wx.Panel):
    def __init__(self, parent, log, model, direction):
        self.log = log
        wx.Panel.__init__(self, parent, -1)

        self.dvc = dv.DataViewCtrl(self,
                                   style=wx.BORDER_THEME
                                   | dv.DV_ROW_LINES
                                   | dv.DV_HORIZ_RULES
                                   | dv.DV_VERT_RULES
                                   | dv.DV_MULTIPLE
                                   )

        self.model = model

        self.dvc.AssociateModel(self.model)

        for idx,(colname,width) in enumerate(zip(lstcolnames,lstcolwidths)):
            self.dvc.AppendTextColumn(colname,  idx, width=width, mode=dv.DATAVIEW_CELL_EDITABLE)

        DropTarget = NodeDropTarget(self)
        self.dvc.SetDropTarget(DropTarget)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        self.direction =  direction
        titlestr = direction + " variables"

        title = wx.StaticText(self, label = titlestr)

        delbt = wx.Button(self, label="Delete Row(s)")
        self.Bind(wx.EVT_BUTTON, self.OnDeleteRows, delbt)

        topsizer = wx.BoxSizer(wx.HORIZONTAL)
        topsizer.Add(title, 1, wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, 5)
        topsizer.Add(delbt, 0, wx.LEFT|wx.RIGHT, 5)
        self.Sizer.Add(topsizer, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        self.Sizer.Add(self.dvc, 1, wx.EXPAND)



    def OnDeleteRows(self, evt):
        items = self.dvc.GetSelections()
        rows = [self.model.GetRow(item) for item in items]
        self.model.DeleteRows(rows)


    def OnNodeDnD(self):
        # Have to find OPC-UA client extension panel from here 
        # in order to avoid keeping reference (otherwise __del__ isn't called)
        #             splitter.        panel.      splitter
        ClientPanel = self.GetParent().GetParent().GetParent()
        nodes = ClientPanel.GetSelectedNodes()
        for node in nodes:
            cname = node.get_node_class().name
            dname = node.get_display_name().Text
            if cname != "Variable":
                self.log("Node {} ignored (not a variable)".format(dname))
                continue

            tname = node.get_data_type_as_variant_type().name
            if tname not in UA_IEC_types:
                self.log("Node {} ignored (unsupported type)".format(dname))
                continue

            access = node.get_access_level()
            if {"input":ua.AccessLevel.CurrentRead,
                "output":ua.AccessLevel.CurrentWrite}[self.direction] not in access:
                self.log("Node {} ignored because of insuficient access rights".format(dname))
                continue

            nsid = node.nodeid.NamespaceIndex
            nid =  node.nodeid.Identifier
            nid_type =  type(nid).__name__
            iecid = nid

            value = [dname,
                     nsid,
                     nid_type,
                     nid,
                     tname,
                     iecid]
            self.model.AddRow(value)



il = None
fldridx = None    
fldropenidx = None
fileidx = None
smileidx = None
isz = (16,16)

treecolnames  = [  "Name", "Class", "NSIdx", "Id"]
treecolwidths = [     250,     100,      50,  200]


def prepare_image_list():
    global il, fldridx, fldropenidx, fileidx, smileidx    

    if il is not None: 
        return

    il = wx.ImageList(isz[0], isz[1])
    fldridx     = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER,      wx.ART_OTHER, isz))
    fldropenidx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, isz))
    fileidx     = il.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))
    smileidx    = il.Add(wx.ArtProvider.GetBitmap(wx.ART_ADD_BOOKMARK, wx.ART_OTHER, isz))


class OPCUAClientPanel(wx.SplitterWindow):
    def __init__(self, parent, modeldata, log, uri_getter):
        self.log = log
        wx.SplitterWindow.__init__(self, parent, -1)

        self.ordered_nodes = []

        self.inout_panel = wx.Panel(self)
        self.inout_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=2, vgap=0)
        self.inout_sizer.AddGrowableCol(0)
        self.inout_sizer.AddGrowableRow(1)

        self.client = None
        self.uri_getter = uri_getter

        self.connect_button = wx.ToggleButton(self.inout_panel, -1, "Browse Server")

        self.selected_splitter = wx.SplitterWindow(self.inout_panel, style=wx.SUNKEN_BORDER | wx.SP_3D)

        self.selected_datas = modeldata
        self.selected_models = { direction:OPCUASubListModel(self.selected_datas[direction], log) for direction in directions }
        self.selected_lists = { direction:OPCUASubListPanel(
                self.selected_splitter, log, 
                self.selected_models[direction], direction) 
            for direction in directions }

        self.selected_splitter.SplitHorizontally(*[self.selected_lists[direction] for direction in directions]+[300])

        self.inout_sizer.Add(self.connect_button, flag=wx.GROW)
        self.inout_sizer.Add(self.selected_splitter, flag=wx.GROW)
        self.inout_sizer.Layout()
        self.inout_panel.SetAutoLayout(True)
        self.inout_panel.SetSizer(self.inout_sizer)

        self.Initialize(self.inout_panel)

        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnConnectButton, self.connect_button)

    def OnClose(self):
        if self.client is not None:
            self.client.disconnect()
            self.client = None

    def __del__(self):
        self.OnClose()

    def OnConnectButton(self, event):
        if self.connect_button.GetValue():
            
            self.tree_panel = wx.Panel(self)
            self.tree_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=2, vgap=0)
            self.tree_sizer.AddGrowableCol(0)
            self.tree_sizer.AddGrowableRow(0)

            self.tree = TreeListCtrl(self.tree_panel, -1, style=0, agwStyle=
                                            wx.TR_DEFAULT_STYLE
                                            | wx.TR_MULTIPLE
                                            | wx.TR_FULL_ROW_HIGHLIGHT
                                       )

            prepare_image_list()
            self.tree.SetImageList(il)

            for idx,(colname, width) in enumerate(zip(treecolnames, treecolwidths)):
                self.tree.AddColumn(colname)
                self.tree.SetColumnWidth(idx, width)

            self.tree.SetMainColumn(0)

            self.client = Client(self.uri_getter())
            self.client.connect()
            self.client.load_type_definitions()  # load definition of server specific structures/extension objects
            rootnode = self.client.get_root_node()

            rootitem = self.AddNodeItem(self.tree.AddRoot, rootnode)

            # Populate first level so that root can be expanded
            self.CreateSubItems(rootitem)

            self.tree.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.OnExpand)

            self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnTreeNodeSelection)
            self.tree.Bind(wx.EVT_TREE_BEGIN_DRAG, self.OnTreeBeginDrag)

            self.tree.Expand(rootitem)

            hint = wx.StaticText(self, label = "Drag'n'drop desired variables from tree to Input or Output list")

            self.tree_sizer.Add(self.tree, flag=wx.GROW)
            self.tree_sizer.Add(hint, flag=wx.GROW)
            self.tree_sizer.Layout()
            self.tree_panel.SetAutoLayout(True)
            self.tree_panel.SetSizer(self.tree_sizer)

            self.SplitVertically(self.tree_panel, self.inout_panel, 500)
        else:
            self.client.disconnect()
            self.client = None
            self.Unsplit(self.tree_panel)
            self.tree_panel.Destroy()


    def CreateSubItems(self, item):
        node, browsed = self.tree.GetPyData(item)
        if not browsed:
            for subnode in node.get_children():
                self.AddNodeItem(lambda n: self.tree.AppendItem(item, n), subnode)
            self.tree.SetPyData(item,(node, True))

    def AddNodeItem(self, item_creation_func, node):
        nsid = node.nodeid.NamespaceIndex
        nid =  node.nodeid.Identifier
        dname = node.get_display_name().Text
        cname = node.get_node_class().name

        item = item_creation_func(dname)

        if cname == "Variable":
            access = node.get_access_level()
            normalidx = fileidx
            r = ua.AccessLevel.CurrentRead in access
            w = ua.AccessLevel.CurrentWrite in access
            if r and w:
                ext = "RW"
            elif r:
                ext = "RO"
            elif w:
                ext = "WO"  # not sure this one exist
            else:
                ext = "no access"  # not sure this one exist
            cname = "Var "+node.get_data_type_as_variant_type().name+" (" + ext + ")"
        else:
            normalidx = fldridx

        self.tree.SetPyData(item,(node, False))
        self.tree.SetItemText(item, cname, 1)
        self.tree.SetItemText(item, str(nsid), 2)
        self.tree.SetItemText(item, type(nid).__name__+": "+str(nid), 3)
        self.tree.SetItemImage(item, normalidx, which = wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(item, fldropenidx, which = wx.TreeItemIcon_Expanded)

        return item

    def OnExpand(self, evt):
        for item in evt.GetItem().GetChildren():
            self.CreateSubItems(item)

    # def OnActivate(self, evt):
    #     item = evt.GetItem()
    #     node, browsed = self.tree.GetPyData(item)

    def OnTreeNodeSelection(self, event):
        items = self.tree.GetSelections()
        items_pydata = [self.tree.GetPyData(item) for item in items]

        nodes = [node for node, _unused in items_pydata]

        # append new nodes to ordered list
        for node in nodes:
            if node not in self.ordered_nodes:
                self.ordered_nodes.append(node)

        # filter out vanished items
        self.ordered_nodes = [
            node 
            for node in self.ordered_nodes 
            if node in nodes]

    def GetSelectedNodes(self):
        return self.ordered_nodes 

    def OnTreeBeginDrag(self, event):
        """
        Called when a drag is started in tree
        @param event: wx.TreeEvent
        """
        if self.ordered_nodes:
            # Just send a recognizable mime-type, drop destination
            # will get python data from parent
            data = wx.CustomDataObject(OPCUAClientDndMagicWord)
            dragSource = wx.DropSource(self)
            dragSource.SetData(data)
            dragSource.DoDragDrop()

    def Reset(self):
        for direction in directions:
            self.selected_models[direction].ResetData() 
        

class OPCUAClientList(list):
    def __init__(self, log = lambda m:None):
        super(OPCUAClientList, self).__init__(self)
        self.log = log

    def append(self, value):
        v = dict(zip(lstcolnames, value))

        if type(v["IEC"]) != int:
            if len(self) == 0:
                v["IEC"] = 0
            else:
                iecnums = set(zip(*self)[lstcolnames.index("IEC")])
                greatest = max(iecnums)
                holes = set(range(greatest)) - iecnums
                v["IEC"] = min(holes) if holes else greatest+1

        if v["IdType"] not in UA_NODE_ID_types:
            self.log("Unknown IdType\n".format(value))
            return False

        try:
            for t,n in zip(lstcoltypess, lstcolnames):
                v[n] = t(v[n]) 
        except ValueError: 
            self.log("Variable {} (Id={}) has invalid type\n".format(v["Name"],v["Id"]))
            return False

        if len(self)>0 and v["Id"] in zip(*self)[lstcolnames.index("Id")]:
            self.log("Variable {} (Id={}) already in list\n".format(v["Name"],v["Id"]))
            return False

        list.append(self, [v[n] for n in lstcolnames])

        return True

class OPCUAClientModel(dict):
    def __init__(self, log = lambda m:None):
        super(OPCUAClientModel, self).__init__()
        for direction in directions:
            self[direction] = OPCUAClientList(log)

    def LoadCSV(self,path):
        with open(path, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            buf = {direction:[] for direction, _model in self.iteritems()}
            for direction, model in self.iteritems():
                self[direction][:] = []
            for row in reader:
                direction = row[0]
                self[direction].append(row[1:])

    def SaveCSV(self,path):
        with open(path, 'wb') as csvfile:
            for direction, data in self.iteritems():
                writer = csv.writer(csvfile, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
                for row in data:
                    writer.writerow([direction] + row)

    def GenerateC(self, path, locstr, server_uri):
        template = """/* code generated by beremiz OPC-UA extension */

#include <open62541/client_config_default.h>
#include <open62541/client_highlevel.h>
#include <open62541/plugin/log_stdout.h>

static UA_Client *client;

#define DECL_VAR(ua_type, C_type, c_loc_name)                                                       \\
static UA_Variant c_loc_name##_variant;                                                             \\
static C_type c_loc_name##_buf = 0;                                                                 \\
C_type *c_loc_name = &c_loc_name##_buf;

%(decl)s

void __cleanup_%(locstr)s(void)
{
    UA_Client_disconnect(client);
    UA_Client_delete(client);
}


#define INIT_READ_VARIANT(ua_type, c_loc_name)                                                     \\
    UA_Variant_init(&c_loc_name##_variant);

#define INIT_WRITE_VARIANT(ua_type, ua_type_enum, c_loc_name)       \\
    UA_Variant_setScalar(&c_loc_name##_variant, (ua_type*)c_loc_name, &UA_TYPES[ua_type_enum]);

int __init_%(locstr)s(int argc,char **argv)
{
    UA_StatusCode retval;
    client = UA_Client_new();
    UA_ClientConfig_setDefault(UA_Client_getConfig(client));
%(init)s

    /* Connect to server */
    retval = UA_Client_connect(client, "%(uri)s");
    if(retval != UA_STATUSCODE_GOOD) {
        UA_Client_delete(client);
        return EXIT_FAILURE;
    }
}

#define READ_VALUE(ua_type, ua_type_enum, c_loc_name, ua_nodeid_type, ua_nsidx, ua_node_id)        \\
    retval = UA_Client_readValueAttribute(                                                         \\
        client, ua_nodeid_type(ua_nsidx, ua_node_id), &c_loc_name##_variant);                      \\
    if(retval == UA_STATUSCODE_GOOD && UA_Variant_isScalar(&c_loc_name##_variant) &&               \\
       c_loc_name##_variant.type == &UA_TYPES[ua_type_enum]) {                                     \\
            c_loc_name##_buf = *(ua_type*)c_loc_name##_variant.data;                               \\
            UA_Variant_clear(&c_loc_name##_variant);  /* Unalloc requiered on each read ! */       \\
    }

void __retrieve_%(locstr)s(void)
{
    UA_StatusCode retval;
%(retrieve)s
}

#define WRITE_VALUE(ua_type, c_loc_name, ua_nodeid_type, ua_nsidx, ua_node_id)       \\
    UA_Client_writeValueAttribute(                                                                 \\
        client, ua_nodeid_type(ua_nsidx, ua_node_id), &c_loc_name##_variant);

void __publish_%(locstr)s(void)
{
%(publish)s
}

"""
        
        formatdict = dict(
            locstr   = locstr,
            uri      = server_uri,
            decl     = "",
            cleanup  = "",
            init     = "",
            retrieve = "",
            publish  = "" 
        )
        for direction, data in self.iteritems():
            iec_direction_prefix = {"input": "__I", "output": "__Q"}[direction]
            for row in data:
                name, ua_nsidx, ua_nodeid_type, _ua_node_id, ua_type, iec_number = row
                iec_type, C_type, iec_size_prefix, ua_type_enum, ua_type = UA_IEC_types[ua_type]
                c_loc_name = iec_direction_prefix + iec_size_prefix + locstr + "_" + str(iec_number)
                ua_nodeid_type, id_formating = UA_NODE_ID_types[ua_nodeid_type]
                ua_node_id = id_formating.format(_ua_node_id)

                formatdict["decl"] += """
DECL_VAR({ua_type}, {C_type}, {c_loc_name})""".format(**locals())

                if direction == "input":
                    formatdict["init"] +="""
    INIT_READ_VARIANT({ua_type}, {c_loc_name})""".format(**locals())
                    formatdict["retrieve"] += """
    READ_VALUE({ua_type}, {ua_type_enum}, {c_loc_name}, {ua_nodeid_type}, {ua_nsidx}, {ua_node_id})""".format(**locals())

                if direction == "output":
                    formatdict["init"] +="""
    INIT_WRITE_VARIANT({ua_type}, {ua_type_enum}, {c_loc_name})""".format(**locals())
                    formatdict["publish"] += """
    WRITE_VALUE({ua_type}, {c_loc_name}, {ua_nodeid_type}, {ua_nsidx}, {ua_node_id})""".format(**locals())

        Ccode = template%formatdict
        
        return Ccode

if __name__ == "__main__":

    import wx.lib.mixins.inspection as wit
    import sys,os

    app = wit.InspectableApp()

    frame = wx.Frame(None, -1, "OPCUA Client Test App", size=(800,600))

    uri = sys.argv[1] if len(sys.argv)>1 else "opc.tcp://localhost:4840"

    test_panel = wx.Panel(frame)
    test_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=2, vgap=0)
    test_sizer.AddGrowableCol(0)
    test_sizer.AddGrowableRow(0)

    modeldata = OPCUAClientModel(print)

    opcuatestpanel = OPCUAClientPanel(test_panel, modeldata, print, lambda:uri)

    def OnGenerate(evt):
        dlg = wx.FileDialog(
            frame, message="Generate file as ...", defaultDir=os.getcwd(),
            defaultFile="", 
            wildcard="C (*.c)|*.c", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
            )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            Ccode = """
/*
In case open62541 was built just aside beremiz, you can build this test with:
gcc %s -o %s \\
    -I ../../open62541/plugins/include/ \\
    -I ../../open62541/build/src_generated/ \\
    -I ../../open62541/include/ \\
    -I ../../open62541/arch/ ../../open62541/build/bin/libopen62541.a
*/

"""%(path, path[:-2]) + modeldata.GenerateC(path, "test", uri) + """

int main(int argc, char *argv[]) {

    __init_test(arc,argv);
   
    __retrieve_test();
   
    __publish_test();

    __cleanup_test();

    return EXIT_SUCCESS;
}
"""

            with open(path, 'wb') as Cfile:
                Cfile.write(Ccode)


        dlg.Destroy()

    def OnLoad(evt):
        dlg = wx.FileDialog(
            frame, message="Choose a file",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard="CSV (*.csv)|*.csv",
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR | wx.FD_FILE_MUST_EXIST )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            modeldata.LoadCSV(path)
            opcuatestpanel.Reset()

        dlg.Destroy()

    def OnSave(evt):
        dlg = wx.FileDialog(
            frame, message="Save file as ...", defaultDir=os.getcwd(),
            defaultFile="", 
            wildcard="CSV (*.csv)|*.csv", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
            )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            modeldata.SaveCSV(path)

        dlg.Destroy()

    test_sizer.Add(opcuatestpanel, flag=wx.GROW)

    testbt_sizer = wx.BoxSizer(wx.HORIZONTAL)

    loadbt = wx.Button(test_panel, label="Load")
    test_panel.Bind(wx.EVT_BUTTON, OnLoad, loadbt)

    savebt = wx.Button(test_panel, label="Save")
    test_panel.Bind(wx.EVT_BUTTON, OnSave, savebt)

    genbt = wx.Button(test_panel, label="Generate")
    test_panel.Bind(wx.EVT_BUTTON, OnGenerate, genbt)

    testbt_sizer.Add(loadbt, 0, wx.LEFT|wx.RIGHT, 5)
    testbt_sizer.Add(savebt, 0, wx.LEFT|wx.RIGHT, 5)
    testbt_sizer.Add(genbt, 0, wx.LEFT|wx.RIGHT, 5)

    test_sizer.Add(testbt_sizer, flag=wx.GROW)
    test_sizer.Layout()
    test_panel.SetAutoLayout(True)
    test_panel.SetSizer(test_sizer)

    def OnClose(evt):
        opcuatestpanel.OnClose()
        evt.Skip()

    frame.Bind(wx.EVT_CLOSE, OnClose)

    frame.Show()

    app.MainLoop()

