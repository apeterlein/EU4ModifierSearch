import os
import re
from base64 import standard_b64encode as b64encode
from bz2 import compress
from json import loads, dumps as JSONencode
from time import perf_counter
from pdb import set_trace as trace

base = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Europa Universalis IV\\"
base_ign = ["trigger", "is_valid", "chance", "ai_will_do", "ai_chance", "allow", "potential", \
            "chance", "default", "enabled", "can_pick", "is_bad", "is_imperial_modifier", \
            "is_man_of_war_modifier", "is_marine_modifier", "is_scholar_modifier", \
            "is_streltsy_modifier", "is_janissary_modifier", "is_banner_modifier", \
            "is_carolean_modifier", "is_cawa_modifier", "is_cossack_modifier", \
            "is_mercenary_modifier", "is_qizilbash_modifier", "is_rajput_modifier", \
            "is_revolutionary_guard_modifier", "is_hussars_modifier", "is_mamluks_modifier", \
            "is_samurai_modifier", "is_tercio_modifier", "color", "custom_name", "picture", \
            "sprite", "ai_priority", "custom_tooltip"]
sep = chr(31)
final = { "__modifiers": {} }

def addTabCount(inp: str) -> str:
    inp = inp.replace("    ", "\t") # :(
    return str(len(inp) - len(inp.lstrip("\t"))) + sep + inp.strip()

def processLine(line: str) -> list[(str, str)]:
    line = line.split("#")[0].strip() # Strip comments and whitespace
    result = []
    for ln in re.split("([{}])", line):
        if ln == "":
            continue
        if ln in ("{", "}"): # Start or end of block
            result.append((ln, ""))
        elif "=" in ln: # Modifiers and value
            spln = ln.split("=")
            mod, val = spln[0].strip(), "".join(spln[1:]).strip()
            if mod != "":
                result.append((mod, val))
    return result

def parse(label: str, drc: str, mod_levels: list[int], effect_level: int, ign_files: list[str] = [], \
          inc_files: list[str] = [], ign_blocks: list[str] = [], effect_keys: list[str] = [], \
          debug: bool = False, debug_lines: int = 250):
    print("Parsing " + label + "...")
    start_time = perf_counter()
    num = 0 # Parsed line counter
    if label not in final:
        final[label] = {}
    ign_blocks += base_ign
    for root, _, files in os.walk(base + drc): # Walk through each file in directory
        for file in files:
            if file in ign_files or (inc_files and file not in inc_files):
                continue
            path = os.path.join(root, file)
            with open(path) as f:
                path = ".\\" + drc # For later labelling
                level = 0 # Current bracket level
                skip_level = -1 # Skip to level
                effect = "" # Current effect
                contents = [path] # Effect contents
                for line in f:
                    if len(line.strip()) > 0:
                        contents.append(addTabCount(line))
                    num += 1
                    if debug:
                        print("==================")
                        print("LINE: ", repr(line))
                        if num > debug_lines:
                            break
                    if num % 500 == 0 and not debug:
                        print(num, "lines in %.4f seconds" % (perf_counter() - start_time))
                    ended = False # Track end of effect portion of file
                    for mod, val in processLine(line):
                        if debug:
                            print("------------------")
                            print("PRC MOD: " + mod)
                            print("PRC VAL: " + val)
                            print("LEVEL: ", level)
                            print("SKIP: ", skip_level)
                        if mod == "{":
                            level += 1 # Increase level
                            if debug:
                                print("== INC LEVEL")
                            continue
                        if mod == "}":
                            level -= 1 # Decrease level
                            if level == effect_level:
                                ended = True
                            if debug:
                                print("== DNC LEVEL")
                        if level <= skip_level: # Done skipping
                            skip_level = -1
                            if debug:
                                print("== SKIP END")
                        if skip_level == -1 and mod not in ("{", "}"):
                            if mod in ign_blocks:
                                if debug:
                                    print("== START SKIP")
                                skip_level = level
                                continue
                            if effect_keys: # By key instead of level
                                if mod in effect_keys:
                                    effect = val # New effect
                                    if debug:
                                        print("== NEW EFFECT: ", effect)
                            elif level == effect_level:
                                effect = mod # New effect
                                if debug:
                                    print("== NEW EFFECT: ", effect)
                            if val == "" or effect == "":
                                continue
                                if debug:
                                    print("== REJ EMPTY")
                            if level in mod_levels:
                                title = (label + sep + effect)
                                if debug:
                                    print("== ADD MOD: ", repr(title))
                                if mod not in final["__modifiers"]:
                                    final["__modifiers"][mod] = [title]
                                if title not in final["__modifiers"][mod]:
                                    final["__modifiers"][mod].append(title)
                    if ended:
                        if debug:
                            print("== EFFECT END")
                        if effect != "":
                            final[label][effect] = contents
                            effect = ""
                        elif debug:
                            print("== EMPTY EFFECT DISCARDED")
                        contents = [path]

