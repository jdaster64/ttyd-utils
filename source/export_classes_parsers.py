#! /usr/bin/python3.6

"""Helper library used by export_classes.py.

Contains templates for parsing various types of structs from section dumps
of PM:TTYD (specifically the US version, if there are version differences)."""
# Jonathan Aldrich 2021-03-02 ~ 2021-03-04

import codecs
import numpy as np
import pandas as pd

import jdalibpy.bindatastore as bd

class ExportClassesParserError(Exception):
    def __init__(self, message=""):
        self.message = message
        
class FieldMetadata(object):
    def __init__(self, offset, name, datatype, bit=None):
        self.name = name
        self.offset = offset
        self.datatype = datatype
        self.bit = bit
        
class StructMetadata(object):
    def __init__(self, name, size, array, fields, substructs=None):
        self.name = name
        self.size = size
        self.array = array
        self.fields = fields
        self.substructs = substructs
        
# Special cases for arrays of structs (any other value = fixed-size array).
SINGLE_INSTANCE = 1
ZERO_TERMINATED = 0
UNKNOWN_LENGTH = -1
        
# TODO: Move this to a separate file / parse from a serialized format?
g_StructDefs = {
    "AudienceItemWeight": StructMetadata(
        "AudienceItemWeight", 0x8, array=ZERO_TERMINATED,
        fields=[
            FieldMetadata(0, "item_id", bd.BDType.U32),
            FieldMetadata(4, "weight", bd.BDType.S32),
        ]),
    "BattleGroupSetup": StructMetadata(
        "BattleGroupSetup", 0x20, array=SINGLE_INSTANCE,
        fields=[
            FieldMetadata(0x00, "num_enemies", bd.BDType.S32),
            FieldMetadata(0x04, "unit_data", bd.BDType.POINTER),
            FieldMetadata(0x08, "held_weight", bd.BDType.S32),
            FieldMetadata(0x0c, "random_weight", bd.BDType.S32),
            FieldMetadata(0x10, "none_weight", bd.BDType.S32),
            FieldMetadata(0x14, "hp_drop_table", bd.BDType.POINTER),
            FieldMetadata(0x18, "fp_drop_table", bd.BDType.POINTER),
            # 0x1c = unknown field
        ]),
    "BattleSetupData": StructMetadata(
        "BattleSetupData", 0x44, array=ZERO_TERMINATED,
        fields=[
            FieldMetadata(0x00, "battle_name", bd.BDType.CSTRING),
            FieldMetadata(0x04, "secondary_name", bd.BDType.CSTRING),
            # 0x08 = unknown field
            FieldMetadata(0x0c, "special_loadout_flag_id", bd.BDType.S32),
            FieldMetadata(0x10, "on_loadouts", bd.BDType.POINTER),
            FieldMetadata(0x14, "off_loadouts", bd.BDType.POINTER),
            FieldMetadata(0x18, "Flags_Unknown0", bd.BDType.U32, 0),
            FieldMetadata(0x18, "Flags_Unknown1", bd.BDType.U32, 1),
            FieldMetadata(0x18, "Flags_Unknown2", bd.BDType.U32, 2),
            FieldMetadata(0x18, "Flags_Unknown3", bd.BDType.U32, 3),
            FieldMetadata(0x18, "Flags_CannotFlee", bd.BDType.U32, 4),
            FieldMetadata(0x18, "Flags_AlternateMerleeRates", bd.BDType.U32, 5),
            FieldMetadata(0x18, "Flags_GrubbaConditions?", bd.BDType.U32, 6),
            FieldMetadata(0x18, "Flags_Unknown20", bd.BDType.U32, 20),
            FieldMetadata(0x18, "Flags_NoBumpAttack", bd.BDType.U32, 28),
            FieldMetadata(0x18, "Flags_Unknown29", bd.BDType.U32, 29),
            FieldMetadata(0x1c, "special_audience_type", bd.BDType.S32),
            FieldMetadata(0x20, "aud_min_wt_toad", bd.BDType.S8),
            FieldMetadata(0x21, "aud_max_wt_toad", bd.BDType.S8),
            FieldMetadata(0x22, "aud_min_wt_xnaut", bd.BDType.S8),
            FieldMetadata(0x23, "aud_max_wt_xnaut", bd.BDType.S8),
            FieldMetadata(0x24, "aud_min_wt_boo", bd.BDType.S8),
            FieldMetadata(0x25, "aud_max_wt_boo", bd.BDType.S8),
            FieldMetadata(0x26, "aud_min_wt_hammerbros", bd.BDType.S8),
            FieldMetadata(0x27, "aud_max_wt_hammerbros", bd.BDType.S8),
            FieldMetadata(0x28, "aud_min_wt_dullbones", bd.BDType.S8),
            FieldMetadata(0x29, "aud_max_wt_dullbones", bd.BDType.S8),
            FieldMetadata(0x2a, "aud_min_wt_shyguy", bd.BDType.S8),
            FieldMetadata(0x2b, "aud_max_wt_shyguy", bd.BDType.S8),
            FieldMetadata(0x2c, "aud_min_wt_dayzee", bd.BDType.S8),
            FieldMetadata(0x2d, "aud_max_wt_dayzee", bd.BDType.S8),
            FieldMetadata(0x2e, "aud_min_wt_puni", bd.BDType.S8),
            FieldMetadata(0x2f, "aud_max_wt_puni", bd.BDType.S8),
            FieldMetadata(0x30, "aud_min_wt_koopa", bd.BDType.S8),
            FieldMetadata(0x31, "aud_max_wt_koopa", bd.BDType.S8),
            FieldMetadata(0x32, "aud_min_wt_heavybomb", bd.BDType.S8),
            FieldMetadata(0x33, "aud_max_wt_heavybomb", bd.BDType.S8),
            FieldMetadata(0x34, "aud_min_wt_goomba", bd.BDType.S8),
            FieldMetadata(0x35, "aud_max_wt_goomba", bd.BDType.S8),
            FieldMetadata(0x36, "aud_min_wt_plant", bd.BDType.S8),
            FieldMetadata(0x37, "aud_max_wt_plant", bd.BDType.S8),
            FieldMetadata(0x38, "aud_min_wt_12", bd.BDType.S8),
            FieldMetadata(0x39, "aud_max_wt_12", bd.BDType.S8),
            FieldMetadata(0x3a, "aud_min_wt_13", bd.BDType.S8),
            FieldMetadata(0x3b, "aud_max_wt_13", bd.BDType.S8),
            FieldMetadata(0x3c, "aud_min_wt_14", bd.BDType.S8),
            FieldMetadata(0x3d, "aud_max_wt_14", bd.BDType.S8),
            FieldMetadata(0x3e, "aud_min_wt_15", bd.BDType.S8),
            FieldMetadata(0x3f, "aud_max_wt_15", bd.BDType.S8),
            FieldMetadata(0x40, "music_name", bd.BDType.CSTRING),
        ]),
    "BattleSetupNoTable": StructMetadata(
        "BattleSetupNoTable", 0x8, array=ZERO_TERMINATED,
        fields=[
            FieldMetadata(0, "btl_no_string", bd.BDType.CSTRING),
            FieldMetadata(4, "btl_no_id", bd.BDType.S32),
        ]),
    "BattleSetupWeightedLoadout": StructMetadata(
        "BattleSetupWeightedLoadout", 0xc, array=ZERO_TERMINATED,
        fields=[
            FieldMetadata(0, "weight", bd.BDType.S32),
            FieldMetadata(4, "group_setup_data", bd.BDType.POINTER),
            FieldMetadata(8, "stage_data", bd.BDType.POINTER),
        ]),
    "BattleStageData": StructMetadata(
        "BattleStageData", 0x1b4, array=UNKNOWN_LENGTH,
        fields=[
            FieldMetadata(0x000, "global_data_dir", bd.BDType.CSTRING),
            FieldMetadata(0x004, "current_data_dir", bd.BDType.CSTRING),
            FieldMetadata(0x008, "num_objects", bd.BDType.S32),
            FieldMetadata(0x00c, "objects", bd.BDType.POINTER),
            FieldMetadata(0x190, "init_evt", bd.BDType.POINTER),
            FieldMetadata(0x194, "destroy_a1_evt", bd.BDType.POINTER),
            FieldMetadata(0x198, "destroy_a2_evt", bd.BDType.POINTER),
            FieldMetadata(0x19c, "destroy_b_evt", bd.BDType.POINTER),
            FieldMetadata(0x1a0, "bg_a1_evt", bd.BDType.POINTER),
            FieldMetadata(0x1a4, "bg_a2_evt", bd.BDType.POINTER),
            FieldMetadata(0x1a8, "bg_b_scroll_evt", bd.BDType.POINTER),
            FieldMetadata(0x1ac, "bg_b_rotate_evt", bd.BDType.POINTER),
            FieldMetadata(0x1b0, "unk_1b0", bd.BDType.S8),
            FieldMetadata(0x1b1, "disallow_destroying_a1", bd.BDType.S8),
            FieldMetadata(0x1b2, "disallow_destroying_a2", bd.BDType.S8),
            FieldMetadata(0x1b3, "disallow_destroying_b", bd.BDType.S8),
        ],
        substructs = [
            FieldMetadata(0x010, "weapon_bg_a", "BattleWeapon"),
            FieldMetadata(0x0d0, "weapon_bg_b", "BattleWeapon"),
        ]),
    "BattleStageFallObjectData": StructMetadata(
        "BattleStageFallObjectData", 0x78c, array=4,
        fields=[
            FieldMetadata(0x0c0, "wt_basin", bd.BDType.S8),
            FieldMetadata(0x0c1, "wt_bucket", bd.BDType.S8),
            FieldMetadata(0x0c2, "wt_small_bugs", bd.BDType.S8),
            FieldMetadata(0x0c3, "wt_large_bug", bd.BDType.S8),
            FieldMetadata(0x0c4, "wt_fork", bd.BDType.S8),
            FieldMetadata(0x0c5, "wt_water", bd.BDType.S8),
            FieldMetadata(0x0c6, "wt_statue", bd.BDType.S8),
            FieldMetadata(0x0c7, "wt_meteor", bd.BDType.S8),
            FieldMetadata(0x0c8, "wt_stage_light", bd.BDType.S8),
        ],
        substructs = [
            FieldMetadata(0x000, "weapon_ceiling_fall", "BattleWeapon"),
            FieldMetadata(0x0cc, "weapon_basin", "BattleWeapon"),
            FieldMetadata(0x18c, "weapon_bucket", "BattleWeapon"),
            FieldMetadata(0x24c, "weapon_small_bugs", "BattleWeapon"),
            FieldMetadata(0x30c, "weapon_large_bug", "BattleWeapon"),
            FieldMetadata(0x3cc, "weapon_fork", "BattleWeapon"),
            FieldMetadata(0x48c, "weapon_water", "BattleWeapon"),
            FieldMetadata(0x54c, "weapon_statue", "BattleWeapon"),
            FieldMetadata(0x60c, "weapon_meteor", "BattleWeapon"),
            FieldMetadata(0x6cc, "weapon_stage_light", "BattleWeapon"),
        ]),
    "BattleStageNozzleData": StructMetadata(
        "BattleStageNozzleData", 0x310, array=4,
        fields=[
            FieldMetadata(0x0, "wt_turn_00", bd.BDType.S8),
            FieldMetadata(0x1, "wt_turn_01", bd.BDType.S8),
            FieldMetadata(0x2, "wt_turn_02", bd.BDType.S8),
            FieldMetadata(0x3, "wt_turn_03", bd.BDType.S8),
            FieldMetadata(0x4, "wt_turn_04", bd.BDType.S8),
            FieldMetadata(0x5, "wt_turn_05", bd.BDType.S8),
            FieldMetadata(0x6, "wt_turn_06", bd.BDType.S8),
            FieldMetadata(0x7, "wt_turn_07", bd.BDType.S8),
            FieldMetadata(0x8, "wt_turn_08", bd.BDType.S8),
            FieldMetadata(0x9, "wt_turn_09", bd.BDType.S8),
            FieldMetadata(0xa, "wt_turn_10", bd.BDType.S8),
            FieldMetadata(0xb, "wt_turn_11", bd.BDType.S8),
            FieldMetadata(0xc, "wt_fog", bd.BDType.S8),
            FieldMetadata(0xd, "wt_ice", bd.BDType.S8),
            FieldMetadata(0xe, "wt_explosion", bd.BDType.S8),
            FieldMetadata(0xf, "wt_fire", bd.BDType.S8),
        ],
        substructs = [
            FieldMetadata(0x010, "weapon_fog", "BattleWeapon"),
            FieldMetadata(0x0d0, "weapon_ice", "BattleWeapon"),
            FieldMetadata(0x190, "weapon_explosion", "BattleWeapon"),
            FieldMetadata(0x250, "weapon_fire", "BattleWeapon"),
        ]),
    "BattleUnitPoseTable": StructMetadata(
        "BattleUnitPoseTable", 0x8, array=UNKNOWN_LENGTH,
        fields=[
            FieldMetadata(0, "pose_id", bd.BDType.U32),
            FieldMetadata(4, "pose_name", bd.BDType.CSTRING),
        ]),
    "BattleStageObjectData": StructMetadata(
        "BattleStageObjectData", 0x18, array=UNKNOWN_LENGTH,
        fields=[
            FieldMetadata(0x00, "name", bd.BDType.CSTRING),
            FieldMetadata(0x04, "unk_04", bd.BDType.U16),
            FieldMetadata(0x06, "layer", bd.BDType.U16),
            FieldMetadata(0x08, "pos_x", bd.BDType.FLOAT),
            FieldMetadata(0x0c, "pos_y", bd.BDType.FLOAT),
            FieldMetadata(0x10, "pos_z", bd.BDType.FLOAT),
            FieldMetadata(0x14, "frames_to_start_falling", bd.BDType.U8),
            FieldMetadata(0x15, "frames_to_fall", bd.BDType.U8),
        ]),
    "BattleUnitDataTable": StructMetadata(
        "BattleUnitDataTable", 0x8, array=ZERO_TERMINATED,
        fields=[
            FieldMetadata(0, "key", bd.BDType.S32),
            FieldMetadata(4, "value", bd.BDType.POINTER),
        ]),
    "BattleUnitDefense": StructMetadata(
        "BattleUnitDefense", 0x5, array=SINGLE_INSTANCE,
        fields=[
            FieldMetadata(0, "normal", bd.BDType.S8),
            FieldMetadata(1, "fire", bd.BDType.S8),
            FieldMetadata(2, "ice", bd.BDType.S8),
            FieldMetadata(3, "explosion", bd.BDType.S8),
            FieldMetadata(4, "electric", bd.BDType.S8),
        ]),
    "BattleUnitDefenseAttr": StructMetadata(
        "BattleUnitDefenseAttr", 0x5, array=SINGLE_INSTANCE,
        fields=[
            FieldMetadata(0, "normal", bd.BDType.S8),
            FieldMetadata(1, "fire", bd.BDType.S8),
            FieldMetadata(2, "ice", bd.BDType.S8),
            FieldMetadata(3, "explosion", bd.BDType.S8),
            FieldMetadata(4, "electric", bd.BDType.S8),
        ]),
    "BattleUnitKind": StructMetadata(
        "BattleUnitKind", 0xc4, array=SINGLE_INSTANCE,
        fields=[
            FieldMetadata(0x00, "kind", bd.BDType.S32),
            FieldMetadata(0x04, "unit_name", bd.BDType.CSTRING),
            FieldMetadata(0x08, "max_hp", bd.BDType.S16),
            FieldMetadata(0x0a, "max_fp", bd.BDType.S16),
            FieldMetadata(0x0c, "danger_hp", bd.BDType.S8),
            FieldMetadata(0x0d, "peril_hp", bd.BDType.S8),
            FieldMetadata(0x0e, "level", bd.BDType.S8),
            FieldMetadata(0x0f, "bonus_exp", bd.BDType.S8),
            FieldMetadata(0x10, "bonus_coin", bd.BDType.S8),
            FieldMetadata(0x11, "bonus_coin_rate", bd.BDType.S8),
            FieldMetadata(0x12, "base_coin", bd.BDType.S8),
            FieldMetadata(0x13, "run_rate", bd.BDType.S8),
            FieldMetadata(0x14, "power_bounce_min_cap", bd.BDType.S16),
            FieldMetadata(0x16, "width", bd.BDType.S16),
            FieldMetadata(0x18, "height", bd.BDType.S16),
            FieldMetadata(0x1a, "hit_offset_x", bd.BDType.S16),
            FieldMetadata(0x1c, "hit_offset_y", bd.BDType.S16),
            FieldMetadata(0x20, "center_offset_x", bd.BDType.FLOAT),
            FieldMetadata(0x24, "center_offset_y", bd.BDType.FLOAT),
            FieldMetadata(0x28, "center_offset_z", bd.BDType.FLOAT),
            FieldMetadata(0x2c, "hp_gauge_offset_x", bd.BDType.S16),
            FieldMetadata(0x2e, "hp_gauge_offset_y", bd.BDType.S16),
            FieldMetadata(0x30, "talk_toge_base_offset_x", bd.BDType.FLOAT),
            FieldMetadata(0x34, "talk_toge_base_offset_y", bd.BDType.FLOAT),
            FieldMetadata(0x38, "talk_toge_base_offset_z", bd.BDType.FLOAT),
            FieldMetadata(0x3c, "held_item_base_offset_x", bd.BDType.FLOAT),
            FieldMetadata(0x40, "held_item_base_offset_y", bd.BDType.FLOAT),
            FieldMetadata(0x44, "held_item_base_offset_z", bd.BDType.FLOAT),
            FieldMetadata(0x48, "burn_flame_offset_x", bd.BDType.FLOAT),
            FieldMetadata(0x4c, "burn_flame_offset_y", bd.BDType.FLOAT),
            FieldMetadata(0x50, "burn_flame_offset_z", bd.BDType.FLOAT),
            FieldMetadata(0x54, "unk_54", bd.BDType.FLOAT),
            FieldMetadata(0x58, "unk_58", bd.BDType.FLOAT),
            FieldMetadata(0x5c, "love_slap_hit_offset_x", bd.BDType.FLOAT),
            FieldMetadata(0x60, "love_slap_hit_offset_y", bd.BDType.FLOAT),
            FieldMetadata(0x64, "love_slap_hit_offset_z", bd.BDType.FLOAT),
            FieldMetadata(0x68, "lip_lock_hit_offset_x", bd.BDType.FLOAT),
            FieldMetadata(0x6c, "lip_lock_hit_offset_y", bd.BDType.FLOAT),
            FieldMetadata(0x70, "lip_lock_hit_offset_z", bd.BDType.FLOAT),
            FieldMetadata(0x74, "art_attack_hit_offset_x", bd.BDType.FLOAT),
            FieldMetadata(0x78, "art_attack_hit_offset_y", bd.BDType.FLOAT),
            FieldMetadata(0x7c, "art_attack_hit_offset_z", bd.BDType.FLOAT),
            FieldMetadata(0x80, "art_attack_width", bd.BDType.FLOAT),
            FieldMetadata(0x84, "art_attack_height", bd.BDType.FLOAT),
            FieldMetadata(0x88, "turn_order", bd.BDType.S8),
            FieldMetadata(0x89, "turn_order_variance", bd.BDType.S8),
            FieldMetadata(0x8a, "swallow_chance", bd.BDType.S8),
            FieldMetadata(0x8b, "swallow_attributes", bd.BDType.S8),
            FieldMetadata(0x8c, "ultra_hammer_knock_chance", bd.BDType.S8),
            FieldMetadata(0x8d, "itemsteal_param", bd.BDType.S8),
            FieldMetadata(0x90, "star_point_disp_offset_x", bd.BDType.FLOAT),
            FieldMetadata(0x94, "star_point_disp_offset_y", bd.BDType.FLOAT),
            FieldMetadata(0x98, "star_point_disp_offset_z", bd.BDType.FLOAT),
            FieldMetadata(0x9c, "damaged_sfx_name", bd.BDType.CSTRING),
            FieldMetadata(0xa0, "fire_damage_sfx_name", bd.BDType.CSTRING),
            FieldMetadata(0xa4, "ice_damage_sfx_name", bd.BDType.CSTRING),
            FieldMetadata(0xa8, "explosion_damage_sfx_name", bd.BDType.CSTRING),
            FieldMetadata(0xac, "UA_Unknown0", bd.BDType.U32, 0),
            FieldMetadata(0xac, "UA_NotReachable", bd.BDType.U32, 1),
            FieldMetadata(0xac, "UA_NonGrounded", bd.BDType.U32, 2),
            FieldMetadata(0xac, "UA_AllMissableAttacksMiss?", bd.BDType.U32, 3),
            FieldMetadata(0xac, "UA_Veiled", bd.BDType.U32, 4),
            FieldMetadata(0xac, "UA_ShellShielded", bd.BDType.U32, 5),
            FieldMetadata(0xac, "UA_Unknown12", bd.BDType.U32, 12),
            FieldMetadata(0xac, "UA_Unknown13", bd.BDType.U32, 13),
            FieldMetadata(0xac, "UA_Inactive?", bd.BDType.U32, 17),
            FieldMetadata(0xac, "UA_Unknown21", bd.BDType.U32, 21),
            FieldMetadata(0xac, "UA_NoDamageDealt?", bd.BDType.U32, 30),
            FieldMetadata(0xb0, "status_vulnerability", bd.BDType.POINTER),
            FieldMetadata(0xb4, "num_parts", bd.BDType.S8),
            FieldMetadata(0xb8, "parts", bd.BDType.POINTER),
            FieldMetadata(0xbc, "init_evt", bd.BDType.POINTER),
            FieldMetadata(0xc0, "data_table", bd.BDType.POINTER),
        ]),
    "BattleUnitKindPart": StructMetadata(
        "BattleUnitKindPart", 0x4c, array=UNKNOWN_LENGTH,
        fields=[
            FieldMetadata(0x00, "index", bd.BDType.S32),
            FieldMetadata(0x04, "name", bd.BDType.S8),
            FieldMetadata(0x08, "model_name", bd.BDType.S32),
            FieldMetadata(0x0c, "part_offset_pos_x", bd.BDType.FLOAT),
            FieldMetadata(0x10, "part_offset_pos_y", bd.BDType.FLOAT),
            FieldMetadata(0x14, "part_offset_pos_z", bd.BDType.FLOAT),
            FieldMetadata(0x18, "hit_base_offset_x", bd.BDType.FLOAT),
            FieldMetadata(0x1c, "hit_base_offset_y", bd.BDType.FLOAT),
            FieldMetadata(0x20, "hit_base_offset_z", bd.BDType.FLOAT),
            FieldMetadata(0x24, "hit_cursor_base_offset_x", bd.BDType.FLOAT),
            FieldMetadata(0x28, "hit_cursor_base_offset_y", bd.BDType.FLOAT),
            FieldMetadata(0x2c, "hit_cursor_base_offset_z", bd.BDType.FLOAT),
            FieldMetadata(0x30, "unk_30", bd.BDType.S16),
            FieldMetadata(0x32, "unk_32", bd.BDType.S16),
            FieldMetadata(0x34, "base_alpha", bd.BDType.S16),
            FieldMetadata(0x38, "defense", bd.BDType.POINTER),
            FieldMetadata(0x3c, "defense_attr", bd.BDType.POINTER),
            FieldMetadata(0x40, "PA_MainTarget", bd.BDType.U32, 0),
            FieldMetadata(0x40, "PA_PreferredSelectTarget", bd.BDType.U32, 1),
            FieldMetadata(0x40, "PA_SelectTarget", bd.BDType.U32, 2),
            FieldMetadata(0x40, "PA_Unknown3", bd.BDType.U32, 3),
            FieldMetadata(0x40, "PA_IgnoreSelectTarget?", bd.BDType.U32, 4),
            FieldMetadata(0x40, "PA_Unknown5", bd.BDType.U32, 6),
            FieldMetadata(0x40, "PA_WeakToAttackFxR", bd.BDType.U32, 7),
            FieldMetadata(0x40, "PA_WeakToIcePower", bd.BDType.U32, 8),
            FieldMetadata(0x40, "PA_IsWinged", bd.BDType.U32, 11),
            FieldMetadata(0x40, "PA_IsShelled", bd.BDType.U32, 12),
            FieldMetadata(0x40, "PA_IsBombFlippable", bd.BDType.U32, 13),
            FieldMetadata(0x40, "PA_IgnorePreferredTarget?", bd.BDType.U32, 14),
            FieldMetadata(0x40, "PA_NonTargetable", bd.BDType.U32, 16),
            FieldMetadata(0x40, "PA_Unknown18", bd.BDType.U32, 18),
            FieldMetadata(0x40, "PA_Untattleable", bd.BDType.U32, 19),
            FieldMetadata(0x40, "PA_JumplikeCannotTarget", bd.BDType.U32, 20),
            FieldMetadata(0x40, "PA_HammerlikeCannotTarget", bd.BDType.U32, 21),
            FieldMetadata(0x40, "PA_ShellTosslikeCannotTarget", bd.BDType.U32, 22),
            FieldMetadata(0x40, "PA_NoDamageDealt", bd.BDType.U32, 23),
            FieldMetadata(0x40, "PA_IsImmuneToDamageOrStatus?", bd.BDType.U32, 29),
            FieldMetadata(0x40, "PA_IsImmuneToOHKO?", bd.BDType.U32, 30),
            FieldMetadata(0x40, "PA_IsImmuneToStatus?", bd.BDType.U32, 31),
            FieldMetadata(0x44, "PCA_TopSpiky", bd.BDType.U32, 0),
            FieldMetadata(0x44, "PCA_PreemptiveFrontSpiky", bd.BDType.U32, 1),
            FieldMetadata(0x44, "PCA_FrontSpiky", bd.BDType.U32, 2),
            FieldMetadata(0x44, "PCA_Fiery", bd.BDType.U32, 4),
            FieldMetadata(0x44, "PCA_FieryStatus", bd.BDType.U32, 5),
            FieldMetadata(0x44, "PCA_Icy", bd.BDType.U32, 6),
            FieldMetadata(0x44, "PCA_IcyStatus", bd.BDType.U32, 7),
            FieldMetadata(0x44, "PCA_Poison", bd.BDType.U32, 8),
            FieldMetadata(0x44, "PCA_PoisonStatus", bd.BDType.U32, 9),
            FieldMetadata(0x44, "PCA_Electric", bd.BDType.U32, 10),
            FieldMetadata(0x44, "PCA_ElectricStatus", bd.BDType.U32, 11),
            FieldMetadata(0x44, "PCA_Explosive", bd.BDType.U32, 12),
            FieldMetadata(0x44, "PCA_VolatileExplosive", bd.BDType.U32, 13),
            FieldMetadata(0x48, "pose_table", bd.BDType.POINTER),
        ]),
    "BattleUnitPoseTable": StructMetadata(
        "BattleUnitPoseTable", 0x8, array=ZERO_TERMINATED,
        fields=[
            FieldMetadata(0, "pose_id", bd.BDType.S32),
            FieldMetadata(4, "pose_name", bd.BDType.CSTRING),
        ]),
    "BattleUnitSetup": StructMetadata(
        "BattleUnitSetup", 0x30, array=UNKNOWN_LENGTH,
        fields=[
            FieldMetadata(0x00, "unit_kind", bd.BDType.POINTER),
            FieldMetadata(0x04, "alliance", bd.BDType.S8),
            FieldMetadata(0x08, "attack_phase", bd.BDType.S32),
            FieldMetadata(0x0c, "pos_x", bd.BDType.FLOAT),
            FieldMetadata(0x10, "pos_y", bd.BDType.FLOAT),
            FieldMetadata(0x14, "pos_z", bd.BDType.FLOAT),
            FieldMetadata(0x18, "target_x_offset", bd.BDType.U32),
            FieldMetadata(0x1c, "unit_work_0", bd.BDType.U32),
            FieldMetadata(0x20, "unit_work_1", bd.BDType.U32),
            FieldMetadata(0x24, "unit_work_2", bd.BDType.U32),
            FieldMetadata(0x28, "unit_work_3", bd.BDType.U32),
            FieldMetadata(0x2c, "drop_table", bd.BDType.POINTER),
        ]),
    "BattleWeapon": StructMetadata(
        "BattleWeapon", 0xc0, array=SINGLE_INSTANCE,
        fields=[
            FieldMetadata(0x00, "name_msg", bd.BDType.CSTRING),
            FieldMetadata(0x04, "icon", bd.BDType.U16),
            FieldMetadata(0x08, "item_id", bd.BDType.U32),
            FieldMetadata(0x0c, "desc_msg", bd.BDType.CSTRING),
            FieldMetadata(0x10, "base_accuracy", bd.BDType.U8),
            FieldMetadata(0x11, "base_fp_cost", bd.BDType.U8),
            FieldMetadata(0x12, "base_sp_cost", bd.BDType.U8),
            FieldMetadata(0x13, "superguard_state", bd.BDType.U8),
            # 0x14 - unknown float
            FieldMetadata(0x18, "stylish_multiplier", bd.BDType.U8),
            # 0x19 - unknown int8
            FieldMetadata(0x1a, "bingo_slot_inc_chance", bd.BDType.U8),
            # 0x1b - unknown int8
            FieldMetadata(0x1c, "base_damage_fn", bd.BDType.POINTER),
            FieldMetadata(0x20, "base_damage_param0", bd.BDType.S32),
            FieldMetadata(0x24, "base_damage_param1", bd.BDType.S32),
            FieldMetadata(0x28, "base_damage_param2", bd.BDType.S32),
            FieldMetadata(0x2c, "base_damage_param3", bd.BDType.S32),
            FieldMetadata(0x30, "base_damage_param4", bd.BDType.S32),
            FieldMetadata(0x34, "base_damage_param5", bd.BDType.S32),
            FieldMetadata(0x38, "base_damage_param6", bd.BDType.S32),
            FieldMetadata(0x3c, "base_damage_param7", bd.BDType.S32),
            FieldMetadata(0x40, "base_fp_damage_fn", bd.BDType.POINTER),
            FieldMetadata(0x44, "base_fp_damage_param0", bd.BDType.S32),
            FieldMetadata(0x48, "base_fp_damage_param1", bd.BDType.S32),
            FieldMetadata(0x4c, "base_fp_damage_param2", bd.BDType.S32),
            FieldMetadata(0x50, "base_fp_damage_param3", bd.BDType.S32),
            FieldMetadata(0x54, "base_fp_damage_param4", bd.BDType.S32),
            FieldMetadata(0x58, "base_fp_damage_param5", bd.BDType.S32),
            FieldMetadata(0x5c, "base_fp_damage_param6", bd.BDType.S32),
            FieldMetadata(0x60, "base_fp_damage_param7", bd.BDType.S32),
            FieldMetadata(0x64, "TC_CannotTargetMarioOrShellShield", bd.BDType.U32, 0),
            FieldMetadata(0x64, "TC_CannotTargetPartner", bd.BDType.U32, 1),
            FieldMetadata(0x64, "TC_CannotTargetEnemy", bd.BDType.U32, 4),
            FieldMetadata(0x64, "TC_CannotTargetTreeOrSwitch", bd.BDType.U32, 5),
            FieldMetadata(0x64, "TC_CannotTargetSystemUnits", bd.BDType.U32, 6),
            FieldMetadata(0x64, "TC_CannotTargetOppositeAlliance", bd.BDType.U32, 8),
            FieldMetadata(0x64, "TC_CannotTargetOwnAlliance", bd.BDType.U32, 9),
            FieldMetadata(0x64, "TC_CannotTargetSelf", bd.BDType.U32, 12),
            FieldMetadata(0x64, "TC_CannotTargetSameSpecies", bd.BDType.U32, 13),
            FieldMetadata(0x64, "TC_OnlyTargetSelf", bd.BDType.U32, 14),
            FieldMetadata(0x64, "TC_OnlyTargetPreferredParts", bd.BDType.U32, 20),
            FieldMetadata(0x64, "TC_OnlyTargetSelectParts", bd.BDType.U32, 21),
            FieldMetadata(0x64, "TC_SingleTarget", bd.BDType.U32, 24),
            FieldMetadata(0x64, "TC_MultipleTarget", bd.BDType.U32, 25),
            FieldMetadata(0x68, "TP_Tattleable", bd.BDType.U32, 0),
            FieldMetadata(0x68, "TP_Unknown1", bd.BDType.U32, 1),
            FieldMetadata(0x68, "TP_CannotTargetCeiling", bd.BDType.U32, 2),
            FieldMetadata(0x68, "TP_CannotTargetFloating", bd.BDType.U32, 3),
            FieldMetadata(0x68, "TP_CannotTargetGrounded", bd.BDType.U32, 4),
            FieldMetadata(0x68, "TP_Jumplike", bd.BDType.U32, 12),
            FieldMetadata(0x68, "TP_Hammerlike", bd.BDType.U32, 13),
            FieldMetadata(0x68, "TP_ShellTosslike", bd.BDType.U32, 14),
            FieldMetadata(0x68, "TP_Unknown15", bd.BDType.U32, 15),
            FieldMetadata(0x68, "TP_RecoilDamage", bd.BDType.U32, 20),
            FieldMetadata(0x68, "TP_CanOnlyTargetFrontmost", bd.BDType.U32, 24),
            FieldMetadata(0x68, "TP_Unknown25", bd.BDType.U32, 25),
            FieldMetadata(0x68, "TP_Unknown26", bd.BDType.U32, 26),
            FieldMetadata(0x68, "TP_TargetSameAllianceDirection", bd.BDType.U32, 28),
            FieldMetadata(0x68, "TP_TargetOppositeAllianceDirection", bd.BDType.U32, 29),
            FieldMetadata(0x6c, "element", bd.BDType.U8),
            FieldMetadata(0x6d, "damage_pattern", bd.BDType.U8),
            FieldMetadata(0x6e, "weapon_ac_level", bd.BDType.U8),
            # 0x6f - unknown int8
            FieldMetadata(0x70, "ac_message", bd.BDType.CSTRING),
            FieldMetadata(0x74, "SP_BadgeCanAffectPower", bd.BDType.U32, 0),
            FieldMetadata(0x74, "SP_StatusCanAffectPower", bd.BDType.U32, 1),
            FieldMetadata(0x74, "SP_IsChargeable", bd.BDType.U32, 2),
            FieldMetadata(0x74, "SP_CannotMiss", bd.BDType.U32, 3),
            FieldMetadata(0x74, "SP_DiminishingReturnsByHit", bd.BDType.U32, 4),
            FieldMetadata(0x74, "SP_DiminishingReturnsByTarget", bd.BDType.U32, 5),
            FieldMetadata(0x74, "SP_PiercesDefense", bd.BDType.U32, 6),
            FieldMetadata(0x74, "SP_CanBreakIce", bd.BDType.U32, 7),
            FieldMetadata(0x74, "SP_IgnoreTargetStatusVulnerability", bd.BDType.U32, 8),
            FieldMetadata(0x74, "SP_Unknown9", bd.BDType.U32, 9),
            FieldMetadata(0x74, "SP_IgnitesIfBurned", bd.BDType.U32, 10),
            FieldMetadata(0x74, "SP_FlipsShellEnemies", bd.BDType.U32, 12),
            FieldMetadata(0x74, "SP_FlipsBombFlippableEnemies", bd.BDType.U32, 13),
            FieldMetadata(0x74, "SP_GroundsWingedEnemies", bd.BDType.U32, 14),
            FieldMetadata(0x74, "SP_CanUseItemIfConfused", bd.BDType.U32, 16),
            FieldMetadata(0x74, "SP_Unguardable", bd.BDType.U32, 17),
            FieldMetadata(0x78, "CR_Electric", bd.BDType.U32, 0),
            FieldMetadata(0x78, "CR_TopSpiky", bd.BDType.U32, 1),
            FieldMetadata(0x78, "CR_PreemptiveFrontSpiky", bd.BDType.U32, 2),
            FieldMetadata(0x78, "CR_FrontSpiky", bd.BDType.U32, 3),
            FieldMetadata(0x78, "CR_Fiery", bd.BDType.U32, 4),
            FieldMetadata(0x78, "CR_Icy", bd.BDType.U32, 5),
            FieldMetadata(0x78, "CR_Poison", bd.BDType.U32, 6),
            FieldMetadata(0x78, "CR_Explosive", bd.BDType.U32, 7),
            FieldMetadata(0x78, "CR_VolatileExplosive", bd.BDType.U32, 8),
            FieldMetadata(0x78, "CR_Payback", bd.BDType.U32, 9),
            FieldMetadata(0x78, "CR_HoldFast", bd.BDType.U32, 10),
            FieldMetadata(0x7c, "TW_PreferMario", bd.BDType.U32, 0),
            FieldMetadata(0x7c, "TW_PreferPartner", bd.BDType.U32, 1),
            FieldMetadata(0x7c, "TW_PreferFront", bd.BDType.U32, 2),
            FieldMetadata(0x7c, "TW_PreferBack", bd.BDType.U32, 3),
            FieldMetadata(0x7c, "TW_PreferSameAlliance", bd.BDType.U32, 4),
            FieldMetadata(0x7c, "TW_PreferOppositeAlliance", bd.BDType.U32, 5),
            FieldMetadata(0x7c, "TW_PreferLessHealthy", bd.BDType.U32, 8),
            FieldMetadata(0x7c, "TW_GreatlyPreferLessHealthy", bd.BDType.U32, 9),
            FieldMetadata(0x7c, "TW_PreferLowerHP", bd.BDType.U32, 10),
            FieldMetadata(0x7c, "TW_PreferHigherHP", bd.BDType.U32, 11),
            FieldMetadata(0x7c, "TW_PreferInPeril", bd.BDType.U32, 12),
            FieldMetadata(0x7c, "TW_Unknown13", bd.BDType.U32, 13),
            FieldMetadata(0x7c, "TW_ChooseWeightedRandomly", bd.BDType.U32, 31),
            FieldMetadata(0x80, "sleep_chance", bd.BDType.S8),
            FieldMetadata(0x81, "sleep_time", bd.BDType.S8),
            FieldMetadata(0x82, "stop_chance", bd.BDType.S8),
            FieldMetadata(0x83, "stop_time", bd.BDType.S8),
            FieldMetadata(0x84, "dizzy_chance", bd.BDType.S8),
            FieldMetadata(0x85, "dizzy_time", bd.BDType.S8),
            FieldMetadata(0x86, "poison_chance", bd.BDType.S8),
            FieldMetadata(0x87, "poison_time", bd.BDType.S8),
            FieldMetadata(0x88, "poison_strength", bd.BDType.S8),
            FieldMetadata(0x89, "confuse_chance", bd.BDType.S8),
            FieldMetadata(0x8a, "confuse_time", bd.BDType.S8),
            FieldMetadata(0x8b, "electric_chance", bd.BDType.S8),
            FieldMetadata(0x8c, "electric_time", bd.BDType.S8),
            FieldMetadata(0x8d, "dodgy_chance", bd.BDType.S8),
            FieldMetadata(0x8e, "dodgy_time", bd.BDType.S8),
            FieldMetadata(0x8f, "burn_chance", bd.BDType.S8),
            FieldMetadata(0x90, "burn_time", bd.BDType.S8),
            FieldMetadata(0x91, "freeze_chance", bd.BDType.S8),
            FieldMetadata(0x92, "freeze_time", bd.BDType.S8),
            FieldMetadata(0x93, "size_change_change", bd.BDType.S8),
            FieldMetadata(0x94, "size_change_time", bd.BDType.S8),
            FieldMetadata(0x95, "size_change_strength", bd.BDType.S8),
            FieldMetadata(0x96, "atk_change_chance", bd.BDType.S8),
            FieldMetadata(0x97, "atk_change_time", bd.BDType.S8),
            FieldMetadata(0x98, "atk_change_strength", bd.BDType.S8),
            FieldMetadata(0x99, "def_change_chance", bd.BDType.S8),
            FieldMetadata(0x9a, "def_change_time", bd.BDType.S8),
            FieldMetadata(0x9b, "def_change_strength", bd.BDType.S8),
            FieldMetadata(0x9c, "allergic_chance", bd.BDType.S8),
            FieldMetadata(0x9d, "allergic_time", bd.BDType.S8),
            FieldMetadata(0x9e, "ohko_chance", bd.BDType.S8),
            FieldMetadata(0x9f, "charge_strength", bd.BDType.S8),
            FieldMetadata(0xa0, "fast_chance", bd.BDType.S8),
            FieldMetadata(0xa1, "fast_time", bd.BDType.S8),
            FieldMetadata(0xa2, "slow_chance", bd.BDType.S8),
            FieldMetadata(0xa3, "slow_time", bd.BDType.S8),
            FieldMetadata(0xa4, "fright_chance", bd.BDType.S8),
            FieldMetadata(0xa5, "gale_force_chance", bd.BDType.S8),
            FieldMetadata(0xa6, "payback_time", bd.BDType.S8),
            FieldMetadata(0xa7, "hold_fast_time", bd.BDType.S8),
            FieldMetadata(0xa8, "invisible_chance", bd.BDType.S8),
            FieldMetadata(0xa9, "invisible_time", bd.BDType.S8),
            FieldMetadata(0xaa, "hp_regen_time", bd.BDType.S8),
            FieldMetadata(0xab, "hp_regen_strength", bd.BDType.S8),
            FieldMetadata(0xac, "fp_regen_time", bd.BDType.S8),
            FieldMetadata(0xad, "fp_regen_strength", bd.BDType.S8),
            FieldMetadata(0xb0, "attack_evt", bd.BDType.POINTER),
            FieldMetadata(0xb4, "bg_a1_a2_fall_weight", bd.BDType.S8),
            FieldMetadata(0xb5, "bg_a1_fall_weight", bd.BDType.S8),
            FieldMetadata(0xb6, "bg_a2_fall_weight", bd.BDType.S8),
            FieldMetadata(0xb7, "bg_a_no_fall_weight", bd.BDType.S8),
            FieldMetadata(0xb8, "bg_b_fall_chance", bd.BDType.S8),
            FieldMetadata(0xb9, "nozzle_turn_chance", bd.BDType.S8),
            FieldMetadata(0xba, "nozzle_fire_chance", bd.BDType.S8),
            FieldMetadata(0xbb, "ceiling_fall_chance", bd.BDType.S8),
            FieldMetadata(0xbc, "object_fall_chance", bd.BDType.S8),
            FieldMetadata(0xbd, "unk_stage_hazard_chance", bd.BDType.S8),
        ]),
    "CookingRecipe": StructMetadata(
        "CookingRecipe", 0xc, array=UNKNOWN_LENGTH,
        fields=[
            FieldMetadata(0, "ingredient_1_id", bd.BDType.CSTRING),
            FieldMetadata(4, "ingredient_2_id", bd.BDType.CSTRING),
            FieldMetadata(8, "result_id", bd.BDType.CSTRING),
        ]),
    "ItemData": StructMetadata(
        "ItemData", 0x28, array=ZERO_TERMINATED,
        fields=[
            FieldMetadata(0x00, "id", bd.BDType.CSTRING),
            FieldMetadata(0x04, "name", bd.BDType.CSTRING),
            FieldMetadata(0x08, "desc", bd.BDType.CSTRING),
            FieldMetadata(0x0c, "menu_desc", bd.BDType.CSTRING),
            FieldMetadata(0x10, "UseLocation_Shop", bd.BDType.U16, 0),
            FieldMetadata(0x10, "UseLocation_Battle", bd.BDType.U16, 1),
            FieldMetadata(0x10, "UseLocation_Field", bd.BDType.U16, 2),
            FieldMetadata(0x12, "type_sort_order", bd.BDType.S16),
            FieldMetadata(0x14, "buy_price", bd.BDType.S16),
            FieldMetadata(0x16, "discount_price", bd.BDType.S16),
            FieldMetadata(0x18, "star_piece_price", bd.BDType.S16),
            FieldMetadata(0x1a, "sell_price", bd.BDType.S16),
            FieldMetadata(0x1c, "bp_cost", bd.BDType.S8),
            FieldMetadata(0x1d, "hp_restored", bd.BDType.S8),
            FieldMetadata(0x1e, "fp_restored", bd.BDType.S8),
            FieldMetadata(0x1f, "sp_restored", bd.BDType.S8),
            FieldMetadata(0x20, "icon", bd.BDType.U16),
            FieldMetadata(0x24, "weapon", bd.BDType.POINTER),
        ]),
    "ItemDropData": StructMetadata(
        "ItemDropData", 0x8, array=ZERO_TERMINATED,
        fields=[
            FieldMetadata(0, "item_id", bd.BDType.S32),
            FieldMetadata(4, "hold_weight", bd.BDType.S16),
            FieldMetadata(6, "drop_weight", bd.BDType.S16),
        ]),
    "NpcAiTypeTable": StructMetadata(
        "NpcAiTypeTable", 0x24, array=ZERO_TERMINATED,
        fields=[
            FieldMetadata(0x00, "ai_type_name", bd.BDType.CSTRING),
            FieldMetadata(0x04, "flags", bd.BDType.U32),
            FieldMetadata(0x08, "init_event", bd.BDType.POINTER),
            FieldMetadata(0x0c, "move_event", bd.BDType.POINTER),
            FieldMetadata(0x10, "dead_event", bd.BDType.POINTER),
            FieldMetadata(0x14, "find_event", bd.BDType.POINTER),
            FieldMetadata(0x18, "lost_event", bd.BDType.POINTER),
            FieldMetadata(0x1c, "return_event", bd.BDType.POINTER),
            FieldMetadata(0x20, "blow_event", bd.BDType.POINTER),
        ]),
    "PointDropData": StructMetadata(
        "PointDropData", 0x10, array=5,
        fields=[
            FieldMetadata(0x00, "max_stat_percent", bd.BDType.S32),
            FieldMetadata(0x04, "overall_drop_rate", bd.BDType.S32),
            FieldMetadata(0x08, "drop_count", bd.BDType.S32),
            FieldMetadata(0x0c, "individual_drop_rate", bd.BDType.S32),
        ]),
    "ShopItemTable": StructMetadata(
        "ShopItemTable", 0x8, array=6,
        fields=[
            FieldMetadata(0, "item_id", bd.BDType.S32),
            FieldMetadata(4, "buy_price", bd.BDType.S32),
        ]),
    "ShopSellPriceList": StructMetadata(
        "ShopSellPriceList", 0x8, array=ZERO_TERMINATED,
        fields=[
            FieldMetadata(0, "item_id", bd.BDType.S32),
            FieldMetadata(4, "sell_price", bd.BDType.S16),
        ]),
    "StatusVulnerability": StructMetadata(
        "StatusVulnerability", 0x16, array=SINGLE_INSTANCE,
        fields=[
            FieldMetadata(0x00, "sleep", bd.BDType.U8),
            FieldMetadata(0x01, "stop", bd.BDType.U8),
            FieldMetadata(0x02, "dizzy", bd.BDType.U8),
            FieldMetadata(0x03, "poison", bd.BDType.U8),
            FieldMetadata(0x04, "confuse", bd.BDType.U8),
            FieldMetadata(0x05, "electric", bd.BDType.U8),
            FieldMetadata(0x06, "burn", bd.BDType.U8),
            FieldMetadata(0x07, "freeze", bd.BDType.U8),
            FieldMetadata(0x08, "huge", bd.BDType.U8),
            FieldMetadata(0x09, "tiny", bd.BDType.U8),
            FieldMetadata(0x0a, "attack_up", bd.BDType.U8),
            FieldMetadata(0x0b, "attack_down", bd.BDType.U8),
            FieldMetadata(0x0c, "defense_up", bd.BDType.U8),
            FieldMetadata(0x0d, "defense_down", bd.BDType.U8),
            FieldMetadata(0x0e, "allergic", bd.BDType.U8),
            FieldMetadata(0x0f, "fright", bd.BDType.U8),
            FieldMetadata(0x10, "gale_force", bd.BDType.U8),
            FieldMetadata(0x11, "fast", bd.BDType.U8),
            FieldMetadata(0x12, "slow", bd.BDType.U8),
            FieldMetadata(0x13, "dodgy", bd.BDType.U8),
            FieldMetadata(0x14, "invisible", bd.BDType.U8),
            FieldMetadata(0x15, "ohko", bd.BDType.U8),
        ]),
}

