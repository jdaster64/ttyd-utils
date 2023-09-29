import os
import shutil
import sys

if len(sys.argv) < 2:
    print("Usage: python3 ./sort_events_by_prefix.py [directory]")
    sys.exit(1)

path_to_files = os.path.abspath(sys.argv[1])

# Define your dictionary
prefix_subdirs = {
    "_main_battle": [
        "attack_audience", "audience_msg", "break_slot", "event_default", "event_subset", "item_data",
        "mario_marioAttackEvent", "mario", "seq_end", "stage_object"
    ],
    "_main_eff": [],
    "_main_evt": [
        "bero", "damage_evt", "door", "kinopio", "lecture_evt", "map_evt",
        "memcard_evt", "mobj_evt", "mobj_kpa", "movefloor", "npc", "shop", "sub_evt",
        "sub_mail",
    ],
    "_main_mot": [],
    "_main_npc": [
        "event_barriern", "event_basabasa", "event_bubble", "event_chorobon", "event_dokan2D", "event_dougassu",
        "event_enemy", "event_fall2D", "event_gesso2D", "event_hannya", "event_hbom", "event_hbross",
        "event_honenoko", "event_kamec", "event_kamec2", "event_karon", "event_killer", "event_kuriboo2D",
        "event_kuriboo", "event_mahoon", "event_met", "event_nokonoko", "event_npc", "event_pakkun", 
        "event_pansy", "event_patakuri", "event_patamet", "event_piders", "event_patapata", "event_sambo",
        "event_sinemon", "event_sinnosuke", "event_teresa", "event_testenemynpc", "event_togedaruma", "event_togemet",
        "event_togenoko", "event_twinkling_pansy", "event_unk", "event_wanwan", "event_zako2D", "event_zakoM2D",
        "event_zakowiz", "event_basabasa2", "event_dokugassun", "event_honenoko2"
    ],
    "_main_party": [],
    "_main_sac" : [
        "bakugame", "common_sac", "deka", "genki", "muki", "suki",
        "zubastar"
    ],
    "_main_seq" : [],
    "_main_unit" : [
        "bomzou", "koura", "mario", "object_switch", "object_tree", "party_christine",
        "party_chuchurina", "party_clauda", "party_nokotarou", "party_sanders", "party_vivian", "party_yoshi", "system"
    ],
    "_main_win" : [],
    "aaa": ["aaa_00"],
    "aji": [
        "aji_00", "aji_01", "aji_02", "aji_03", "aji_04", "aji_05",
        "aji_06", "aji_07","aji_08", "aji_09", "aji_10", "aji_11",
        "aji_12", "aji_13", "aji_14", "aji_15", "aji_16", "aji_17",
        "aji_18", "aji_19", "evt_shuryolight", "unit_barriern_z", "unit_barriern", "unit_boss_magnum",
        "unit_gundan_zako", "battle_database",
    ],
    "bom": [
        "bom_00", "bom_01", "bom_02", "bom_03", "bom_04", "unit_bllizard",
        "unit_ice_pakkun", "unit_kuriboo", "battle_database"
    ],
    "dmo": ["dmo_00"],
    "dou": [
        "dou_00", "dou_01", "dou_02", "dou_03", "dou_04", "dou_05",
        "dou_06", "dou_07", "dou_08", "dou_09", "dou_10", "dou_11",
        "dou_12", "dou_13", "dou_dou", "evt_lect", "unit_bubble", "unit_heavy_bom",
        "unit_hermos", "unit_killer", "unit_kuriboo", "unit_patamet", "battle_database"
    ],
    "eki": [
        "eki_00", "eki_01", "eki_02", "eki_03", "eki_04", "eki_05",
        "eki_06", "unit_kuriboo", "unit_kurokumorn", "unit_patatogemet", "unit_sambo", "evt_lect"
    ],
    "end": [],
    "gon": [
        "gon_00", "gon_01", "gon_02", "gon_03", "gon_04", "gon_05",
        "gon_06", "gon_07", "gon_08", "gon_09", "gon_10", "gon_11",
        "gon_12", "gon_13", "unit_boss_gonbaba", "evt_lect", "unit_honenoko", "unit_kuriboo",
        "unit_nokonoko", "unit_patakuri", "unit_patapata", "unit_red_honenoko", "unit_togekuri"
    ],
    "gor": [
        "gor_00", "gor_01", "gor_02", "gor_03", "gor_04", "gor_10",
        "gor_11", "gor_12", "gor_irai", "unit_boss_kanbu1", "unit_gundan_zako", "unit_kuriboo",
        "unit_lecture_christine", "unit_lecture_frankli", "unit_monban", "unit_npc_christine", "evt_lect"
    ],
    "gra": [
        "gra_00", "gra_01", "gra_02", "gra_03", "gra_04", "gra_05",
        "gra_06", "unit_faker_mario", "unit_hyper_kuriboo", "unit_hyper_patakuri", "unit_hyper_sinemon", "unit_kuriboo",
        "unit_pansy", "unit_twinkling_pansy", "unit_hyper_togekuri"
    ],
    "hei": [
        "hei_00", "hei_01", "hei_02", "hei_03", "hei_04", "hei_05",
        "hei_06", "hei_07", "hei_08", "hei_09", "hei_10", "hei_11",
        "hei_12", "hei_13", "unit_chorobon", "unit_gold_chorobon", "unit_kuriboo", "unit_monochrome_sinemon",
        "unit_nokonoko", "unit_patakuri", "unit_patapata", "unit_sinemon", "unit_sinnosuke", "unit_togedaruma",
        "unit_togekuri", "evt_lect"
    ],
    "hom": ["hom_00", "hom_10", "hom_11", "hom_12"],
    "jin": [
        "jin_00", "jin_01", "jin_02", "jin_03", "jin_04", "jin_05",
        "jin_06", "jin_07", "jin_08", "jin_09", "jin_10", "jin_11",
        "unit_atmic", "unit_basabasa", "unit_boss_rampell", "unit_faker_mario", "unit_gullible_christine", "unit_gullible_clauda",
        "unit_gullible_nokotarou", "unit_gullible_yoshi", "unit_met", "unit_teresa", "unit_togemet", "evt_kagemario"
    ],
    "jon": [
        "jon_evt", "jon_gonbaba", "jon_iri_12", "jon_jon", "unit_badge_borodo", "unit_basabasa", "unit_bllizard",
        "unit_bomhei", "unit_borodo", "unit_boss_zonbaba", "unit_bubble", "unit_burst_wanwan", "unit_chorobon",
        "unit_churantalar_piders", "unit_churantalar_renzoku", "unit_churantalar", "unit_dark_keeper", "unit_dokugassun", "unit_flower_chorobon",
        "unit_giant_bomb", "unit_hannya", "unit_heavy_bom", "unit_hennya", "unit_hinnya", "unit_honenoko",
        "unit_hyper_jyugem", "unit_hyper_sinemon", "unit_hyper_togezo", "unit_ice_pakkun", "unit_jyugem", "unit_karon",
        "unit_mahorn", "unit_monochrome_kurokumorn", "unit_monochrome_sinemon", "unit_pakkun_flower", "unit_patamet", "unit_patatogemet",
        "unit_phantom", "unit_piders", "unit_purple_teresa", "unit_sambo_mummy", "unit_sambo", "unit_sinemon",
        "unit_super_mahorn", "unit_teresa", "unit_togenoko", "unit_togezo", "unit_twinkling_pansy", "unit_ura_noko",
        "unit_wanwan", "unit_yamitogedaruma", "unit_togekuri", "unit_yami_kuriboo", "unit_yami_noko", "unit_yami_pata",
        "unit_yami_patakuri", "unit_yami_togekuri", "jon"
    ],
    "kpa": [
        "kpa_00", "kpa_01", "kpa_02", "kpa_03", "kpa_04", "kpa_05",
        "kpa_06", "kpa_07"
    ],
    "las": [
        "las_00", "las_01", "las_02", "las_03", "las_04", "las_05",
        "las_06", "las_07", "las_08", "las_09", "las_10", "las_11",
        "las_12", "las_13", "las_14", "las_15", "las_16", "las_17",
        "las_18", "las_19", "las_20", "las_21", "las_22", "las_23",
        "las_24", "las_25", "las_26", "las_27", "las_28", "las_29",
        "las_30", "unit_basabasa", "unit_black_karon", "unit_boss_batten_leader", "unit_boss_batten_satellite", "unit_boss_black_peach",
        "unit_boss_bunbaba", "unit_boss_kamec", "unit_boss_koopa", "unit_boss_majolyne", "unit_boss_marilyn", "unit_boss_rampell",
        "unit_heavy_bom", "unit_honenoko", "unkt_karon", "unit_phantom", "unit_red_honenoko", "unit_super_killer",
        "unit_super_mahorn", "unit_wanwan", "battle_database", "evt_shuryolight", "unit_karon"
    ],
    "moo": [
        "moo_00", "moo_01", "moo_02", "moo_03", "moo_04", "moo_05", "moo_06", "moo_07", "unit_barriern_z", "unit_hyper_sinemon", "unit_kuriboo", "unit_sinemon"
    ],
    "mri": [
        "mri_00", "mri_01", "mri_02", "mri_03", "mri_04", "mri_05",
        "mri_06", "mri_07", "mri_08", "mri_09", "mri_10", "mri_11",
        "mri_12", "mri_13", "mri_14", "mri_15", "mri_16", "mri_17",
        "mri_18", "mri_19", "mri_20", "mri_evt", "mri_mri", "mri_puni",
        "unit_barriern", "unit_boss_kanbu2", "unit_boss_magnum", "unit_dokugassun", "unit_gundan_zako", "unit_kuriboo",
        "unit_monochrome_kurokumorn", "unit_monochrome_pakkun", "unit_pakkun_flower", "unit_piders", "battle_database", "evt_lect"
    ],
    "muj": [
        "muj_00", "muj_01", "muj_02", "muj_03", "muj_04", "muj_05",
        "muj_06", "muj_07", "muj_08", "muj_09", "muj_10", "muj_11",
        "muj_12", "muj_20", "muj_21", "muj_battle_database", "muj_evt", "muj_korutesu",
        "muj_muj", "unit_boss_cortez", "unit_boss_gundan_zako_group1", "unit_boss_honeduka", "unit_boss_kanbu3", "unit_flower_chorobon",
        "unit_green_chorobon", "unit_boss_gundan_zako_group2", "unit_boss_gundan_zako_group3", "unit_boss_gundan_zako_magician", "unit_gundan_zako", "unit_hermos",
        "unit_kuriboo", "unit_pakkun_flower", "unit_poison_pakkun", "battle_database", "evt_lect"
    ],
    "nok": [
        "nok_00", "nok_01", "nok_nokonoko", "unit_act_kinopio", "unit_act_mario", "unit_act_teresa",
        "unit_act_atmic", "unit_act_clauda", "unit_act_kinopiko"
    ],
    "pik": [
        "pik_00", "pik_01", "pik_02", "pik_03", "pik_04", "unit_purple_teresa"
    ],
    "rsh": [
        "rsh_00", "rsh_01", "rsh_02", "rsh_03", "rsh_04", "rsh_05",
        "rsh_06", "rsh_07", "rsh_08", "rsh_evt", "rsh_kami", "rsh_simi",
        "unit_boss_moamoa", "battle_database"
    ],
    "sys": [],
    "tik": [
        "tik_00", "tik_01", "tik_02", "tik_03", "tik_04", "tik_05",
        "tik_06", "tik_07", "tik_08", "tik_09", "tik_10", "tik_11",
        "tik_12", "tik_13", "tik_14", "tik_15", "tik_16", "tik_17",
        "tik_18", "tik_19", "tik_20", "tik_21", "unit_boss_gesso", "unit_hammer_bros",
        "unit_hannya", "unit_hennya", "unit_hinnya", "unit_kamec", "unit_kuriboo", "unit_lecture_frankli",
        "unit_nokonoko", "unit_patakuri", "unit_patapata", "unit_togekuri", "unit_togenoko", "battle_database",
        "evt_lect"
    ],

    "tou2": [
        "tou_03", "unit_basabasa", "unit_bomhei", "unit_boomerang_bros", "unit_borodo", "unit_boss_champion",
        "unit_boss_koopa", "unit_boss_macho", "unit_burst_wanwan", "unit_chorobon", "unit_chrimson_togemet", "unit_dark_keeper",
        "unit_fire_bros", "unit_flower_chorobon", "unit_green_chorobon", "unit_hammer_bros", "unit_hannya", "unit_hennya",
        "unit_hinnya", "unit_honenoko", "unit_hyper_jyugem", "unit_hyper_sinnosuke", "unit_hyper_togezo", "unit_iron_sinemon",
        "unit_iron_sinemon2", "unit_jyugem", "unit_kamec", "unit_monochrome_kurokumorn", "unit_monochrome_pakkun", "unit_nokonoko",
        "unit_patapata", "unit_piders", "unit_sambo", "unit_togedaruma", "unit_togezo", "unit_ura_noko",
        "unit_ura_pata", "unit_wanawana", "unit_crimson_togemet", "unit_kurikuri", "unit_togenoko"
    ],
    "tou": [
        "tou_00", "tou_01", "tou_02", "tou_03", "tou_04", "tou_05",
        "tou_06", "tou_07", "tou_08", "tou_09", "tou_10", "tou_11",
        "tou_12", "tou_13", "tou_20", "tou_dummy", "tou_evt", "evt_lect"
    ],
    "tst": [], #only not blank on PAL
    "usu": [
        "usu_00", "usu_01", "evt_lect", "evt_kagemario"
    ],
    "win": [
        "win_00", "win_01", "win_02", "win_03", "win_04", "win_05",
        "win_06", "win_evt", "unit_boss_majolyne", "unit_boss_marilyn", "unit_boss_vivian", "unit_dokugassun",
        "unit_gundan_zako", "unit_kuriboo", "unit_monochrome_kurokumorn", "unit_monochrome_pakkun", "unit_monochrome_sinemon", "unit_pakkun_flower",
        "win_win", "evt_lect"
    ],
    "yuu": [
        "yuu_00", "yuu_01", "yuu_02", "yuu_03", "evt_yuuminigame", "evt_yuunpc"
    ]
}

# Create directories for keys and elements
for key, elements in prefix_subdirs.items():
    key_path = os.path.join(path_to_files, key)
    os.makedirs(key_path, exist_ok=True)
    
    for element in elements:
        element_path = os.path.join(key_path, element)
        os.makedirs(element_path, exist_ok=True)

# Sort files into appropriate folders
for filename in os.listdir(path_to_files):
    file_path = os.path.join(path_to_files, filename)
    
    if os.path.isfile(file_path):
        moved = False
        for key, elements in prefix_subdirs.items():
            if moved:
                break
                
            if filename.startswith(key):
                for element in elements:
                    if filename.startswith(f"{key}_{element}_"):
                        destination_path = os.path.join(path_to_files, key, element, filename)
                        shutil.move(file_path, destination_path)
                        moved = True
                        break
                        
                if not moved:
                    destination_path = os.path.join(path_to_files, key, filename)
                    shutil.move(file_path, destination_path)
                    moved = True
