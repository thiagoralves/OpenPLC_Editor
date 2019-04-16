#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz
#
# Copyright (C) 2011-2014: Laurent BESSARD, Edouard TISSERANT
#                          RTES Lab : CRKim, JBLee, youcu
#                          Higen Motor : Donggu Kang
#
# See COPYING file for copyrights details.

from __future__ import absolute_import
from __future__ import division
import os

from etherlab.EthercatSlave import ExtractHexDecValue, DATATYPECONVERSION, ExtractName

SLAVE_PDOS_CONFIGURATION_DECLARATION = """
/* Slave %(slave)d, "%(device_type)s"
 * Vendor ID:       0x%(vendor).8x
 * Product code:    0x%(product_code).8x
 * Revision number: 0x%(revision_number).8x
 */

ec_pdo_entry_info_t slave_%(slave)d_pdo_entries[] = {
%(pdos_entries_infos)s
};

ec_pdo_info_t slave_%(slave)d_pdos[] = {
%(pdos_infos)s
};

ec_sync_info_t slave_%(slave)d_syncs[] = {
%(pdos_sync_infos)s
    {0xff}
};
"""

SLAVE_CONFIGURATION_TEMPLATE = """
    if (!(slave%(slave)d = ecrt_master_slave_config(master, %(alias)d, %(position)d, 0x%(vendor).8x, 0x%(product_code).8x))) {
        SLOGF(LOG_CRITICAL, "EtherCAT failed to get slave %(device_type)s configuration at alias %(alias)d and position %(position)d.");
        goto ecat_failed;
    }

    if (ecrt_slave_config_pdos(slave%(slave)d, EC_END, slave_%(slave)d_syncs)) {
        SLOGF(LOG_CRITICAL, "EtherCAT failed to configure PDOs for slave %(device_type)s at alias %(alias)d and position %(position)d.");
        goto ecat_failed;
    }
"""

SLAVE_INITIALIZATION_TEMPLATE = """
    {
        uint8_t value[%(data_size)d];
        EC_WRITE_%(data_type)s((uint8_t *)value, %(data)s);
        if (ecrt_master_sdo_download(master, %(slave)d, 0x%(index).4x, 0x%(subindex).2x, (uint8_t *)value, %(data_size)d, &abort_code)) {
            SLOGF(LOG_CRITICAL, "EtherCAT Failed to initialize slave %(device_type)s at alias %(alias)d and position %(position)d. Error: %%d", abort_code);
            goto ecat_failed;
        }
    }
"""

SLAVE_OUTPUT_PDO_DEFAULT_VALUE = """
    {
        uint8_t value[%(data_size)d];
        if (ecrt_master_sdo_upload(master, %(slave)d, 0x%(index).4x, 0x%(subindex).2x, (uint8_t *)value, %(data_size)d, &result_size, &abort_code)) {
            SLOGF(LOG_CRITICAL, "EtherCAT failed to get default value for output PDO in slave %(device_type)s at alias %(alias)d and position %(position)d. Error: %%ud", abort_code);
            goto ecat_failed;
        }
        %(real_var)s = EC_READ_%(data_type)s((uint8_t *)value);
    }
"""


