#! /usr/bin/python3.4

"""Exports labeled or raw data of various class types from TTYD dumps."""
# Jonathan "jdaster64" Aldrich 2019-09-30 ~ 2019-10-12

import codecs
import os
import sys
import numpy as np
import pandas as pd

import jdalibpy.bindump as bindump
import jdalibpy.flags as flags
import ttyd_maplib as maplib

FLAGS = flags.Flags()
# Filepath to a file in the format of REPO/resources/ttyd_*_symboldiffs_*.csv.
FLAGS.DefineString("input_diffs", "")
# Filepattern matching RAM dumps from every area in the game, named by their
# internal area code (e.g. "aji" = X-Naut fortress), with the area replaced with
# the wildcard *; Example: "path/to/file/*.raw"
FLAGS.DefineString("input_ram_pattern", "")
# Directory to output all script text files to.
FLAGS.DefineString("output_dir", "")
# Toggles whether to output formatted data or the raw bytes of the class.
FLAGS.DefineBool("use_raw_classes", False)

# Text files with enemy and item IDs and names.
FLAGS.DefineString("enemies", "../resources/enemy_names.txt")
FLAGS.DefineString("items", "../resources/item_names.txt")

g_DatabufMap = {}

# Arrays of constant-ish data used to identify items, enemies, etc.
k_MaxItemId = 0x153
g_EnemyIds = []
g_ItemIds = []

# Maps of flag values to flag names for various bitfields.
g_AttackTargetClassFlags = {
    0x1: "TC_CannotTargetMarioOrShellShield",
    0x2: "TC_CannotTargetPartner",
    0x10: "TC_CannotTargetEnemy",
    0x20: "TC_CannotTargetTreeOrSwitch",
    0x40: "TC_CannotTargetSystemUnits",
    0x100: "TC_CannotTargetOppositeAlliance",
    0x200: "TC_CannotTargetOwnAlliance",
    0x1000: "TC_CannotTargetSelf",
    0x2000: "TC_OnlyTargetSelfOrSameSpecies",
    0x4000: "TC_OnlyTargetSelf",
    0x100000: "TC_OnlyTargetHighPriorityParts",
    0x200000: "TC_OnlyTargetPriorityParts",
    0x1000000: "TC_SingleTarget",
    0x2000000: "TC_MultipleTarget",
}
g_AttackTargetPropertyFlags = {
    0x1: "TP_Tattleable",
    0x4: "TP_CannotTargetCeiling",
    0x8: "TP_CannotTargetFloating",
    0x10: "TP_CannotTargetGround",
    0x1000: "TP_Jumplike",
    0x2000: "TP_Hammerlike",
    0x4000: "TP_ShellTosslike",
    0x100000: "TP_RecoilDamage",
    0x1000000: "TP_CanOnlyTargetFrontmost",
    0x10000000: "TP_UsedOnSelfOrAlliesOnly?",
    0x20000000: "TP_UsableOnOpposingTeam?",
}
g_AttackSpecialPropertyFlags = {
    0x1: "SP_BadgeCanAffectPower",
    0x2: "SP_StatusCanAffectPower",
    0x4: "SP_IsChargeable",
    0x8: "SP_CannotMiss",
    0x10: "SP_DiminishingReturnsByHit",
    0x20: "SP_DiminishingReturnsByTarget",
    0x40: "SP_PiercesDefense",
    0x80: "SP_UnusedCanBreakIce?",
    0x100: "SP_IgnoreTargetStatusVulnerability",
    0x200: "SP_UnknownGaleForceOnly?",
    0x400: "SP_IgnitesIfBurned",
    0x1000: "SP_FlipsShellEnemies",
    0x2000: "SP_FlipsBombFlippableEnemies",
    0x4000: "SP_GroundsWingedEnemies",
    0x10000: "SP_CanUseItemIfConfused?",
    0x20000: "SP_Unguardable?",
}
g_AttackCounterResistanceFlags = {
    0x1: "CR_Electric",
    0x2: "CR_TopSpiky",
    0x4: "CR_PreemptiveFrontSpiky",
    0x8: "CR_FrontSpiky",
    0x10: "CR_Fiery",
    0x20: "CR_Icy",
    0x40: "CR_Poison",
    0x80: "CR_Explosive",
    0x100: "CR_VolatileExplosive",
    0x200: "CR_Payback",
    0x400: "CR_HoldFast",
}
g_AttackTargetWeightingFlags = {
    0x1: "TW_PreferMario",
    0x2: "TW_PreferPartner",
    0x4: "TW_PreferFront",
    0x8: "TW_PreferBack",
    0x10: "TW_PreferSameAlliance",
    0x20: "TW_PreferSameAllianceButNot2",
    0x100: "TW_PreferLessHealthy",
    0x200: "TW_GreatlyPreferLessHealthy",
    0x400: "TW_PreferLowerHP",
    0x800: "TW_PreferHigherHP",
    0x1000: "TW_PreferInPeril",
    0x2000: "TW_NoEffect0x2000?",
    0x80000000: "TW_ChooseWeightedRandomly",
}
g_UnitPartsAttributeFlags = {
    0x1: "PA_HighestPriorityTarget",
    0x2: "PA_HighPriorityTarget",
    0x4: "PA_PriorityTarget",
    0x10: "PA_NonPriorityTarget0x10",
    0x80: "PA_WeakToAttackFxR",
    0x100: "PA_WeakToIcePower",
    0x800: "PA_IsWinged",
    0x1000: "PA_IsShelled",
    0x2000: "PA_IsBombFlippable",
    0x4000: "PA_NonPriorityTarget0x4000",
    0x10000: "PA_NeverTargetable",
    0x80000: "PA_Untattleable",
    0x100000: "PA_JumplikeCannotTarget",
    0x200000: "PA_HammerlikeCannotTarget",
    0x400000: "PA_ShellTosslikeCannotTarget",
    0x800000: "PA_Unknown0x800000",
    0x20000000: "PA_IsImmuneToDamageOrStatus",
    0x40000000: "PA_IsImmuneToOHKO",
    0x80000000: "PA_IsImmuneToStatus",
}
g_UnitPartsCounterAttributeFlags = {
    0x1: "PCA_TopSpiky",
    0x2: "PCA_PreemptiveFrontSpiky",
    0x4: "PCA_FrontSpiky",
    0x10: "PCA_Fiery",
    0x20: "PCA_FieryStatus",
    0x40: "PCA_Icy",
    0x80: "PCA_IcyStatus",
    0x100: "PCA_Poison",
    0x200: "PCA_PoisonStatus",
    0x400: "PCA_Electric",
    0x800: "PCA_ElectricStatus",
    0x1000: "PCA_Explosive",
    0x2000: "PCA_VolatileExplosive",
}