def GetStructDefs():
    return g_StructDefs
    
def ParseClass(view, symbol, symbol_table=None):
    """Given symbol metadata and a BDView, returns the symbol's salient fields.
    
    Args:
    - view (bd.BDView) - A view offset to the start of the symbol's data.
    - symbol (series) - A single dataframe row containing the following columns:
      area, name, namespace, address (as integer, in RAM), type (class name).
    - symbol_table (df) - Optional; dataframe containing the following columns:
      index [area, address], name, namespace. If provided, will attempt to match
      pointer fields with their respective symbols.
    Returns:
    - A dataframe with a single row, and the columns: area, name, namespace,
      address (as hex string) and the fields of the corresponding class type."""
    struct_def = g_StructDefs[symbol["type"]]
    columns = ["area", "name", "namespace", "address"]
    data = [symbol["area"], symbol["name"], symbol["namespace"],
        "%08x" % symbol["address"]]

    for field in struct_def.fields:
        columns.append(field.name)
        if field.datatype == bd.BDType.CSTRING:
            # String types need to be indirected (const char*) and decoded.
            if view.rptr(field.offset) == 0:
                value = "<NULL>"
            else:
                try:
                    str_view = view.indirect(field.offset)
                    value = codecs.decode(str_view.rcstring(), "shift-jis")
                except:
                    raise ExportClassesParserError(
                        'Error parsing field "%s" in %s %s %s.' %
                        (field.name, symbol["area"], symbol["name"],
                         symbol["namespace"]))
        else:
            # Otherwise, read the value per the specified field type.
            value = view.read(field.datatype, field.offset)
        
        # Bitfield types: get the boolean value of a particular bit.
        if field.bit is not None:
            value = 1 if value & (1 << field.bit) else 0
            
        # Pointer types: get the name of symbol pointed to if possible.
        if field.datatype == bd.BDType.POINTER:
            if symbol_table is not None:
                # Try to look up the symbol in its corresponding area.
                try:
                    ref = symbol_table.loc[(symbol["area"], value)]
                    value = "%s %s" % (ref["name"], ref["namespace"])
                except:
                    # Not found, try to look up the symbol in _main.
                    try:
                        ref = symbol_table.loc[("_main", value)]
                        value = "%s %s" % (ref["name"], ref["namespace"])
                    except:
                        # Still not found, just convert address to hex.
                        value = "%08x" % value
            else:
                value = "%08x" % value
            
        data.append(value)
        
    return pd.DataFrame([data], columns=columns)
    
def ParseClassRawBytes(view, symbol):
    """Given symbol metadata and a BDView, returns the symbol's binary data.
    
    Args:
    - view (bd.BDView) - A view offset to the start of the symbol's data.
    - symbol (series) - A single dataframe row containing the following columns:
      area, name, namespace, address (as integer, in RAM), type (class name).
    Returns:
    - A dataframe with a single row, and the columns: area, name, namespace,
      address (as hex string) and one column per raw byte of the class."""
    struct_def = g_StructDefs[symbol["type"]]
    columns = ["area", "name", "namespace", "address"]
    data = [symbol["area"], symbol["name"], symbol["namespace"],
        "%08x" % symbol["address"]]
    
    # Append each byte of the object's data in hex one at a time.
    for x in range(struct_def.size):
        columns.append(("%02x" if struct_def.size <= 256 else "%03x") % x)
        data.append("%02x" % view.ru8(x))
        
    return pd.DataFrame([data], columns=columns)
