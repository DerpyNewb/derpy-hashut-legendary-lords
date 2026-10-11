"""Mirror the Hashut's Legendary Lords tools into repos/derpy-hashut-legendary-lords, the public repo.

The workspace is the source of truth; the repo is a copy with the same layout, so every
tool's relative paths ("Modding Files/...", "tools/...") work from either root.
README.md, CHANGELOG.md, LICENSE, .gitignore and .gitattributes are written in the repo
itself and never touched here. The copying is sync_guilds_repo's.

    py tools/sync_hll_repo.py            # copy every changed file into the repo
    py tools/sync_hll_repo.py --check    # list drift, copy nothing; exit 1 on drift
    py tools/sync_hll_repo.py --selftest

Then commit and push from inside the repo folder.

TOOLS ONLY, by the author's ask (2026-10-11: "a repo for the tools used in the hll mod"). The
mod's own Lua and TSVs are not mirrored: the lords pack is the truth for its 81 scripts and
the staged copies under Modding Files/pack go stale against it. TOOLS below is every tool that
builds, imports into or audits !aa_derpy_hashut_legendary_lords.pack, plus everything those
import, found by walking their imports. The house ancillary generators are not here: they
build derpy_chd_house_ancillaries.pack, which has its own repo.

NOTHING OF CA'S OR GW'S IS PUBLISHED, and no file naming a Windows user profile. `refused()`
checks every manifest entry, by extension and by content, and the sync will not run while it
reports anything.
"""
import os
import re
import sys

import sync_guilds_repo as SG

ROOT = SG.ROOT
REPO = os.path.join(ROOT, "repos", "derpy-hashut-legendary-lords")

TOOLS = [
    # victory routes: the generator and its importer
    "gen_victory_routes.py", "import_victory_routes.py", "anc_effect_scopes.py",
    # the two lords added 2026-10-03, Zochaz, and what was built on them
    "gen_new_house_lords.py", "gen_new_lords_cb.py", "gen_kharkadon_bodyguards.py",
    "gen_zochaz.py", "gen_portrait_settings.py", "gen_character_portrait.py",
    "make_toz_seat_banner.py",
    # the naval horde (Abnagg and Tordrek) and Tordrek's Vampire Coast skills
    "gen_naval_horde_units.py", "gen_naval_horde_phase6.py", "gen_naval_horde_admiral.py",
    "gen_naval_horde_tordrek.py", "import_naval_horde.py", "gen_tordrek_vc_skills.py",
    "patch_army_banner.py", "test_naval_confed_stances.lua",
    # missions, AI strength, the Conclave's start (stale, says so itself)
    "gen_hellshard_missions.py", "test_drill_relic_dilemma.lua", "gen_ll_ai_strength.py",
    "gen_ghorth_settlement_tiers.py",
    # audits
    "check_skill_trees.py", "export_skill_lines.py", "check_hll_settings.py",
    "check_effect_signs.py", "check_effect_bundle_loc.py",
    "check_lua_api.py", "check_lua_undeclared.py", "check_lua_literal_left.py",
    # readers and the RPFM client everything above imports
    "import_house_ancillaries.py", "rpfm_client.py", "read_pack_index.py", "read_animpack.py",
    "read_vanilla_cache.py", "fetch_vanilla_tables.py", "read_vanilla_db.py",
    "gen_commodity_icons.py",
    # this file and its copier
    "sync_guilds_repo.py", "sync_hll_repo.py",
]

REFERENCE = ["VICTORY_CONDITIONS.md", "MISSIONS.md", "TOWER_OF_ZHARR_CUSTOM_SEATS.md",
             "HELLFORGE_UNIT_CAPS.md"]
SPECS = ["2026-10-06-kharkadon-bodyguards-design.md", "2026-10-06-kharkadon-personal-line-design.md",
         "2026-10-11-victory-routes-vco-parity-design.md",
         "2026-10-11-victory-routes-vco-parity-phase2-design.md"]
PLANS = ["2026-10-06-kharkadon-personal-line.md", "2026-10-11-victory-routes-vco-parity-phase1.md",
         "2026-10-11-victory-routes-vco-parity-phase2.md"]