def finalEncode() -> str:
    return b64encode(compress(JSONencode(final).encode())).decode()

# Version
with open(base + "launcher-settings.json") as f:
    final["__version"] = loads("".join(f))["version"]
    
print("Updating for", final["__version"])

# Advisors
parse("Advisor Modifiers", "common\\advisortypes\\", [1, 3], 0, ign_blocks = ["monarch_power"])

# Age abilities
parse("Age Abilities", "common\\ages\\", [4], 0, ign_blocks = ["objectives", "effect"])

# Ancestor Personalities
ign = ["ruler_allow", "heir_allow", "consort_allow", "easy_war_chance_multiplier", "fair_fights", \
       "gift_chance", "knowledge_sharing", "other_ai_help_us_multiplier", "war_chance_multiplier", \
       "wants_condottieri", "different_religion_war_multiplier", "wants_gold", "custom_ai_explanation", \
       "nation_designer_cost", "building_budget_multiplier", "war_priority", "wants_colonies", \
       "ai_pick_ancestor", "other_ai_peace_term_bonus", "other_ai_war_chance_multiplier", \
       "wants_avoid_debase", "wants_avoid_loans", "wants_ecumenical_council", "peace_desire", \
       "heretic_ally_acceptance", "heathen_ally_acceptance", "alliance_acceptance", "enemy_strength_multiplier", \
       "wants_heathen_land", "wants_heretic_land", "wants_excommunicate", "wants_land", "wants_explorers"]
parse("Ancestor Personalities", "common\\ancestor_personalities", [1], 0, ign_blocks = ign)

# Buildings
ign = ["build_trigger", "keep_trigger", "on_built", "on_destroyed", "manufactory", "bonus_manufactory"]
parse("Building Modifiers", "common\\buildings\\", [2], 0, ign_blocks = ign)

# Centers of trade
parse("Centers of Trade", "common\\centers_of_trade\\", [2], 0)

# Church aspects
parse("Church Aspects", "common\\church_aspects\\", [2], 0, ign_blocks = ["effect"])

# Custom nation ideas
ign = ["category", "level_cost_1", "level_cost_2", "level_cost_3", "level_cost_4", "level_cost_5",
       "level_cost_6", "level_cost_7", "level_cost_8", "level_cost_9", "level_cost_10", "max_level"]
parse("Custom Nation Ideas", "common\\custom_ideas\\", [2], 1, ign_blocks = ign)

# EoC Decrees
parse("EoC Decrees", "common\\decrees\\", [2], 0, ign_blocks = ["effect"])

# Defender of the faith
parse("DoF Modifiers", "common\\defender_of_faith\\", [2], 0)

# Disasters
ign = ["can_start", "can_stop", "can_end", "progress", \
       "down_progress", "on_start", "on_end", "on_start_effect", \
       "on_end_effect", "on_progress_effect", "on_monthly", "monthly"]
parse("Disaster Modifiers", "common\\disasters\\", [2], 0, ign_blocks = ign)

# Crownland
parse("Crownland Modifiers", "common\\estate_crown_land\\", [2], 0, inc_files = ["00_bonuses.txt"], effect_keys = ["key"])

# Estate privileges
ign = ["can_select", "can_revoke", "on_granted", "on_revoked", "on_granted_province", "on_revoked_province", \
       "on_invalid", "on_invalid_province", "mechanics", "additional_description", "on_cooldown_expires"]
parse("Privilege Modifiers", "common\\estate_privileges\\", [2, 3], 0, ign_blocks = ign)

# Estates
ign = ["province_independence_weight", "land_ownership_modifier", "influence_modifier", \
       "loyalty_modifier", "privileges", "agendas", "desc"]