def ConfigureVariable(entry_infos, str_completion):
    entry_infos["data_type"] = DATATYPECONVERSION.get(entry_infos["var_type"], None)
    if entry_infos["data_type"] is None:
        msg = _("Type of location \"%s\" not yet supported!") % entry_infos["var_name"]
        raise ValueError(msg)

    if not entry_infos.get("no_decl", False):
        if "real_var" in entry_infos:
            str_completion["located_variables_declaration"].append(
                "IEC_%(var_type)s %(real_var)s;" % entry_infos)
        else:
            entry_infos["real_var"] = "beremiz" + entry_infos["var_name"]
            str_completion["located_variables_declaration"].extend(
                ["IEC_%(var_type)s %(real_var)s;" % entry_infos,
                 "IEC_%(var_type)s *%(var_name)s = &%(real_var)s;" % entry_infos])
        for declaration in entry_infos.get("extra_declarations", []):
            entry_infos["extra_decl"] = declaration
            str_completion["located_variables_declaration"].append(
                "IEC_%(var_type)s *%(extra_decl)s = &%(real_var)s;" % entry_infos)
    elif "real_var" not in entry_infos:
        entry_infos["real_var"] = "beremiz" + entry_infos["var_name"]

    str_completion["used_pdo_entry_offset_variables_declaration"].append(
        "unsigned int slave%(slave)d_%(index).4x_%(subindex).2x;" % entry_infos)

    if entry_infos["data_type"] == "BIT":
        str_completion["used_pdo_entry_offset_variables_declaration"].append(
            "unsigned int slave%(slave)d_%(index).4x_%(subindex).2x_bit;" % entry_infos)

        str_completion["used_pdo_entry_configuration"].append(
            ("    {%(alias)d, %(position)d, 0x%(vendor).8x, 0x%(product_code).8x, " +
             "0x%(index).4x, %(subindex)d, &slave%(slave)d_%(index).4x_%(subindex).2x, " +
             "&slave%(slave)d_%(index).4x_%(subindex).2x_bit},") % entry_infos)

        if entry_infos["dir"] == "I":
            str_completion["retrieve_variables"].append(
                ("    %(real_var)s = EC_READ_BIT(domain1_pd + slave%(slave)d_%(index).4x_%(subindex).2x, " +
                 "slave%(slave)d_%(index).4x_%(subindex).2x_bit);") % entry_infos)
        elif entry_infos["dir"] == "Q":
            str_completion["publish_variables"].append(
                ("    EC_WRITE_BIT(domain1_pd + slave%(slave)d_%(index).4x_%(subindex).2x, " +
                 "slave%(slave)d_%(index).4x_%(subindex).2x_bit, %(real_var)s);") % entry_infos)

    else:
        str_completion["used_pdo_entry_configuration"].append(
            ("    {%(alias)d, %(position)d, 0x%(vendor).8x, 0x%(product_code).8x, 0x%(index).4x, " +
             "%(subindex)d, &slave%(slave)d_%(index).4x_%(subindex).2x},") % entry_infos)

        if entry_infos["dir"] == "I":
            str_completion["retrieve_variables"].append(
                ("    %(real_var)s = EC_READ_%(data_type)s(domain1_pd + " +
                 "slave%(slave)d_%(index).4x_%(subindex).2x);") % entry_infos)
        elif entry_infos["dir"] == "Q":
            str_completion["publish_variables"].append(
                ("    EC_WRITE_%(data_type)s(domain1_pd + slave%(slave)d_%(index).4x_%(subindex).2x, " +
                 "%(real_var)s);") % entry_infos)


def ExclusionSortFunction(x, y):
    if x["matching"] == y["matching"]:
        if x["assigned"] and not y["assigned"]:
            return -1
        elif not x["assigned"] and y["assigned"]:
            return 1
        return cmp(x["count"], y["count"])
    return -cmp(x["matching"], y["matching"])