class ExtractClassDataError(Exception):
    def __init__(self, message=""):
        self.message = message
        
def _GetEnemyIds():
    if FLAGS.HasFlag("enemies"):
        lines = open(FLAGS.GetFlag("enemies")).readlines()
        for s in lines:
            g_EnemyIds.append(s[:-1])
    else:
        # Add numbers to array so there's SOMETHING to print
        for x in range(0x100):
            g_EnemyIds.append("Enemy %X" % (x,))
    # Add placeholder names for later actors if not present.
    while len(g_EnemyIds) < 0x100:
        g_EnemyIds.append("Actor %X" % (len(g_EnemyIds),))
        
def _GetItemIds():
    if FLAGS.HasFlag("items"):
        lines = open(FLAGS.GetFlag("items")).readlines()
        for s in lines:
            g_ItemIds.append(s[6:-1])
    else:
        # Add numbers to array so there's SOMETHING to print.
        for x in range(k_MaxItemId):
            g_ItemIds.append("Item %X" % (x,))
            
# Helper function for parsing bitfields.
def _ParseFlagAttributes(dat, address, attr_map):
    attribute_flags = dat.read_u32(address)
    attributes = []
    for (mask, flag_name) in attr_map.items():
        if attribute_flags & mask:
            attributes.append(flag_name)
    return "|".join(attributes)
            
# Alternative helper function for parsing bitfields.
def _ParseFlagAttributesIndividually(
    row, dat=None, address=None, attr_map=None, header=False):
    for (mask, flag_name) in attr_map.items():
        if header:
            row.append(flag_name)
        else:
            attribute_flags = dat.read_u32(address)
            row.append("X" if (attribute_flags & mask) != 0 else "")
        
# Helper function for parsing strings.
def _ParseJisString(dat, address):
    char_ptr = dat.read_u32(address)
    if char_ptr:
        return dat.read_cstring(address, [0]).decode("shift-jis")
    else:
        return "<NULL>"
        
