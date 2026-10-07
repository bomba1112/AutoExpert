# ruff: noqa: E501
"""The owners club (product phase, stage 4), behind the owners_club_v1 flag.

- Rooms: one per make and one per popular generation (a generation with configurations and at
  least three known issues in the database), never per trim, so no room is empty. An owner gets
  to the rooms from a car in the garage.
- Starter topics come from the database's known issues of the generation (rendered in the
  reader's language; FACT plain, SECONDARY_NOTE "по данным справочников", OWNER_REPORTS
  "владельцы сообщают"; HIDDEN_CONFLICT never).
- Writing needs a confirmed email (the preview's demo sessions excepted) and no active ban.
  E-mail addresses and phone numbers in texts are masked; photos are re-encoded (no camera
  metadata, no location). Authors are shown by a display name, never by e-mail.
- Moderation: reports (three reports hide a text until a moderator looks), an automatic filter of
  obscenities and spam (held for a moderator), optional AI moderation (club_ai_moderation),
  bans, and a log of every moderation action.
- Owners repeatedly reporting the same problem ("у меня то же самое" from club_review_threshold
  owners) put the post into a review queue; only a moderator's approval writes it to the database,
  as OWNER_REPORTS ("владельцы сообщают").
"""

from __future__ import annotations

import hashlib
import io
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.english import pick
from app.db.session import bind_url
from app.models.catalog import VehicleGeneration, VehicleMake, VehicleModel
from app.models.club import (
    ClubBan,
    ClubComment,
    ClubModerationLog,
    ClubPhoto,
    ClubPost,
    ClubReaction,
    ClubReport,
    ClubReviewItem,
    ClubRoom,
)
from app.models.evidence import KnownIssue, TechnicalEvidence
from app.models.user import User
from app.services import accounts, us_tech_facts