parse("Estate Modifiers", "common\\estates\\", [2], 0, ign_blocks = ign)

# Events
parse("Event Modifiers", "common\\event_modifiers\\", [1], 0, ign_blocks = ["religion", "secondary_religion"], \
      ign_files = ["01_mission_modifiers.txt"])

# Missions
parse("Mission Modifiers", "common\\event_modifiers\\", [1], 0, ign_blocks = ["religion", "secondary_religion"], \
      inc_files = ["01_mission_modifiers.txt"])

# Factions
parse("Faction Modifiers", "common\\factions\\", [2], 0)

# Federation advancements
parse("Federation Advancements", "common\\federation_advancements\\", [2], 0, ign_blocks = ["effect"])

# Religious fervor
parse("Religious Fervor", "common\\fervor\\", [2], 0)

# Static modifiers
parse("Static Modifiers", "common\\static_modifiers\\", [1], 0, ign_blocks = ["religion"])

# Cults
parse("Cult Modifiers", "common\\fetishist_cults\\", [1], 0)

# Flagships
parse("Flagship Modifiers", "common\\flagship_modifications\\", [2], 0, ign_blocks = ["ai_trade_score", "ai_war_score"])

# Golden bulls
parse("Golden Bulls", "common\\golden_bulls\\", [2], 0, ign_blocks = ["mechanics"])

# Goverment reforms
ign = ["nation_designer_trigger", "factions", "assimilation_cultures", "states_general_mechanic", \
       "disallowed_trade_goods", "ai", "conditional", "removed_effect", "custom_attributes", \
       "remove_country_modifier", "remove_government_reform"]
parse("Government Reforms", "common\\government_reforms\\", [2], 0, ign_blocks = ign)

# Great projects
ign = ["build_trigger", "on_built", "on_destroyed", "can_use_modifiers_trigger", \
       "can_upgrade_trigger", "keep_trigger", "upgrade_time", "cost_to_upgrade", \
       "on_upgraded", "trigger", "tooltip_potential"]
parse("Great Projects", "common\\great_projects\\", [3, 4], 0, ign_blocks = ign)

# Hegemon modifiers
parse("Hegemon Modifiers", "common\\hegemons\\", [2], 0)

# Holy orders
ign = ["per_province_effect", "per_province_abandon_effect"]
parse("Holy Orders", "common\\holy_orders\\", [2], 0, ign_blocks = ign)

# Idea Groups
parse("Idea Groups", "common\\ideas\\", [2], 0, ign_blocks = ["category", "effect"], inc_files = ["00_basic_ideas.txt"])

# National Ideas
parse("National Ideas", "common\\ideas\\", [2], 0, ign_blocks = ["category", "effect"], ign_files = ["00_basic_ideas.txt"])

# Imperial reforms
ign = ["empire", "on_effect", "off_effect"]
parse("Imperial Reforms", "common\\imperial_reforms\\", [2], 0, ign_blocks = ign)

# Institutions
ign = ["history", "can_start", "can_embrace", "embracement_speed"]
parse("Institutions", "common\\institutions\\", [2], 0, ign_blocks = ign)

# Isolationism
parse("Isolationism", "common\\isolationism\\", [2], 0)

# Leader traits
parse("Leader Traits", "common\\leader_personalities\\", [1], 0)

# Mercenaries
parse("Mercenary Modifiers", "common\\mercenary_companies\\", [2], 0, ign_blocks = ["rnw_modifier_weights"])

# Naval doctrines
parse("Naval Doctrines", "common\\naval_doctrines\\", [2], 0, ign_blocks = ["effect", "removed_effect", "is_primitive"])

# Parliament
parse("Parliament Modifiers", "common\\parliament_issues\\", [2], 0, ign_blocks = ["effect", "on_issue_taken"])

# Personal deities
parse("Person Deities", "common\\personal_deities\\", [1], 0, ign_blocks = ["effect", "removed_effect"])

# Policies
ign = ["monarch_power", "effect", "removed_effect"]
parse("Policies", "common\\policies\\", [1], 0, ign_blocks = ign)

# Professionalism
ign = ["hidden", "army_professionalism", "marker_sprite", "unit_sprite_start"]
parse("Army Professionalism", "common\\professionalism\\", [1], 0, ign_blocks = ign)