def _ParseAttackParams(df, row, area="", address=0, header=False):
    if header:
        for colname in [
            "Name Key", "Icon?", "Associated Item", "Base Accuracy",
            "Base FP Cost", "Base SP Cost", "Superguardable",
            "Stylish Multiplier", "Bingo Slot Chance", "Damage Function",
            "Damage Param1", "Damage Param2", "Damage Param3", "Damage Param4",
            "Damage Param5", "Damage Param6", "Damage Param7", "Damage Param8",
            "FP Damage Function", "FP Damage Param1", "FP Damage Param2",
            "FP Damage Param3", "FP Damage Param4", "FP Damage Param5",
            "FP Damage Param6", "FP Damage Param7", "FP Damage Param8",
            "Element", "After-Hit Effect", "Weapon AC Level", "AC Message Key",
            "Attack Script",
            # Status effect parameters.
            "Sleep Chance", "Sleep Time",
            "Stop Chance", "Stop Time", "Dizzy Chance", "Dizzy Time",
            "Poison Chance", "Poison Time", "Poison Strength", "Confuse Chance",
            "Confuse Time", "Electric Chance", "Electric Time", "Dodgy Chance",
            "Dodgy Time", "Burn Chance", "Burn Time", "Freeze Chance",
            "Freeze Time", "Size Change Chance", "Size Change Time",
            "Size Change Strength", "ATK Change Chance", "ATK Change Time",
            "ATK Change Strength", "DEF Change Chance", "DEF Change Time",
            "DEF Change Strength", "Allergic Chance", "Allergic Time",
            "OHKO Chance", "Charge Strength", "Fast Chance", "Fast Time",
            "Slow Chance", "Slow Time", "Fright Chance", "Gale Force Chance",
            "Payback Time", "Hold Fast Time", "Invisible Chance",
            "Invisible Time", "HP-Regen Time", "HP-Regen Strength",
            "FP-Regen Time", "FP-Regen Strength",
            # Stage hazard parameters.
            "BG A1+A2 Fall Weight", "BG A1 Fall Weight", "BG A2 Fall Weight",
            "BG No A1-A2 Fall Weight", "BG B Fall Chance", "Nozzle Turn Chance",
            "Nozzle Fire Chance", "Ceiling Fall Chance", "Object Fall Chance",
            "Unknown Stage Hazard Chance",
        ]:
            row.append(colname)
            
        # Headers for bitfield flags.
        _ParseFlagAttributesIndividually(
            row, attr_map=g_AttackTargetClassFlags, header=True)
        _ParseFlagAttributesIndividually(
            row, attr_map=g_AttackTargetPropertyFlags, header=True)
        _ParseFlagAttributesIndividually(
            row, attr_map=g_AttackSpecialPropertyFlags, header=True)
        _ParseFlagAttributesIndividually(
            row, attr_map=g_AttackCounterResistanceFlags, header=True)
        _ParseFlagAttributesIndividually(
            row, attr_map=g_AttackTargetWeightingFlags, header=True)
    else:
        # For diagnostics.
        print("%s 0x%08x" % (area, address))
        
        dat = g_DatabufMap[area]
        row.append(_ParseJisString(dat, address + 0x0))
        row.append(hex(dat.read_u16(address + 0x4)))
        row.append(g_ItemIds[dat.read_s32(address + 0x8)])
        row.append(dat.read_u8(address + 0x10))
        row.append(dat.read_u8(address + 0x11))
        row.append(dat.read_u8(address + 0x12))
        row.append("Yes" if dat.read_u8(address + 0x13) else "No")
        row.append(dat.read_u8(address + 0x18))
        row.append(dat.read_u8(address + 0x1a))
        if dat.read_u32(address + 0x1c):
            row.append(maplib.LookupSymbolName(
                df, area, dat.read_u32(address + 0x1c)))
        else:
            row.append("NULL")
        for idx in range(0x20, 0x40, 4):
            row.append(dat.read_s32(address + idx))
        if dat.read_u32(address + 0x40):
            row.append(maplib.LookupSymbolName(
                df, area, dat.read_u32(address + 0x40)))
        else:
            row.append("NULL")
        for idx in range(0x44, 0x64, 4):
            row.append(dat.read_s32(address + idx))
        element_types = ["Normal", "Fire", "Ice", "Explosion", "Electric"]
        row.append(element_types[dat.read_u8(address + 0x6c)])
        row.append(hex(dat.read_u8(address + 0x6d)))
        row.append(dat.read_u8(address + 0x6e))
        row.append(_ParseJisString(dat, address + 0x70))
        if dat.read_u32(address + 0xb0):
            row.append(maplib.LookupSymbolName(
                df, area, dat.read_u32(address + 0xb0), "EventScript_t"))
        else:
            row.append("NULL")
        # Status effect parameters.
        for idx in range(0x80, 0xae):
            row.append(dat.read_s8(address + idx))
        # Stage hazard parameters.
        for idx in range(0xb4, 0xbe):
            row.append(dat.read_s8(address + idx))
        # Bitfield flags.
        _ParseFlagAttributesIndividually(
            row, dat, address + 0x64, g_AttackTargetClassFlags)
        _ParseFlagAttributesIndividually(
            row, dat, address + 0x68, g_AttackTargetPropertyFlags)
        _ParseFlagAttributesIndividually(
            row, dat, address + 0x74, g_AttackSpecialPropertyFlags)
        _ParseFlagAttributesIndividually(
            row, dat, address + 0x78, g_AttackCounterResistanceFlags)
        _ParseFlagAttributesIndividually(
            row, dat, address + 0x7c, g_AttackTargetWeightingFlags)
        