VISIBLE_LEVELS = ("FACT", "SECONDARY_NOTE", "OWNER_REPORTS")
MIN_ISSUES = 3
STARTERS = 20
POSTS_PER_10_MIN = 5
MAX_LINKS = 2
MAX_PHOTO_BYTES = 8 * 1024 * 1024
OBSCENE = re.compile(
    r"\b(?:ху[йяеёи]\w*|пизд\w*|[её]б(?:ан|ат|ал|у|ну)\w*|бля\w*|сук[аи]\w*|мудак\w*|залуп\w*|"
    r"fuck\w*|shit\w*|cunt\w*|bitch\w*|asshole\w*|motherfuck\w*|"
    r"sik\w*|götver\w*|qəhbə\w*|amcıq\w*|peysər\w*)", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE = re.compile(r"(?<!\w)\+?\d[\d\s().-]{7,}\d(?!\w)")
LINK = re.compile(r"https?://|www\.", re.I)
T = {
    "owner": ("Владелец", "Sahib", "Owner"),
    "hidden": ("[скрыто]", "[gizlədildi]", "[hidden]"),
    "auto_expert": ("Auto Expert · из нашей базы", "Auto Expert · bazamızdan", "Auto Expert · from our database"),
    "symptoms": ("Симптомы", "Əlamətlər", "Symptoms"),
    "check": ("Что проверить", "Nəyi yoxlamalı", "What to check"),
    "starter_note": ("Известная проблема этого поколения. Сталкивались? Расскажите и отметьте «у меня то же самое».",
                     "Bu nəslin məlum problemi. Rastlaşmısınız? Yazın və «məndə də eynisi» qeyd edin.",
                     "A known issue of this generation. Have you seen it? Tell us and mark \"me too\"."),
    "held": ("На проверке у модератора", "Moderator yoxlamasındadır", "Waiting for a moderator"),
}


class ClubError(Exception):
    def __init__(self, status: int, code: str):
        super().__init__(code)
        self.status, self.code = status, code


def enabled(settings=None) -> bool:
    settings = settings or get_settings()
    if settings.owners_club_v1 is not None:
        return bool(settings.owners_club_v1)
    return settings.environment != "production"


def tr(language: str, key: str) -> str:
    return pick(language, *T[key])


def display_name(user: User | None, language: str) -> str:
    if user is None:
        return tr(language, "auto_expert")
    if user.display_name:
        return user.display_name
    return f"{tr(language, 'owner')} #{hashlib.sha256(user.id.encode()).hexdigest()[:4].upper()}"


def mask_personal(text: str, language: str) -> str:
    hidden = tr(language, "hidden")
    return PHONE.sub(hidden, EMAIL.sub(hidden, text or ""))


# --- rooms -------------------------------------------------------------------------------------
_ROOMS_READY: set[str] = set()


def ensure_rooms(db) -> None:
    """Make rooms and popular generation rooms (idempotent)."""
    bind = bind_url(db)
    if bind in _ROOMS_READY and db.scalar(select(func.count()).select_from(ClubRoom)):
        return
    existing = set(db.scalars(select(ClubRoom.key)))
    gens = db.execute(
        select(VehicleGeneration.id, VehicleGeneration.code, VehicleGeneration.name, VehicleModel.name, VehicleMake.id, VehicleMake.name,
               func.min(TechnicalEvidence.year_from), func.max(TechnicalEvidence.year_to))
        .join(VehicleModel, VehicleModel.id == VehicleGeneration.model_id).join(VehicleMake, VehicleMake.id == VehicleModel.make_id)
        .join(TechnicalEvidence, TechnicalEvidence.generation_id == VehicleGeneration.id)
        .where(TechnicalEvidence.fact_key == "configuration")
        .group_by(VehicleGeneration.id, VehicleGeneration.code, VehicleGeneration.name, VehicleModel.name, VehicleMake.id, VehicleMake.name)).all()
    issue_counts = dict(db.execute(
        select(KnownIssue.generation_id, func.count(func.distinct(func.coalesce(KnownIssue.title, KnownIssue.component))))
        .where(KnownIssue.display_level.in_(VISIBLE_LEVELS), KnownIssue.is_demo.is_(False)).group_by(KnownIssue.generation_id)).all())
    for make_id, make_name in {(g[4], g[5]) for g in gens}:
        if f"make:{make_id}" not in existing:
            db.add(ClubRoom(key=f"make:{make_id}", kind="MAKE", make_id=make_id, title=make_name))
    for gen_id, code, name, model, make_id, make_name, y0, y1 in gens:
        if issue_counts.get(gen_id, 0) < MIN_ISSUES or f"generation:{gen_id}" in existing:
            continue
        label = code if code and len(code) <= 12 else (name or "")
        db.add(ClubRoom(key=f"generation:{gen_id}", kind="GENERATION", make_id=make_id, generation_id=gen_id,
                        title=f"{make_name} {model} {label}".strip(), year_from=y0, year_to=y1))
    db.flush()
    _ROOMS_READY.add(bind)


def rooms_for_vehicle(db, vehicle) -> list[ClubRoom]:
    ensure_rooms(db)
    row = db.execute(select(TechnicalEvidence.generation_id, TechnicalEvidence.make_id).where(
        TechnicalEvidence.fact_key == "configuration", TechnicalEvidence.configuration_key == vehicle.configuration_key).limit(1)).first()
    if not row:
        return []
    out = []
    room = db.scalar(select(ClubRoom).where(ClubRoom.key == f"generation:{row[0]}"))
    if room:
        out.append(room)
    make = db.scalar(select(ClubRoom).where(ClubRoom.key == f"make:{row[1]}"))
    if make:
        out.append(make)
    return out


def ensure_starters(db, room: ClubRoom) -> None:
    if room.kind != "GENERATION" or room.starters_at is not None:
        return
    issues = db.scalars(select(KnownIssue).where(KnownIssue.generation_id == room.generation_id,
                                                 KnownIssue.display_level.in_(VISIBLE_LEVELS), KnownIssue.is_demo.is_(False)))
    seen, chosen = set(), []
    for issue in sorted(issues, key=lambda i: (str(us_tech_facts._enum(i.display_level)) == "OWNER_REPORTS",
                                               us_tech_facts.SEVERITY_RANK.get(us_tech_facts._enum(i.severity), 9), i.title or "")):
        title = (issue.title or issue.component or "").strip()
        if title.lower() in seen:
            continue
        seen.add(title.lower())
        chosen.append(issue)
    for issue in chosen[:STARTERS]:
        db.add(ClubPost(room_id=room.id, user_id=None, kind="STARTER", known_issue_id=issue.id,
                        title=(issue.title or issue.component)[:160], body="", status="VISIBLE"))
    room.starters_at = datetime.now(UTC)
    db.flush()


# --- writing -----------------------------------------------------------------------------------
def active_ban(db, user: User) -> ClubBan | None:
    now = datetime.now(UTC)
    for ban in db.scalars(select(ClubBan).where(ClubBan.user_id == user.id, ClubBan.lifted_at.is_(None))):
        until = ban.until if ban.until is None or ban.until.tzinfo else ban.until.replace(tzinfo=UTC)
        if until is None or until > now:
            return ban
    return None


def check_writer(db, user: User) -> None:
    from app.services import entitlements

    entitlements.require(db, user, "CLUB_WRITE")
    if not accounts.can_write(user):
        raise ClubError(403, "EMAIL_NOT_CONFIRMED")
    if active_ban(db, user):
        raise ClubError(403, "BANNED")


def log(db, actor: str, action: str, target_type: str, target_id: str, reason: str | None = None, **details) -> None:
    db.add(ClubModerationLog(actor=actor, action=action, target_type=target_type, target_id=target_id, reason=reason, details=details))


def screen(db, text: str) -> list[str]:
    """Reasons to hold a text for a moderator (empty: publish)."""
    reasons = []
    if OBSCENE.search(text):
        reasons.append("OBSCENE")
    if len(LINK.findall(text)) > MAX_LINKS:
        reasons.append("SPAM_LINKS")
    settings = get_settings()
    if settings.club_ai_moderation and not reasons:
        verdict = ai_moderate(text)
        if verdict:
            reasons.append(f"AI:{verdict}")
    return reasons


def ai_moderate(text: str, transport=None) -> str | None:
    """Optional AI moderation (club_ai_moderation): Claude says ALLOW or a short reason to hold.
    Without a key or on an error the text is not held by the AI (the other filters still apply)."""
    from app.services.ai_mechanic import api_key

    key = api_key()
    if not key:
        return None
    settings = get_settings()
    body = {"model": settings.ai_mechanic_model, "max_tokens": 20,
            "system": "You moderate a car owners' forum. Reply with exactly ALLOW, or one word: ABUSE, SPAM, PERSONAL_DATA, ILLEGAL.",
            "messages": [{"role": "user", "content": text[:4000]}]}
    try:
        with httpx.Client(transport=transport, timeout=20) as client:
            r = client.post("https://api.anthropic.com/v1/messages", json=body,
                            headers={"x-api-key": key, "anthropic-version": "2023-06-01"})
        r.raise_for_status()
        answer = "".join(b.get("text", "") for b in r.json().get("content") or []).strip().upper()
    except (httpx.HTTPError, ValueError):
        return None
    return None if answer.startswith("ALLOW") or not answer else answer.split()[0][:20]


def _rate_limit(db, user: User, body: str) -> None:
    since = datetime.now(UTC) - timedelta(minutes=10)
    recent = db.scalars(select(ClubPost.body).where(ClubPost.user_id == user.id, ClubPost.created_at >= since)).all()
    if len(recent) >= POSTS_PER_10_MIN:
        raise ClubError(429, "TOO_MANY_POSTS")
    if body.strip() and body.strip() in {b.strip() for b in recent}:
        raise ClubError(409, "DUPLICATE_POST")


def create_post(db, user: User, room: ClubRoom, title: str, body: str, language: str) -> ClubPost:
    check_writer(db, user)
    title, body = mask_personal(title.strip(), language), mask_personal(body.strip(), language)
    _rate_limit(db, user, body)
    reasons = screen(db, f"{title}\n{body}")
    post = ClubPost(room_id=room.id, user_id=user.id, kind="POST", title=title[:160], body=body,
                    status="HELD" if reasons else "VISIBLE")
    db.add(post)
    db.flush()
    if reasons:
        log(db, "AUTOFILTER" if not any(r.startswith("AI:") for r in reasons) else "AI", "HOLD", "POST", post.id, ",".join(reasons))
    return post


def create_comment(db, user: User, post: ClubPost, body: str, language: str) -> ClubComment:
    check_writer(db, user)
    body = mask_personal(body.strip(), language)
    reasons = screen(db, body)
    comment = ClubComment(post_id=post.id, user_id=user.id, body=body, status="HELD" if reasons else "VISIBLE")
    db.add(comment)
    db.flush()
    if reasons:
        log(db, "AUTOFILTER", "HOLD", "COMMENT", comment.id, ",".join(reasons))
    return comment


def same_here(db, user: User, post: ClubPost, room: ClubRoom) -> ClubPost:
    check_writer(db, user)
    if db.scalar(select(ClubReaction).where(ClubReaction.post_id == post.id, ClubReaction.user_id == user.id)):
        return post
    db.add(ClubReaction(post_id=post.id, user_id=user.id))
    post.same_count += 1
    db.flush()
    owners = post.same_count + (1 if post.user_id and post.user_id != user.id else 0)
    threshold = get_settings().club_review_threshold
    if post.kind == "POST" and room.kind == "GENERATION" and owners >= threshold:
        item = db.scalar(select(ClubReviewItem).where(ClubReviewItem.post_id == post.id))
        if item is None:
            db.add(ClubReviewItem(post_id=post.id, room_id=room.id, owners=owners))
            log(db, "REPORTS", "QUEUE_FOR_REVIEW", "POST", post.id, f"{owners} owners")
        elif item.status == "PENDING":
            item.owners = owners
    return post


def report(db, user: User, target_type: str, target, reason: str, note: str | None) -> None:
    if db.scalar(select(ClubReport).where(ClubReport.target_type == target_type, ClubReport.target_id == target.id,
                                          ClubReport.reporter_id == user.id)):
        return
    db.add(ClubReport(target_type=target_type, target_id=target.id, reporter_id=user.id, reason=reason, note=(note or "")[:300] or None))
    target.report_count += 1
    if target.report_count >= get_settings().club_report_threshold and target.status == "VISIBLE":
        target.status = "HIDDEN"
        log(db, "REPORTS", "HIDE", target_type, target.id, f"{target.report_count} reports")
    db.flush()


def save_photo(db, user: User, post: ClubPost, data: bytes) -> ClubPhoto:
    """Re-encode the upload as JPEG: camera metadata and location are not kept."""
    from PIL import Image, ImageOps

    check_writer(db, user)
    if len(data) > MAX_PHOTO_BYTES:
        raise ClubError(413, "PHOTO_TOO_LARGE")
    if db.scalar(select(func.count()).select_from(ClubPhoto).where(ClubPhoto.post_id == post.id)) >= 4:
        raise ClubError(409, "TOO_MANY_PHOTOS")
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except Exception as exc:  # noqa: BLE001 - any undecodable upload is refused
        raise ClubError(415, "NOT_AN_IMAGE") from exc
    image = ImageOps.exif_transpose(image).convert("RGB")
    image.thumbnail((1600, 1600))
    folder = Path(get_settings().club_media_dir)
    folder.mkdir(parents=True, exist_ok=True)
    photo = ClubPhoto(post_id=post.id, user_id=user.id, path="", width=image.width, height=image.height)
    db.add(photo)
    db.flush()
    path = folder / f"{photo.id}.jpg"
    image.save(path, "JPEG", quality=85)
    photo.path = str(path)
    return photo


# --- moderation ----------------------------------------------------------------------------------
def moderate(db, moderator: User, target_type: str, target, action: str, reason: str | None) -> None:
    target.status = {"RESTORE": "VISIBLE", "REMOVE": "REMOVED", "HIDE": "HIDDEN"}[action]
    for r in db.scalars(select(ClubReport).where(ClubReport.target_type == target_type, ClubReport.target_id == target.id,
                                                 ClubReport.status == "OPEN")):
        r.status = "RESOLVED"
    log(db, moderator.id, action, target_type, target.id, reason)


def ban(db, moderator: User, user: User, reason: str, days: int | None) -> ClubBan:
    item = ClubBan(user_id=user.id, by_user_id=moderator.id, reason=reason,
                   until=datetime.now(UTC) + timedelta(days=days) if days else None)
    db.add(item)
    db.flush()
    log(db, moderator.id, "BAN", "USER", user.id, reason, days=days)
    return item


def review(db, moderator: User, item: ClubReviewItem, approve: bool, severity: str, note: str | None) -> KnownIssue | None:
    """A moderator's check of a repeated owner report. Approved -> a known issue of the generation,
    OWNER_REPORTS ("владельцы сообщают"), confidence LOW; rejected -> nothing is written."""
    item.status, item.reviewed_by, item.reviewed_at, item.note = ("APPROVED" if approve else "REJECTED"), moderator.id, datetime.now(UTC), note
    log(db, moderator.id, "REVIEW_APPROVE" if approve else "REVIEW_REJECT", "POST", item.post_id, note)
    if not approve:
        return None
    post = db.get(ClubPost, item.post_id)
    room = db.get(ClubRoom, item.room_id)
    issue = KnownIssue(
        component="owner_report", title=post.title[:240], description=post.body or post.title, symptoms=[post.title],
        severity=severity, confidence="LOW", inspection_recommendation="", status="NEEDS_INSPECTION",
        scope_level="GENERATION", display_level="OWNER_REPORTS", make_id=room.make_id, generation_id=room.generation_id,
        year_from=room.year_from, year_to=room.year_to, source_count=item.owners, evidence_ids=[f"club_post:{post.id}"],
        conditions={"origin": "owners_club", "review_id": item.id, "owners": item.owners}, data_origin="REAL", is_demo=False,
        natural_key=f"club-{item.id}"[:64])
    db.add(issue)
    db.flush()
    item.known_issue_id = issue.id
    return issue


# --- views (no personal data) -------------------------------------------------------------------
def room_view(room: ClubRoom, language: str, posts: int | None = None) -> dict:
    years = f" ({room.year_from}–{room.year_to})" if room.year_from else ""
    return {"id": room.id, "kind": room.kind, "title": room.title + years, "posts": posts}


def _starter_body(db, post: ClubPost, language: str) -> dict:
    issue = db.get(KnownIssue, post.known_issue_id) if post.known_issue_id else None
    if issue is None:
        return {"title": post.title, "body": "", "mark": None}
    translate = us_tech_facts.Translator(db, language)
    title = translate("issue_title", issue.title) if issue.title else translate("issue_component", issue.component)
    lines = []
    symptoms = [translate("issue_symptom", s) for s in issue.symptoms or [] if s]
    if symptoms:
        lines.append(f"{tr(language, 'symptoms')}: {'; '.join(symptoms[:5])}")
    if issue.inspection_recommendation:
        lines.append(f"{tr(language, 'check')}: {translate('issue_inspection', issue.inspection_recommendation)}")
    lines.append(tr(language, "starter_note"))
    level = us_tech_facts._enum(issue.display_level)
    mark = {"SECONDARY_NOTE": ("по данным справочников", "məlumat kitabçalarına görə", "per reference sources"),
            "OWNER_REPORTS": ("владельцы сообщают", "sahiblər bildirir", "owners report")}.get(level)
    return {"title": title, "body": "\n".join(lines), "mark": pick(language, *mark) if mark else None}


def post_view(db, post: ClubPost, viewer: User, language: str, *, full: bool = False) -> dict:
    author = db.get(User, post.user_id) if post.user_id else None
    text = _starter_body(db, post, language) if post.kind == "STARTER" else {"title": post.title, "body": post.body, "mark": None}
    me_too = bool(db.scalar(select(ClubReaction).where(ClubReaction.post_id == post.id, ClubReaction.user_id == viewer.id)))
    out = {"id": post.id, "room_id": post.room_id, "kind": post.kind, **text, "author": display_name(author, language),
           "mine": post.user_id == viewer.id, "status": post.status, "same_count": post.same_count, "me_too": me_too,
           "created_at": post.created_at.isoformat() if post.created_at else None,
           "held_note": tr(language, "held") if post.status == "HELD" else None,
           "comments": db.scalar(select(func.count()).select_from(ClubComment).where(ClubComment.post_id == post.id,
                                                                                    ClubComment.status == "VISIBLE")) or 0,
           "photos": [f"/club/photos/{p.id}" for p in db.scalars(select(ClubPhoto).where(ClubPhoto.post_id == post.id))]}
    if full:
        comments = db.scalars(select(ClubComment).where(ClubComment.post_id == post.id).order_by(ClubComment.created_at))
        out["comment_list"] = [{"id": c.id, "author": display_name(db.get(User, c.user_id), language), "mine": c.user_id == viewer.id,
                                "body": c.body, "status": c.status, "held_note": tr(language, "held") if c.status == "HELD" else None,
                                "created_at": c.created_at.isoformat() if c.created_at else None}
                               for c in comments if c.status == "VISIBLE" or c.user_id == viewer.id or viewer.is_admin]
    return out


def visible(post_or_comment, viewer: User) -> bool:
    status = post_or_comment.status
    return status == "VISIBLE" or (status == "HELD" and post_or_comment.user_id == viewer.id) or viewer.is_admin