class _EthercatCFileGenerator(object):

    def __init__(self, controler):
        self.Controler = controler

        self.Slaves = []
        self.UsedVariables = {}

    def __del__(self):
        self.Controler = None

    def DeclareSlave(self, slave_index, slave):
        self.Slaves.append((slave_index, slave.getInfo().getAutoIncAddr(), slave))

    def DeclareVariable(self, slave_index, index, subindex, iec_type, dir, name, no_decl=False):
        slave_variables = self.UsedVariables.setdefault(slave_index, {})

        entry_infos = slave_variables.get((index, subindex), None)
        if entry_infos is None:
            slave_variables[(index, subindex)] = {
                "infos": (iec_type, dir, name, no_decl, []),
                "mapped": False}
            return name
        elif entry_infos["infos"][:2] == (iec_type, dir):
            if name != entry_infos["infos"][2]:
                if dir == "I":
                    entry_infos["infos"][4].append(name)
                    return entry_infos["infos"][2]
                else:
                    msg = _("Output variables can't be defined with different locations ({a1} and {a2})").\
                          format(a1=entry_infos["infos"][2], a2=name)
                    raise ValueError(msg)
        else:
            raise ValueError(_("Definition conflict for location \"%s\"") % name)

    def GenerateCFile(self, filepath, location_str, master_number):

        # Extract etherlab master code template
        plc_etherlab_filepath = os.path.join(os.path.split(__file__)[0], "plc_etherlab.c")
        plc_etherlab_file = open(plc_etherlab_filepath, 'r')
        plc_etherlab_code = plc_etherlab_file.read()
        plc_etherlab_file.close()

        # Initialize strings for formatting master code template
        str_completion = {
            "location": location_str,
            "master_number": master_number,
            "located_variables_declaration": [],
            "used_pdo_entry_offset_variables_declaration": [],
            "used_pdo_entry_configuration": [],
            "pdos_configuration_declaration": "",
            "slaves_declaration": "",
            "slaves_configuration": "",
            "slaves_output_pdos_default_values_extraction": "",
            "slaves_initialization": "",
            "retrieve_variables": [],
            "publish_variables": [],
        }

        # Initialize variable storing variable mapping state
        for slave_entries in self.UsedVariables.itervalues():
            for entry_infos in slave_entries.itervalues():
                entry_infos["mapped"] = False

        # Sort slaves by position (IEC_Channel)
        self.Slaves.sort()
        # Initialize dictionary storing alias auto-increment position values
        alias = {}

        # Generating code for each slave
        for (slave_idx, slave_alias, slave) in self.Slaves:
            type_infos = slave.getType()

            # Defining slave alias and auto-increment position
            if alias.get(slave_alias) is not None:
                alias[slave_alias] += 1
            else:
                alias[slave_alias] = 0
            slave_pos = (slave_alias, alias[slave_alias])

            # Extract slave device informations
            device, module_extra_params = self.Controler.GetModuleInfos(type_infos)
            if device is None:
                msg = _("No informations found for device %s!") \
                      % (type_infos["device_type"])
                raise ValueError(msg)

            # Extract slaves variables to be mapped
            slave_variables = self.UsedVariables.get(slave_idx, {})

            # Extract slave device object dictionary entries
            device_entries = device.GetEntriesList()

            # Adding code for declaring slave in master code template strings
            for element in ["vendor", "product_code", "revision_number"]:
                type_infos[element] = ExtractHexDecValue(type_infos[element])
            type_infos.update(dict(zip(["slave", "alias", "position"], (slave_idx,) + slave_pos)))

            # Extract slave device CoE informations
            device_coe = device.getCoE()
            if device_coe is not None:

                # If device support CanOpen over Ethernet, adding code for calling
                # init commands when initializing slave in master code template strings
                initCmds = []
                for initCmd in device_coe.getInitCmd():
                    initCmds.append({
                        "Index": ExtractHexDecValue(initCmd.getIndex()),
                        "Subindex": ExtractHexDecValue(initCmd.getSubIndex()),
                        "Value": initCmd.getData().getcontent()})
                initCmds.extend(slave.getStartupCommands())
                for initCmd in initCmds:
                    index = initCmd["Index"]
                    subindex = initCmd["Subindex"]
                    entry = device_entries.get((index, subindex), None)
                    if entry is not None:
                        data_size = entry["BitSize"] // 8
                        data_str = ("0x%%.%dx" % (data_size * 2)) % initCmd["Value"]
                        init_cmd_infos = {
                            "index": index,
                            "subindex": subindex,
                            "data": data_str,
                            "data_type": DATATYPECONVERSION.get(entry["Type"]),
                            "data_size": data_size
                        }
                        init_cmd_infos.update(type_infos)
                        str_completion["slaves_initialization"] += SLAVE_INITIALIZATION_TEMPLATE % init_cmd_infos

                # Extract slave device PDO configuration capabilities
                PdoAssign = device_coe.getPdoAssign()
                PdoConfig = device_coe.getPdoConfig()
            else:
                PdoAssign = PdoConfig = False

            # Test if slave has a configuration or need one
            if len(device.getTxPdo() + device.getRxPdo()) > 0 or len(slave_variables) > 0 and PdoConfig and PdoAssign:

                str_completion["slaves_declaration"] += "static ec_slave_config_t *slave%(slave)d = NULL;\n" % type_infos
                str_completion["slaves_configuration"] += SLAVE_CONFIGURATION_TEMPLATE % type_infos

                # Initializing
                pdos_infos = {
                    "pdos_entries_infos": [],
                    "pdos_infos": [],
                    "pdos_sync_infos": [],
                }
                pdos_infos.update(type_infos)

                sync_managers = []
                for sync_manager_idx, sync_manager in enumerate(device.getSm()):
                    sync_manager_infos = {
                        "index": sync_manager_idx,
                        "name": sync_manager.getcontent(),
                        "slave": slave_idx,
                        "pdos": [],
                        "pdos_number": 0,
                    }

                    sync_manager_control_byte = ExtractHexDecValue(sync_manager.getControlByte())
                    sync_manager_direction = sync_manager_control_byte & 0x0c
                    sync_manager_watchdog = sync_manager_control_byte & 0x40
                    if sync_manager_direction:
                        sync_manager_infos["sync_manager_type"] = "EC_DIR_OUTPUT"
                    else:
                        sync_manager_infos["sync_manager_type"] = "EC_DIR_INPUT"
                    if sync_manager_watchdog:
                        sync_manager_infos["watchdog"] = "EC_WD_ENABLE"
                    else:
                        sync_manager_infos["watchdog"] = "EC_WD_DISABLE"

                    sync_managers.append(sync_manager_infos)

                pdos_index = []
                exclusive_pdos = {}
                selected_pdos = []
                for pdo, pdo_type in ([(pdo, "Inputs") for pdo in device.getTxPdo()] +
                                      [(pdo, "Outputs") for pdo in device.getRxPdo()]):

                    pdo_index = ExtractHexDecValue(pdo.getIndex().getcontent())
                    pdos_index.append(pdo_index)

                    excluded_list = pdo.getExclude()
                    if len(excluded_list) > 0:
                        exclusion_list = [pdo_index]
                        for excluded in excluded_list:
                            exclusion_list.append(ExtractHexDecValue(excluded.getcontent()))
                        exclusion_list.sort()

                        exclusion_scope = exclusive_pdos.setdefault(tuple(exclusion_list), [])

                        entries = pdo.getEntry()
                        pdo_mapping_match = {
                            "index": pdo_index,
                            "matching": 0,
                            "count": len(entries),
                            "assigned": pdo.getSm() is not None
                        }
                        exclusion_scope.append(pdo_mapping_match)

                        for entry in entries:
                            index = ExtractHexDecValue(entry.getIndex().getcontent())
                            subindex = ExtractHexDecValue(entry.getSubIndex())
                            if slave_variables.get((index, subindex), None) is not None:
                                pdo_mapping_match["matching"] += 1

                        if pdo.getFixed() is not True:
                            pdo_mapping_match["matching"] += \
                                module_extra_params["max_pdo_size"] - \
                                pdo_mapping_match["count"]

                    elif pdo.getMandatory():
                        selected_pdos.append(pdo_index)

                excluded_pdos = []
                for exclusion_scope in exclusive_pdos.itervalues():
                    exclusion_scope.sort(ExclusionSortFunction)
                    start_excluding_index = 0
                    if exclusion_scope[0]["matching"] > 0:
                        selected_pdos.append(exclusion_scope[0]["index"])
                        start_excluding_index = 1
                    excluded_pdos.extend([
                        pdo["index"]
                        for pdo in exclusion_scope[start_excluding_index:]
                        if PdoAssign or not pdo["assigned"]])

                for pdo, pdo_type in ([(pdo, "Inputs") for pdo in device.getTxPdo()] +
                                      [(pdo, "Outputs") for pdo in device.getRxPdo()]):
                    entries = pdo.getEntry()

                    pdo_index = ExtractHexDecValue(pdo.getIndex().getcontent())
                    if pdo_index in excluded_pdos:
                        continue

                    pdo_needed = pdo_index in selected_pdos

                    entries_infos = []

                    for entry in entries:
                        index = ExtractHexDecValue(entry.getIndex().getcontent())
                        subindex = ExtractHexDecValue(entry.getSubIndex())
                        entry_infos = {
                            "index": index,
                            "subindex": subindex,
                            "name": ExtractName(entry.getName()),
                            "bitlen": entry.getBitLen(),
                        }
                        entry_infos.update(type_infos)
                        entries_infos.append("    {0x%(index).4x, 0x%(subindex).2x, %(bitlen)d}, /* %(name)s */" % entry_infos)

                        entry_declaration = slave_variables.get((index, subindex), None)
                        if entry_declaration is not None and not entry_declaration["mapped"]:
                            pdo_needed = True

                            entry_infos.update(dict(zip(["var_type", "dir", "var_name", "no_decl", "extra_declarations"],
                                                        entry_declaration["infos"])))
                            entry_declaration["mapped"] = True

                            entry_type = entry.getDataType().getcontent()
                            if entry_infos["var_type"] != entry_type:
                                message = _("Wrong type for location \"%s\"!") % entry_infos["var_name"]
                                if self.Controler.GetSizeOfType(entry_infos["var_type"]) != \
                                   self.Controler.GetSizeOfType(entry_type):
                                    raise ValueError(message)
                                else:
                                    self.Controler.GetCTRoot().logger.write_warning(_("Warning: ") + message + "\n")

                            if (entry_infos["dir"] == "I" and pdo_type != "Inputs") or \
                               (entry_infos["dir"] == "Q" and pdo_type != "Outputs"):
                                raise ValueError(_("Wrong direction for location \"%s\"!") % entry_infos["var_name"])

                            ConfigureVariable(entry_infos, str_completion)

                        elif pdo_type == "Outputs" and entry.getDataType() is not None and device_coe is not None:
                            data_type = entry.getDataType().getcontent()
                            entry_infos["dir"] = "Q"
                            entry_infos["data_size"] = max(1, entry_infos["bitlen"] // 8)
                            entry_infos["data_type"] = DATATYPECONVERSION.get(data_type)
                            entry_infos["var_type"] = data_type
                            entry_infos["real_var"] = "slave%(slave)d_%(index).4x_%(subindex).2x_default" % entry_infos

                            ConfigureVariable(entry_infos, str_completion)

                            str_completion["slaves_output_pdos_default_values_extraction"] += \
                                SLAVE_OUTPUT_PDO_DEFAULT_VALUE % entry_infos

                    if pdo_needed:
                        for excluded in pdo.getExclude():
                            excluded_index = ExtractHexDecValue(excluded.getcontent())
                            if excluded_index not in excluded_pdos:
                                excluded_pdos.append(excluded_index)

                        sm = pdo.getSm()
                        if sm is None:
                            for sm_idx, sync_manager in enumerate(sync_managers):
                                if sync_manager["name"] == pdo_type:
                                    sm = sm_idx
                        if sm is None:
                            raise ValueError(_("No sync manager available for %s pdo!") % pdo_type)

                        sync_managers[sm]["pdos_number"] += 1
                        sync_managers[sm]["pdos"].append(
                            {"slave": slave_idx,
                             "index": pdo_index,
                             "name": ExtractName(pdo.getName()),
                             "type": pdo_type,
                             "entries": entries_infos,
                             "entries_number": len(entries_infos),
                             "fixed": pdo.getFixed() is True})

                if PdoConfig and PdoAssign:
                    dynamic_pdos = {}
                    dynamic_pdos_number = 0
                    for category, min_index, max_index in [("Inputs", 0x1600, 0x1800),
                                                           ("Outputs", 0x1a00, 0x1C00)]:
                        for sync_manager in sync_managers:
                            if sync_manager["name"] == category:
                                category_infos = dynamic_pdos.setdefault(category, {})
                                category_infos["sync_manager"] = sync_manager
                                category_infos["pdos"] = [pdo for pdo in category_infos["sync_manager"]["pdos"]
                                                          if not pdo["fixed"] and pdo["type"] == category]
                                category_infos["current_index"] = min_index
                                category_infos["max_index"] = max_index
                                break

                    for (index, subindex), entry_declaration in slave_variables.iteritems():

                        if not entry_declaration["mapped"]:
                            entry = device_entries.get((index, subindex), None)
                            if entry is None:
                                msg = _("Unknown entry index 0x{a1:.4x}, subindex 0x{a2:.2x} for device {a3}").\
                                      format(a1=index, a2=subindex, a3=type_infos["device_type"])
                                raise ValueError(msg)

                            entry_infos = {
                                "index": index,
                                "subindex": subindex,
                                "name": entry["Name"],
                                "bitlen": entry["BitSize"],
                            }
                            entry_infos.update(type_infos)

                            entry_infos.update(dict(zip(["var_type", "dir", "var_name", "no_decl", "extra_declarations"],
                                                        entry_declaration["infos"])))
                            entry_declaration["mapped"] = True

                            if entry_infos["var_type"] != entry["Type"]:
                                message = _("Wrong type for location \"%s\"!") % entry_infos["var_name"]
                                if self.Controler.GetSizeOfType(entry_infos["var_type"]) != \
                                   self.Controler.GetSizeOfType(entry["Type"]):
                                    raise ValueError(message)
                                else:
                                    self.Controler.GetCTRoot().logger.write_warning(message + "\n")

                            if entry_infos["dir"] == "I" and entry["PDOMapping"] in ["T", "RT"]:
                                pdo_type = "Inputs"
                            elif entry_infos["dir"] == "Q" and entry["PDOMapping"] in ["R", "RT"]:
                                pdo_type = "Outputs"
                            else:
                                msg = _("Wrong direction for location \"%s\"!") \
                                      % entry_infos["var_name"]
                                raise ValueError(msg)

                            if pdo_type not in dynamic_pdos:
                                msg = _("No Sync manager defined for %s!") % pdo_type
                                raise ValueError(msg)

                            ConfigureVariable(entry_infos, str_completion)

                            if len(dynamic_pdos[pdo_type]["pdos"]) > 0:
                                pdo = dynamic_pdos[pdo_type]["pdos"][0]
                            elif module_extra_params["add_pdo"]:
                                while dynamic_pdos[pdo_type]["current_index"] in pdos_index:
                                    dynamic_pdos[pdo_type]["current_index"] += 1
                                if dynamic_pdos[pdo_type]["current_index"] >= dynamic_pdos[pdo_type]["max_index"]:
                                    raise ValueError(_("No more free PDO index available for %s!") % pdo_type)
                                pdos_index.append(dynamic_pdos[pdo_type]["current_index"])

                                dynamic_pdos_number += 1
                                pdo = {"slave": slave_idx,
                                       "index": dynamic_pdos[pdo_type]["current_index"],
                                       "name": "Dynamic PDO %d" % dynamic_pdos_number,
                                       "type": pdo_type,
                                       "entries": [],
                                       "entries_number": 0,
                                       "fixed": False}
                                dynamic_pdos[pdo_type]["sync_manager"]["pdos_number"] += 1
                                dynamic_pdos[pdo_type]["sync_manager"]["pdos"].append(pdo)
                                dynamic_pdos[pdo_type]["pdos"].append(pdo)
                            else:
                                break

                            pdo["entries"].append("    {0x%(index).4x, 0x%(subindex).2x, %(bitlen)d}, /* %(name)s */" % entry_infos)
                            if entry_infos["bitlen"] < module_extra_params["pdo_alignment"]:
                                pdo["entries"].append("    {0x0000, 0x00, %d}, /* None */" % (
                                    module_extra_params["pdo_alignment"] - entry_infos["bitlen"]))
                            pdo["entries_number"] += 1

                            if pdo["entries_number"] == module_extra_params["max_pdo_size"]:
                                dynamic_pdos[pdo_type]["pdos"].pop(0)

                pdo_offset = 0
                entry_offset = 0
                for sync_manager_infos in sync_managers:

                    for pdo_infos in sync_manager_infos["pdos"]:
                        pdo_infos["offset"] = entry_offset
                        pdo_entries = pdo_infos["entries"]
                        pdos_infos["pdos_infos"].append(
                            ("    {0x%(index).4x, %(entries_number)d, " +
                             "slave_%(slave)d_pdo_entries + %(offset)d}, /* %(name)s */") % pdo_infos)
                        entry_offset += len(pdo_entries)
                        pdos_infos["pdos_entries_infos"].extend(pdo_entries)

                    sync_manager_infos["offset"] = pdo_offset
                    pdo_offset_shift = sync_manager_infos["pdos_number"]
                    pdos_infos["pdos_sync_infos"].append(
                        ("    {%(index)d, %(sync_manager_type)s, %(pdos_number)d, " +
                         ("slave_%(slave)d_pdos + %(offset)d" if pdo_offset_shift else "NULL") +
                         ", %(watchdog)s},") % sync_manager_infos)
                    pdo_offset += pdo_offset_shift

                for element in ["pdos_entries_infos", "pdos_infos", "pdos_sync_infos"]:
                    pdos_infos[element] = "\n".join(pdos_infos[element])

                str_completion["pdos_configuration_declaration"] += SLAVE_PDOS_CONFIGURATION_DECLARATION % pdos_infos

            for (index, subindex), entry_declaration in slave_variables.iteritems():
                if not entry_declaration["mapped"]:
                    message = _("Entry index 0x{a1:.4x}, subindex 0x{a2:.2x} not mapped for device {a3}").\
                              format(a1=index, a2=subindex, a3=type_infos["device_type"])
                    self.Controler.GetCTRoot().logger.write_warning(_("Warning: ") + message + "\n")

        for element in ["used_pdo_entry_offset_variables_declaration",
                        "used_pdo_entry_configuration",
                        "located_variables_declaration",
                        "retrieve_variables",
                        "publish_variables"]:
            str_completion[element] = "\n".join(str_completion[element])

        etherlabfile = open(filepath, 'w')
        etherlabfile.write(plc_etherlab_code % str_completion)
        etherlabfile.close()