def _ParseAudienceItemTable(df, row, area="", address=0, header=False):
    if header:
        for idx in range(1,17):
            row.append("Item %d" % (idx,))
            row.append("Weight")
    else:
        dat = g_DatabufMap[area]
        while True:
            item_id = dat.read_s32(address + 0)
            weight = dat.read_s32(address + 4)
            if item_id == 0:
                break
            row.append(g_ItemIds[item_id])
            row.append(weight)
            address += 8
            
def _ParseBattleParty(df, row, area="", address=0, header=False):
    if header:
        for colname in [
            "Num Units", "Unit Entry Data", "Held Weight", "Random Weight",
            "None Weight", "HP Drop Table", "FP Drop Table", "Unknown"
        ]:
            row.append(colname)
    else:
        dat = g_DatabufMap[area]
        row.append(dat.read_u32(address + 0))
        row.append(maplib.LookupSymbolName(
            df, area, dat.read_u32(address + 4), "BattleUnitEntry_t"))
        row.append(dat.read_u32(address + 0x8))
        row.append(dat.read_u32(address + 0xc))
        row.append(dat.read_u32(address + 0x10))
        row.append(maplib.LookupSymbolName(
            df, area, dat.read_u32(address + 0x14), "PointDropWeights_t"))
        row.append(maplib.LookupSymbolName(
            df, area, dat.read_u32(address + 0x18), "PointDropWeights_t"))
        row.append(hex(dat.read_u32(address + 0x1c)))
            
def _ParseBattlePartyWeights(df, row, area="", address=0, header=False):
    if header:
        for colname in [
            "Weight", "Party Data", "Stage Data"
        ]:
            row.append(colname)
    else:
        dat = g_DatabufMap[area]
        row.append(dat.read_u32(address + 0))
        row.append(maplib.LookupSymbolName(
            df, area, dat.read_u32(address + 4), "BattleLoadoutParams_t"))
        row.append(maplib.LookupSymbolName(
            df, area, dat.read_u32(address + 8), "BattleStageData_t"))
        
def _ParseBattleSetup(df, row, area="", address=0, header=False):
    if header:
        for colname in [
            "Battle Name", "Secondary Name", "Music Name", "Default Loadouts",
            "Loadout Flag", "Alternate Loadouts", "Max Audience",
            "Toad", "X-Naut", "Boo", "Hammer Bro", "Dull Bones", "Shy Guy",
            "Dayzee", "Puni", "Koopa", "Bulky Bob-omb", "Goomba", "Piranha Plant"
        ]:
            row.append(colname)
    else:
        dat = g_DatabufMap[area]
        row.append(_ParseJisString(dat, address + 0))
        row.append(_ParseJisString(dat, address + 4))
        row.append(_ParseJisString(dat, address + 0x40))
        row.append(maplib.LookupSymbolName(
            df, area, dat.read_u32(address + 0x14), "BattleWeightedLoadout_t"))
            
        flag_id = dat.read_s32(address + 0xc)
        if flag_id == -1 or flag_id == 0:
            row.append(""); row.append("")
        else:
            row.append(hex(flag_id + 130000000))
            row.append(maplib.LookupSymbolName(
                df, area, dat.read_u32(address + 0x10),
                "BattleWeightedLoadout_t"))
                
        row.append(dat.read_s32(address + 0x1c) > 0)        
        for x in range(12):
            low_aud_weight = dat.read_s8(address + 0x20 + x*2)
            high_aud_weight = dat.read_s8(address + 0x21 + x*2)
            if low_aud_weight == high_aud_weight:
                row.append(low_aud_weight)
            else:
                row.append("%d-%d" % (low_aud_weight, high_aud_weight))
                
