"""parse a game UserData snapshot to the .hdbest profile. stores RAW game values (exp, skill-tree
node group ids, counts); the backend converts to the site's shapes (level, board x,y, dream rank).
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

from . import HDBEST_FORMAT, HDBEST_VERSION, proto

# UserData field numbers (merged.proto)
_F_USER = 342861366  # User
_F_PROFILE = 49977942  # UserProfile
_F_CARD_LIST = 315485766  # UserCard
_F_MUSIC_LIST = 430828780  # UserMusic
_F_CHAR_LIST = 370704040  # UserCharacter
_F_SKILLTREE_LIST = 73736905  # UserCharacterSkillTree
_F_POSTER_LIST = 451819461  # UserPoster
_F_PARKQUEST_LIST = 296076812  # UserParkQuest
_F_PARKTREASURE = 327922352  # UserParkTreasure
_F_FREECHAT_DETAIL = 498625501  # UserParkTalkFreePickResultDetail
_UC_ID, _UC_EXP, _UC_LB, _UC_POT = 2, 3, 4, 5  # UserCard
_UM_ID = 2  # UserMusic
_U_PUBLIC_ID, _U_REGION = 2, 3  # User
_UP_NAME, _UP_EXP = 2, 14  # UserProfile
_UCH_ID, _UCH_EXP = 2, 6  # UserCharacter
_ST_CHAR, _ST_RELEASED, _ST_CONN_GROUPS, _ST_CONN_CARDS = (
    2,
    3,
    4,
    5,
)  # UserCharacterSkillTree
_PQ_ID, _PQ_CLEAR_TIME = 2, 5  # UserParkQuest
_PT_IDS = 2  # UserParkTreasure
_FC_TALK_ID, _FC_READ_CHRS = 3, 4  # UserParkTalkFreePickResultDetail


def parse_userdata(ud: dict[int, list]) -> dict:
    user = _submsg(ud, _F_USER)
    profile = _submsg(ud, _F_PROFILE)

    cards = []
    for raw in proto.get_list(ud, _F_CARD_LIST):
        c = proto.decode(raw)
        cid = proto.get_str(c, _UC_ID)
        if cid:
            cards.append(
                {
                    "id": cid,
                    "exp": proto.get_int(c, _UC_EXP),
                    "bloom": proto.get_int(c, _UC_LB),
                    "potential": proto.get_int(c, _UC_POT),
                }
            )

    songs = [
        mid
        for raw in proto.get_list(ud, _F_MUSIC_LIST)
        if (mid := proto.get_str(proto.decode(raw), _UM_ID))
    ]

    holomems = []
    for raw in proto.get_list(ud, _F_CHAR_LIST):
        ch = proto.decode(raw)
        cid = proto.get_str(ch, _UCH_ID)
        if cid:
            holomems.append({"id": cid, "exp": proto.get_int(ch, _UCH_EXP)})

    boards = []
    for raw in proto.get_list(ud, _F_SKILLTREE_LIST):
        st = proto.decode(raw)
        cid = proto.get_str(st, _ST_CHAR)
        if not cid:
            continue
        boards.append(
            {
                "character": cid,
                "nodes": _strs(st, _ST_RELEASED),
                "connectedNodes": _strs(st, _ST_CONN_GROUPS),
                "connectedCards": _strs(st, _ST_CONN_CARDS),
            }
        )

    cleared_quests = [
        qid
        for raw in proto.get_list(ud, _F_PARKQUEST_LIST)
        if proto.get_int((q := proto.decode(raw)), _PQ_CLEAR_TIME) > 0
        and (qid := proto.get_str(q, _PQ_ID))
    ]
    treasures = _strs(_submsg(ud, _F_PARKTREASURE), _PT_IDS)
    free_chats = [
        tid
        for raw in proto.get_list(ud, _F_FREECHAT_DETAIL)
        if _strs((d := proto.decode(raw)), _FC_READ_CHRS)
        and (tid := proto.get_str(d, _FC_TALK_ID))
    ]

    return {
        "publicUserId": proto.get_str(user, _U_PUBLIC_ID),
        "region": proto.get_int(user, _U_REGION),
        "userName": proto.get_str(profile, _UP_NAME),
        "playerExp": proto.get_int(profile, _UP_EXP),
        "cards": cards,
        "songs": songs,
        "holomems": holomems,
        "boards": boards,
        "posterCount": len(proto.get_list(ud, _F_POSTER_LIST)),
        "clearedQuests": cleared_quests,
        "treasures": treasures,
        "freeChats": free_chats,
    }


def _submsg(ud: dict[int, list], field: int) -> dict[int, list]:
    raw = proto.get(ud, field)
    return proto.decode(raw) if isinstance(raw, (bytes, bytearray)) else {}


def _strs(d: dict[int, list], field: int) -> list[str]:
    out = []
    for v in proto.get_list(d, field):
        if isinstance(v, (bytes, bytearray)):
            out.append(v.decode("utf-8", "replace"))
    return out


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
