from __future__ import annotations

import gzip
import json
from pathlib import Path

from . import HDBEST_FORMAT, HDBEST_VERSION, proto, schema


def _submsg(ud: dict[int, list], field: int) -> dict[int, list]:
    raw = proto.get(ud, field)
    return proto.decode(raw) if isinstance(raw, (bytes, bytearray)) else {}


def _strs(d: dict[int, list], field: int) -> list[str]:
    return [
        v.decode("utf-8", "replace")
        for v in proto.get_list(d, field)
        if isinstance(v, (bytes, bytearray))
    ]


def parse_userdata(ud: dict[int, list]) -> dict:
    f = schema.field
    user = _submsg(ud, f("UserData", "user"))
    profile = _submsg(ud, f("UserData", "user_profile"))

    cards = []
    for raw in proto.get_list(ud, f("UserData", "user_card_list")):
        c = proto.decode(raw)
        cid = proto.get_str(c, f("UserCard", "card_id"))
        if cid:
            cards.append(
                {
                    "id": cid,
                    "exp": proto.get_int(c, f("UserCard", "exp")),
                    "bloom": proto.get_int(c, f("UserCard", "level_limit_break_count")),
                    "potential": proto.get_int(
                        c, f("UserCard", "potential_upgrade_count")
                    ),
                }
            )

    songs = [
        mid
        for raw in proto.get_list(ud, f("UserData", "user_music_list"))
        if (mid := proto.get_str(proto.decode(raw), f("UserMusic", "music_id")))
    ]

    holomems = []
    for raw in proto.get_list(ud, f("UserData", "user_character_list")):
        ch = proto.decode(raw)
        cid = proto.get_str(ch, f("UserCharacter", "character_id"))
        if cid:
            holomems.append(
                {"id": cid, "exp": proto.get_int(ch, f("UserCharacter", "exp"))}
            )

    boards = []
    for raw in proto.get_list(ud, f("UserData", "user_character_skill_tree_list")):
        st = proto.decode(raw)
        cid = proto.get_str(st, f("UserCharacterSkillTree", "character_id"))
        if not cid:
            continue
        boards.append(
            {
                "character": cid,
                "nodes": _strs(
                    st,
                    f("UserCharacterSkillTree", "released_skill_tree_node_group_ids"),
                ),
                "connectedNodes": _strs(
                    st,
                    f("UserCharacterSkillTree", "connected_skill_tree_node_group_ids"),
                ),
                "connectedCards": _strs(
                    st,
                    f("UserCharacterSkillTree", "connected_skill_tree_node_card_ids"),
                ),
            }
        )

    cleared_quests = [
        qid
        for raw in proto.get_list(ud, f("UserData", "user_park_quest_list"))
        if proto.get_int((q := proto.decode(raw)), f("UserParkQuest", "clear_time")) > 0
        and (qid := proto.get_str(q, f("UserParkQuest", "park_quest_id")))
    ]
    treasures = _strs(
        _submsg(ud, f("UserData", "user_park_treasure")),
        f("UserParkTreasure", "park_treasure_ids"),
    )
    free_chats = [
        tid
        for raw in proto.get_list(
            ud, f("UserData", "user_park_talk_free_pick_result_detail_list")
        )
        if _strs(
            (d := proto.decode(raw)),
            f("UserParkTalkFreePickResultDetail", "already_read_character_ids"),
        )
        and (
            tid := proto.get_str(
                d, f("UserParkTalkFreePickResultDetail", "park_talk_free_id")
            )
        )
    ]

    return {
        "publicUserId": proto.get_str(user, f("User", "public_user_id")),
        "userName": proto.get_str(profile, f("UserProfile", "name")),
        "playerExp": proto.get_int(profile, f("UserProfile", "exp")),
        "cards": cards,
        "songs": songs,
        "holomems": holomems,
        "boards": boards,
        "posterCount": len(proto.get_list(ud, f("UserData", "user_poster_list"))),
        "clearedQuests": cleared_quests,
        "treasures": treasures,
        "freeChats": free_chats,
    }


def build(ud: dict[int, list], region_code: str) -> dict:
    parsed = parse_userdata(ud)
    return {
        "format": HDBEST_FORMAT,
        "version": HDBEST_VERSION,
        "region": region_code,
        **parsed,
    }


def write(obj: dict, out_dir: str | Path = ".") -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = (obj.get("publicUserId") or "profile").strip() or "profile"
    dest = out_dir / f"{name}.hdbest"
    gz = gzip.compress(
        json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )
    dest.write_bytes(gz)
    return dest