def _ParseBattleStageData(df, row, area="", address=0, header=False):
    if header:
        for colname in [
            "Global Stage Data Dir", "Specific Stage Data Dir",
            "A1 Layer", "A2 Layer", "B Layer", "Ceiling", "Init Event",
            "A1 Event", "A2 Event", "B Event", "Unknown Event 1",
            "Unknown Event 2", "Scroll Event", "Rotate Event", "Unknown Bools"
        ]:
            row.append(colname)
    else:
        dat = g_DatabufMap[area]
        row.append(_ParseJisString(dat, address + 0))
        row.append(_ParseJisString(dat, address + 4))
        # Summarize what background layers exist and which actors are targets.
        target_types = ["None", "Party", "Enemies", "All"]
        a1_targets, b_targets = 3, 3
        a1, a2, b, ceiling = "None", "None", "None", "None"
        if dat.read_u32(address + 0x10 + 0x1c) != 0:
            targets = dat.read_u32(address + 0x10 + 0x64)
            if targets & 0xf:
                a1_targets &= ~1
            if targets & 0x10:
                a1_targets &= ~2
        if dat.read_u32(address + 0xd0 + 0x1c) != 0:
            targets = dat.read_u32(address + 0xd0 + 0x64)
            if targets & 0xf:
                b_targets &= ~1
            if targets & 0x10:
                b_targets &= ~2
        for idx in range(dat.read_u32(address + 0x8)):
            obj_address = dat.read_u32(address + 0xc) + idx * 0x18
            obj_layer = dat.read_s16(obj_address + 0x6)
            if obj_layer == 0:
                a1 = target_types[a1_targets]
            elif obj_layer == 1:
                a2 = "Yes"
            elif obj_layer == 2:
                b = target_types[b_targets]
            elif obj_layer == 6:
                ceiling = "Yes"
        row.append(a1); row.append(a2); row.append(b); row.append(ceiling)
        # Store event info, etc. (Probably not too important).
        for idx in range(8):
            row.append(maplib.LookupSymbolName(
                df, area, dat.read_u32(address + 0x190 + idx * 4), 
                "EventScript_t"))
        row.append(hex(dat.read_u32(address + 0x1b0)))
        
def _ParseBattleUnit(df, row, area="", address=0, header=False):
    if header:
        for colname in [
            "Id", "Enemy Name", "Name Key", "Max HP", "Max FP", "Danger HP",
            "Peril HP", "Level", "Bonus EXP", "Bonus Coin", "Bonus Coin Rate",
            "Base Coin", "Run Rate", "PB Minimum Cap", "Turn Order",
            "Turn Order Variance", "Swallowable", "Ultra Hammer Knock Chance",
            "Kiss Thief Threshold", "Default Attributes",
            "Default Status Vuln.", "Parts", "Init Script", "Data Table",
        ]:
            row.append(colname)
    else:
        dat = g_DatabufMap[area]
        row.append("0x%02x" % (dat.read_u32(address + 0x0),))
        row.append(g_EnemyIds[dat.read_u32(address + 0x0)])
        row.append(_ParseJisString(dat, address + 0x4))
        row.append(dat.read_u16(address + 0x8))
        row.append(dat.read_u16(address + 0xa))
        row.append(dat.read_u8(address + 0xc))
        row.append(dat.read_u8(address + 0xd))
        row.append(dat.read_u8(address + 0xe))
        row.append(dat.read_u8(address + 0xf))
        row.append(dat.read_u8(address + 0x10))
        row.append(dat.read_u8(address + 0x11))
        row.append(dat.read_u8(address + 0x12))
        row.append(dat.read_u8(address + 0x13))
        row.append(dat.read_u16(address + 0x14))
        row.append(dat.read_u8(address + 0x88))
        row.append(dat.read_u8(address + 0x89))
        row.append("Yes" if dat.read_u8(address + 0x8a) == 0 else "No")
        row.append(dat.read_u8(address + 0x8c))
        row.append(dat.read_u8(address + 0x8d))
        # Parse default BattleUnitAttribute flags.
        row.append(_ParseFlagAttributes(dat, address + 0xac, {
            0x2: "Ceiling",
            0x4: "Floating",
        }))
        row.append(maplib.LookupSymbolName(
            df, area, dat.read_u32(address + 0xb0),
            "BattleUnitStatusVulnerability_t"))
        row.append(maplib.LookupSymbolName(
            df, area, dat.read_u32(address + 0xb8), "BattleUnitParts_t"))
        row.append(maplib.LookupSymbolName(
            df, area, dat.read_u32(address + 0xbc), "EventScript_t"))
        row.append(maplib.LookupSymbolName(
            df, area, dat.read_u32(address + 0xc0), "BattleUnitDataTable_t"))
        