# Province modifiers
ign = ["on_activation", "on_deactivation", "icon", "viewer", "hidden"]
parse("Province Modifiers", "common\\province_triggered_modifiers\\", [1], 0, ign_blocks = ign)

# Religions
ign = ["allowed_conversion", "on_convert", "heretic", "papacy", "allowed_center_conversion", \
       "aspects", "will_get_center", "orthodox_icons", "flag_emblem_index_range", "holy_sites", \
       "blessings", "religious_schools", "gurus", "celebrate"]
parse("Religions", "common\\religions\\", [3], 1, ign_blocks = ign)

# Papacy
ign = ["anglican", "hussite", "protestant", "reformed", "orthodox", "coptic", "muslim", "eastern", \
       "dharmic", "pagan", "jewish_group", "zoroastrian_group", "potential", "effect", \
       "cost", "on_convert", "curia_treasury_cost", "country", "country_as_secondary", \
       "province"]
parse("Papacy Modifiers", "common\\religions\\", [4, 6], 3, ign_blocks = ign)

# Orthodox icons
ign = ["anglican", "hussite", "protestant", "reformed", "catholic", "coptic", "muslim", "eastern", \
       "dharmic", "pagan", "jewish_group", "zoroastrian_group", "visible", "country", \
       "country_as_secondary", "province"]
parse("Orthodox Icons", "common\\religions\\", [4], 3, ign_blocks = ign)

# Sikh Gurus
ign = ["eastern", "muslim", "christian", "pagan", "jewish_group", "zoroastrian_group", "type", "cost"]
parse("Sikh Gurus", "common\\religions\\", [5, 6], 3, ign_blocks = ign)

# Religious Reforms
parse("Religious Reforms", "common\\religious_reforms\\", [2], 0, ign_blocks = ["can_buy_idea"])

# Ruler Personalities
ign = ["ruler_allow", "heir_allow", "consort_allow", "easy_war_chance_multiplier", "fair_fights", \
       "gift_chance", "knowledge_sharing", "other_ai_help_us_multiplier", "war_chance_multiplier", \
       "wants_condottieri", "different_religion_war_multiplier", "wants_gold", "custom_ai_explanation", \
       "nation_designer_cost", "building_budget_multiplier", "war_priority", "wants_colonies", \
       "static", "other_ai_peace_term_bonus", "other_ai_war_chance_multiplier", \
       "wants_avoid_debase", "wants_avoid_loans", "wants_ecumenical_council", "peace_desire", \
       "heretic_ally_acceptance", "heathen_ally_acceptance", "alliance_acceptance", "enemy_strength_multiplier", \
       "wants_heathen_land", "wants_heretic_land", "wants_excommunicate", "wants_land", "wants_explorers", \
       "wants_avoid_ugly_borders", "wants_betray_allies", "wants_debase", "wants_disclose_attack", \
       "wants_loans", "wants_sell_provinces", "wants_threaten_war", "wants_to_appoint_cardinals_in_his_own_land", \
       "underestimate_ae"]
parse("Ruler Personalities", "common\\ruler_personalities", [1], 0, ign_blocks = ign)

# State Edicts
parse("State Edicts", "common\\state_edicts\\", [2], 0, ign_blocks = ["notify_trigger"])

# Subject Upgrades
parse("Subject Upgrades", "common\\subject_type_upgrades\\", [2], 0, ign_blocks = ["can_upgrade_trigger", "effect"])

# TC Investments
parse("TC Investments", "common\\tradecompany_investments\\", [2], 0, \
      ign_blocks = ["ai_global_worth", "ai_area_worth", "ai_region_worth"])

# Trade Goods
parse("Trade Goods", "common\\tradegoods\\", [2], 0)

# Merchant policies
ign = ["center_of_reformation", "button_gfx", "trade_power", "dominant_religion"]
parse("Merchant Policies", "common\\trading_policies\\", [2], 0, ign_blocks = ign)

# Triggered modifiers
ign = ["on_activation", "on_deactivation", "icon", "viewer", "hidden"]
parse("Triggered Modifiers", "common\\province_triggered_modifiers\\", [1], 0, ign_blocks = ign)

with open("../modifiers.js", "w") as f:
    f.write("window.modifiers = \"" + finalEncode() + "\";")