# HANDOFF_20260831_ABNAGG_TORDREK_SHIPBUILDING_SCOPE.md is left out: it names a Windows profile.
HISTORY = [
    "HANDOFF_20260901_NAVAL_HORDE_ROSTER.md", "HANDOFF_20260901_TORDREK_VC_SKILLS.md",
    "HANDOFF_20260902_NAVAL_HORDE_LIVE_VERIFY.md", "HANDOFF_20260903_HELLSHARD_REPAIR.md",
    "HANDOFF_20260907_VICTORY_ROUTES.md", "HANDOFF_20260908_GHORTH_VICTORY_ROUTES.md",
    "HANDOFF_20260909_VICTORY_ROUTE_REPAIR.md", "HANDOFF_20260911_LL_AI_STRENGTH_FLOOR.md",
    "HANDOFF_20260917_NAVAL_CONFED_STANCES.md", "HANDOFF_20260924_VICTORY_TROPHY_ITEMS.md",
    "HANDOFF_20261003_HLL_MCT_SETTINGS.md", "HANDOFF_20261003_NEW_HOUSE_LORDS.md",
    "HANDOFF_20261004_LORE_ROUTES_AND_BALUR.md", "HANDOFF_20261004_WARRHAK_GORDAK_QUESTS.md",
    "HANDOFF_20261005_KHARKADON_MODEL_AND_OW_FRONTEND.md",
    "HANDOFF_20261006_KHARKADON_BODYGUARDS_DESIGN.md",
    "HANDOFF_20261006_KHARKADON_CUSTOM_BATTLE_PORTRAIT.md",
    "HANDOFF_20261006_KHARKADON_FACTION_EFFECTS.md", "HANDOFF_20261006_KHARKADON_ITEMS.md",
    "HANDOFF_20261006_KHARKADON_PERSONAL_LINE.md", "HANDOFF_20261006_KHARKADON_SELF_BUFFS.md",
    "HANDOFF_20261006_KHARKADON_TEXTURE_SRGB_AND_PORTRAITS.md",
    "HANDOFF_20261007_KHARKADON_SELF_EFFECT_TEXT.md",
    "HANDOFF_20261007_KHARKADON_VICTORY_ROUTES.md", "HANDOFF_20261010_HLL_ELECTOR_SEATS_SCOPE.md",
    "GHORTH_MISSION_OPTIONS_20260903.md", "HOUSE_MISSION_OPTIONS_20260903.md",
    "SKILL_TREE_AUDIT_20260821.md", "VICTORY_ROUTE_TEXT_REVIEW_20261011.md",
]

# Anything that is art, a built pack, a CA ui file or a binary game format never goes public.
REFUSED_EXT = (".png", ".dds", ".jpg", ".jpeg", ".webp", ".tga", ".pack", ".bin",
               ".loc", ".anim", ".rigid_model_v2", ".wem", ".twui.xml", ".xlsx")
# A Windows user-profile path, in any file: it names the machine's owner.
PRIVATE = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s]+", re.I)


def manifest():
    out = [("tools/" + n, "tools/" + n) for n in TOOLS]
    out += [("docs/" + n, "docs/" + n) for n in REFERENCE]
    out += [("docs/superpowers/specs/" + n, "docs/design/" + n) for n in SPECS]
    out += [("docs/superpowers/plans/" + n, "docs/plans/" + n) for n in PLANS]
    out += [("docs/sessions/" + n, "docs/history/" + n) for n in HISTORY]
    return out


def refused(m, root=ROOT):
    """Every manifest entry that must never be published, with why."""
    bad = []
    for src, _dst in m:
        if src.lower().endswith(REFUSED_EXT):
            bad.append((src, "art, CA ui file or game binary"))
            continue
        p = os.path.join(root, src)
        if os.path.isfile(p):
            with open(p, encoding="utf-8", errors="replace") as fh:
                hit = PRIVATE.search(fh.read())
            if hit:
                bad.append((src, "names a user profile: %s" % hit.group(0)))
    return bad


def _selftest():
    import tempfile
    m = manifest()
    assert not refused(m), refused(m)
    # Only the workspace holds the sources; in the repo the docs sit at their remapped paths.
    if os.path.isdir(os.path.join(ROOT, "docs", "superpowers")):
        missing = [s for s, _d in m if not os.path.isfile(os.path.join(ROOT, s))]
        assert not missing, "manifest names files that do not exist: %s" % missing
    assert len({d for _s, d in m}) == len(m), "two entries land on one repo path"
    for probe in ("ui/campaign ui/army_banner.twui.xml", "x/derpy_kharkadon.png",
                  "Modding Files/Modpacks/!aa_derpy_hashut_legendary_lords.pack"):
        assert refused([(probe, probe)]), "refused() let %s through" % probe
    with tempfile.TemporaryDirectory() as td:
        with open(os.path.join(td, "a.md"), "w") as fh:
            fh.write("see C:" + "\\Users\\someone\\notes.md")
        assert refused([("a.md", "a.md")], td), "refused() let a user-profile path through"
    print("selftest ok: %d files, nothing refused" % len(m))


if __name__ == "__main__":
    unknown = [a for a in sys.argv[1:] if a not in ("--check", "--selftest")]
    if unknown:
        print("unknown argument(s): %s" % " ".join(unknown))
        sys.exit(2)
    m = manifest()
    bad = refused(m)
    if bad:
        for s, why in bad:
            print("REFUSED  %s  (%s)" % (s, why))
        sys.exit(1)
    if "--selftest" in sys.argv:
        _selftest()
    elif "--check" in sys.argv:
        found = SG.drift(ROOT, REPO, m)
        for s, _d, why in found:
            print("%-22s %s" % (why, os.path.relpath(s, ROOT)))
        print("%d file(s) drift" % len(found))
        sys.exit(1 if found else 0)
    else:
        found = SG.sync(ROOT, REPO, m)
        for s, _d, why in found:
            print("%-22s %s" % (why, os.path.relpath(s, ROOT)))
        print("synced %d file(s) into %s" % (len(found), REPO))