def _ParseBattleUnitDefense(df, row, area="", address=0, header=False):
    if header:
        for colname in ["Normal", "Fire", "Ice", "Explosion", "Electric"]:
            row.append(colname)
    else:
        dat = g_DatabufMap[area]
        for x in range(5):
            row.append(dat.read_s8(address + x))
        
def _ParseBattleUnitEntry(df, row, area="", address=0, header=False):
    if header:
        for colname in [
            "Unit Type", "Item Table", "X Pos", "Y Pos", "Z Pos",
            "Attack Phase", "Alliance", "Alternate Form"
        ]:
            row.append(colname)
    else:
        dat = g_DatabufMap[area]
        row.append(maplib.LookupSymbolName(
            df, area, dat.read_u32(address + 0x0), "BattleUnitParams_t"))
        row.append(maplib.LookupSymbolName(
            df, area, dat.read_u32(address + 0x2c), "ItemDropWeight_t"))
        row.append(dat.read_float(address + 0xc))
        row.append(dat.read_float(address + 0x10))
        row.append(dat.read_float(address + 0x14))
        row.append(hex(dat.read_u32(address + 0x8)))
        row.append(dat.read_u8(address + 0x4))
        row.append(dat.read_u8(address + 0x1f))
        
def _ParseBattleUnitParts(df, row, area="", address=0, header=False):
    if header:
        for colname in [
            "Index", "Name", "Model Name", "Default Def", "Default Def Attr.",
            "Default Pose Table",
        ]:
            row.append(colname)
            
        # Headers for bitfield flags.
        _ParseFlagAttributesIndividually(
            row, attr_map=g_UnitPartsAttributeFlags, header=True)
        _ParseFlagAttributesIndividually(
            row, attr_map=g_UnitPartsCounterAttributeFlags, header=True)
    else:
        dat = g_DatabufMap[area]
        row.append(hex(dat.read_u32(address + 0x0)))
        row.append(_ParseJisString(dat, address + 0x4))
        row.append(_ParseJisString(dat, address + 0x8))
        row.append(maplib.LookupSymbolName(
            df, area, dat.read_u32(address + 0x38), "BattleUnitDefense_t"))
        row.append(maplib.LookupSymbolName(
            df, area, dat.read_u32(address + 0x3c), "BattleUnitDefenseAttr_t"))
        row.append(maplib.LookupSymbolName(
            df, area, dat.read_u32(address + 0x48), "BattleUnitPoseTable_t"))
        # Bitfield flags.
        _ParseFlagAttributesIndividually(
            row, dat, address + 0x40, g_UnitPartsAttributeFlags)
        _ParseFlagAttributesIndividually(
            row, dat, address + 0x44, g_UnitPartsCounterAttributeFlags)
        
def _ParseItemParams(df, row, area="", address=0, header=False):
    if header:
        for colname in [
            "Item Id", "Name Key", "Description Key", "Menu Description Key",
            "Locations Usable", "Type Sort Order", "Buy Price",
            "Discount Buy Price", "Star Piece Price", "Sell Price",
            "BP Cost", "HP Restored", "FP Restored", "Icon ID", "Attack Params"
        ]:
            row.append(colname)
    else:
        dat = g_DatabufMap[area]
        row.append(_ParseJisString(dat, address + 0))
        row.append(_ParseJisString(dat, address + 4))
        row.append(_ParseJisString(dat, address + 8))
        row.append(_ParseJisString(dat, address + 0xc))
        location_flags = dat.read_s16(address + 0x10)
        locations = []
        if location_flags & 1:
            locations.append("Shop")
        if location_flags & 2:
            locations.append("Battle")
        if location_flags & 4:
            locations.append("Field")
        row.append("|".join(locations))
        row.append(dat.read_s16(address + 0x12))
        row.append(dat.read_s16(address + 0x14))
        row.append(dat.read_s16(address + 0x16))
        row.append(dat.read_s16(address + 0x18))
        row.append(dat.read_s16(address + 0x1a))
        row.append(dat.read_u8(address + 0x1c))
        row.append(dat.read_u8(address + 0x1d))
        row.append(dat.read_u8(address + 0x1e))
        row.append(hex(dat.read_u16(address + 0x20)))
        row.append(maplib.LookupSymbolName(
            df, area, dat.read_u32(address + 0x24), "AttackParams_t"))
        
            
def _ParseItemDropTable(df, row, area="", address=0, header=False):
    if header:
        for idx in range(1,9):
            for colname in ["Item %d", "Hold %d", "Drop %d"]:
                row.append(colname % (idx,))
    else:
        dat = g_DatabufMap[area]
        while True:
            item_id = dat.read_s32(address + 0)
            hold_rate = dat.read_s16(address + 4)
            drop_rate = dat.read_s16(address + 6)
            if item_id == 0 and drop_rate == 0:
                break
            row.append(g_ItemIds[item_id])
            row.append(hold_rate)
            row.append(drop_rate)
            address += 8
        
def _ParseStatusVulnerability(df, row, area="", address=0, header=False):
    if header:
        for colname in [
            "Sleep", "Stop", "Dizzy", "Poison", "Confuse", "Electric", "Burn",
            "Freeze", "Huge", "Tiny", "Attack Up", "Attack Down", "Defense Up",
            "Defense Down", "Allergic", "Fright", "Gale Force", "Fast", "Slow",
            "Dodgy", "Invisible", "OHKO"
        ]:
            row.append(colname)
    else:
        dat = g_DatabufMap[area]
        for x in range(0x16):
            row.append(dat.read_u8(address + x))
            
def _ParseRawBytesOfClass(df, class_size, row, area="", address=0, header=False):
    if header:
        for x in range(class_size):
            row.append(("%02x" if class_size < 256 else "%03x") % (x,))
    else:
        dat = g_DatabufMap[area]
        for x in range(class_size):
            row.append("%02x" % (dat.read_u8(address + x),))
            
def _ParseAdditionalAttackParams(df, rows, parsing_func):
    for idx, df_row in df.loc[df["class"] == "BattleStageData_t"].iterrows():
        class_size = maplib.GetClassSize("BattleStageData_t")
        array_len = df_row["length"] // class_size
        for array_idx in range(array_len):
            area = df_row["area"]
            address = df_row["address"] + array_idx * class_size
            fullname = df_row["fullname"] + "_%02x" % (array_idx,)
            for (offset, sub_attack_name) in {
                0x10: "background_A_weapon",
                0xd0: "background_B_weapon",
            }.items():
                row = []
                row.append("%s %s" % (fullname, sub_attack_name))
                row.append(area)
                row.append(hex(address + offset))
                parsing_func(df, row, area, address + offset)
                rows.append(row)
        
    for idx, df_row in df.loc[
        df["fullname"] == "battle_stage_nozzle_data battle_stage_object.o"
    ].iterrows():
        area = df_row["area"]
        address = df_row["address"]
        for (offset, sub_attack_name) in {
            0x10: "fog_weapon",
            0xd0: "ice_jets_weapon",
            0x190: "explosion_jets_weapon",
            0x250: "fire_jets_weapon",
        }.items():
            for stage_rank in range(4):
                row = []
                row.append("%s_rank_%d" % (sub_attack_name, stage_rank))
                row.append(area)
                params_address = address + offset + stage_rank * 0x310
                row.append(hex(params_address))
                parsing_func(df, row, area, params_address)
                rows.append(row)
        
    for idx, df_row in df.loc[
        df["fullname"] == "battle_stage_fall_object_data battle_stage_object.o"
    ].iterrows():
        area = df_row["area"]
        address = df_row["address"]
        for (offset, sub_attack_name) in {
            0x0: "ceiling_beam_weapon",
            0xcc: "basin_weapon",
            0x18c: "bucket_weapon",
            0x24c: "small_bugs_weapon",
            0x30c: "large_bug_weapon",
            0x3cc: "fork_weapon",
            0x48c: "water_weapon",
            0x54c: "statue_weapon",
            0x60c: "meteor_weapon",
            0x6cc: "stage_light_weapon",
        }.items():
            for stage_rank in range(4):
                row = []
                row.append("%s_rank_%d" % (sub_attack_name, stage_rank))
                row.append(area)
                params_address = address + offset + stage_rank * 0x78c
                row.append(hex(params_address))
                parsing_func(df, row, area, params_address)
                rows.append(row)

def _ParseClassInstances(df, classname, parsing_func, is_array):
    """
    Creates a .CSV containing data parsed from all mapped instances of a
    given class, delegating class-specific implementation to a functor.

    This will not find instances nested in other types of structs unless they
    are separately named symbols; e.g. AttackParams in battle_stage_nozzle_data.
    """
    rows = [["Name", "Area", "Address"]]
    parsing_func(df, rows[0], header=True)
    
    for idx, df_row in df.loc[df["class"] == classname].iterrows():
        class_size = maplib.GetClassSize(classname)
        array_len = 1
        if is_array:
            array_len = df_row["length"] // class_size
        for array_idx in range(array_len):
            row = []
            area = df_row["area"]
            address = df_row["address"]
            if is_array:
                address += array_idx * class_size
                str_idx = ("_%03x" if array_len > 255 else "_%02x") % array_idx
                row.append(df_row["fullname"] + str_idx)
            else:
                row.append(df_row["fullname"])
            row.append(area)
            row.append(hex(address))
            # Run class-specific parser.
            parsing_func(df, row, area, address)
            rows.append(row)
    
    # For attacks specifically, parse stage hazard attacks from other places.
    if classname == "AttackParams_t":
        _ParseAdditionalAttackParams(df, rows, parsing_func)
            
    outfile = codecs.open(
        os.path.join(FLAGS.GetFlag("output_dir"), classname + ".csv"), 
        "w", encoding="utf-8")
    for row in rows:
        outfile.write("%s\n" % ",".join([str(val) for val in row]))
    outfile.flush()
            
def main(argc, argv):
    if not FLAGS.GetFlag("input_diffs"):
        raise ExtractClassDataError("No input diffs CSV provided.")
    if not FLAGS.GetFlag("input_ram_pattern"):
        raise ExtractClassDataError("No input ram filepattern provided.")
    if not FLAGS.GetFlag("output_dir"):
        raise ExtractClassDataError("No directory provided for output CSVs.")
        
    _GetEnemyIds(); _GetItemIds()
        
    # Get a DataFrame of symbol information from the input diffs file.
    df = maplib.GetSymbolInfoFromDiffsCsv(FLAGS.GetFlag("input_diffs"))
    # Sort by area and address for debugging convenience's sake.
    df.sort_values(["area", "address"], kind="mergesort", inplace=True)
        
    # Read binary dumps into BinDump objects.
    for area in df.area.unique():
        area_name = area
        if area == "_MS":
            area_name = "tik"  # Load arbitrary area for the main executable
        dump_fpath = FLAGS.GetFlag("input_ram_pattern").replace("*", area_name)
        if os.path.exists(dump_fpath):
            g_DatabufMap[area] = bindump.BinaryDump(big_endian=True)
            g_DatabufMap[area].register_file(dump_fpath, 0x80000000)
    
    # TODO: Implement parsing functions for any other interesting types.
    parsing_func_map = {
        "AttackParams_t": [_ParseAttackParams, False],
        "AudienceItemWeight_t": [_ParseAudienceItemTable, False],
        "BattleLoadoutParams_t": [_ParseBattleParty, True],
        "BattleObjectData_t": [None, None],
        "BattleSetup_t": [_ParseBattleSetup, True],
        "BattleStageData_t": [_ParseBattleStageData, True],
        "BattleUnitDefense_t": [_ParseBattleUnitDefense, False],
        "BattleUnitDefenseAttr_t": [_ParseBattleUnitDefense, False],
        "BattleUnitEntry_t": [_ParseBattleUnitEntry, True],
        "BattleUnitParams_t": [_ParseBattleUnit, False],
        "BattleUnitParts_t": [_ParseBattleUnitParts, True],
        "BattleUnitStatusVulnerability_t": [_ParseStatusVulnerability, False],
        "BattleWeightedLoadout_t": [_ParseBattlePartyWeights, True],
        "ItemData_t": [_ParseItemParams, True],
        "ItemDropWeight_t": [_ParseItemDropTable, False],
        "ShopItemList_t": [None, None],
        "ShopSellPriceList_t": [None, None],
    }
    if not FLAGS.GetFlag("use_raw_classes"):
        for classname, value in parsing_func_map.items():
            if value[0]:
                print("Exporting instances of class %s" % (classname,))
                _ParseClassInstances(df, classname, value[0], value[1])
    else:
        # Add an additional "class size" parameter into the parser signature.
        GetRawParseFunc = (
            lambda size:
                lambda df, row, area="", address=0, header=False:
                    _ParseRawBytesOfClass(df, size, row, area, address, header))
        for classname, value in parsing_func_map.items():
            class_size = maplib.GetClassSize(classname)
            if class_size > 0:
                print("Exporting raw instances of class %s" % (classname,))
                _ParseClassInstances(
                    df, classname, GetRawParseFunc(class_size), True)

if __name__ == "__main__":
    (argc, argv) = FLAGS.ParseFlags(sys.argv[1:])
    main(argc, argv)