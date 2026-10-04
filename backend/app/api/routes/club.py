# ruff: noqa: E501
"""The owners club API (product phase, stage 4), behind owners_club_v1: on in the preview, off in
production. Reading needs a signed-in user; writing a confirmed email (club.check_writer);
moderation endpoints need a moderator (is_admin). No response carries another user's e-mail."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, File, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.api.dependencies import AdminUser, CurrentUser, DBSession
from app.models.club import (
    ClubComment,
    ClubModerationLog,
    ClubPhoto,
    ClubPost,
    ClubReport,
    ClubReviewItem,
    ClubRoom,
)
from app.models.garage import GarageVehicle
from app.models.user import User
from app.services import club

router = APIRouter(prefix="/club", tags=["owners-club"])
Language = Literal["ru", "az", "en"]


def _enabled() -> None:
    if not club.enabled():
        raise HTTPException(404, "CLUB_DISABLED")


def _run(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except club.ClubError as exc:
        raise HTTPException(exc.status, exc.code) from None


class PostIn(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    body: str = Field(default="", max_length=8000)


class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class ReportIn(BaseModel):
    target_type: Literal["POST", "COMMENT"]
    target_id: str = Field(max_length=36)
    reason: Literal["SPAM", "ABUSE", "PERSONAL_DATA", "OFF_TOPIC", "OTHER"]
    note: str | None = Field(default=None, max_length=300)


class ProfileIn(BaseModel):
    display_name: str = Field(min_length=3, max_length=40)


class ModerateIn(BaseModel):
    action: Literal["RESTORE", "REMOVE", "HIDE"]
    reason: str | None = Field(default=None, max_length=300)


class BanIn(BaseModel):
    post_id: str | None = None
    comment_id: str | None = None
    reason: str = Field(min_length=3, max_length=300)
    days: int | None = Field(default=None, ge=1, le=3650)


class ReviewIn(BaseModel):
    approve: bool
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    note: str | None = Field(default=None, max_length=1000)


def _room(db, room_id: str) -> ClubRoom:
    room = db.get(ClubRoom, room_id)
    if room is None:
        raise HTTPException(404, "ROOM_NOT_FOUND")
    return room


def _post(db, post_id: str, user: User) -> ClubPost:
    post = db.get(ClubPost, post_id)
    if post is None or not club.visible(post, user):
        raise HTTPException(404, "POST_NOT_FOUND")
    return post


def _count(db, room_id: str) -> int:
    return db.scalar(select(func.count()).select_from(ClubPost).where(ClubPost.room_id == room_id, ClubPost.status == "VISIBLE")) or 0


@router.get("/rooms")
def rooms(db: DBSession, user: CurrentUser, language: Language = "ru") -> dict:
    _enabled()
    club.ensure_rooms(db)
    mine = []
    for vehicle in db.scalars(select(GarageVehicle).where(GarageVehicle.user_id == user.id)):
        for room in club.rooms_for_vehicle(db, vehicle):
            mine.append(club.room_view(room, language, _count(db, room.id)) | {"vehicle": f"{vehicle.make} {vehicle.model} {vehicle.year}"})
    makes = []
    all_rooms = list(db.scalars(select(ClubRoom).order_by(ClubRoom.title)))
    for room in [r for r in all_rooms if r.kind == "MAKE"]:
        makes.append(club.room_view(room, language) | {"generations": sum(1 for r in all_rooms if r.kind == "GENERATION" and r.make_id == room.make_id)})
    db.commit()
    return {"mine": mine, "makes": makes, "can_write": club.accounts.can_write(user) and not club.active_ban(db, user)}


@router.get("/vehicles/{vehicle_id}/rooms")
def vehicle_rooms(vehicle_id: str, db: DBSession, user: CurrentUser, language: Language = "ru") -> list[dict]:
    _enabled()
    vehicle = db.get(GarageVehicle, vehicle_id)
    if vehicle is None or vehicle.user_id != user.id:
        raise HTTPException(404, "VEHICLE_NOT_FOUND")
    out = [club.room_view(r, language, _count(db, r.id)) for r in club.rooms_for_vehicle(db, vehicle)]
    db.commit()
    return out


@router.get("/rooms/{room_id}")
def room(room_id: str, db: DBSession, user: CurrentUser, language: Language = "ru") -> dict:
    _enabled()
    current = _room(db, room_id)
    club.ensure_starters(db, current)
    posts = [p for p in db.scalars(select(ClubPost).where(ClubPost.room_id == current.id)) if club.visible(p, user)]
    posts.sort(key=lambda p: (p.kind == "STARTER", -(p.created_at.timestamp() if p.created_at and p.kind == "POST" else 0)))
    out = club.room_view(current, language) | {"posts": [club.post_view(db, p, user, language) for p in posts]}
    if current.kind == "MAKE":
        gens = db.scalars(select(ClubRoom).where(ClubRoom.kind == "GENERATION", ClubRoom.make_id == current.make_id).order_by(ClubRoom.title))
        out["generations"] = [club.room_view(g, language) for g in gens]
    db.commit()
    return out


@router.post("/rooms/{room_id}/posts", status_code=201)
def create_post(room_id: str, value: PostIn, db: DBSession, user: CurrentUser, language: Language = "ru") -> dict:
    _enabled()
    post = _run(club.create_post, db, user, _room(db, room_id), value.title, value.body, language)
    db.commit()
    return club.post_view(db, post, user, language, full=True)


@router.get("/posts/{post_id}")
def post(post_id: str, db: DBSession, user: CurrentUser, language: Language = "ru") -> dict:
    _enabled()
    return club.post_view(db, _post(db, post_id, user), user, language, full=True)


@router.post("/posts/{post_id}/comments", status_code=201)
def comment(post_id: str, value: CommentIn, db: DBSession, user: CurrentUser, language: Language = "ru") -> dict:
    _enabled()
    target = _post(db, post_id, user)
    _run(club.create_comment, db, user, target, value.body, language)
    db.commit()
    return club.post_view(db, target, user, language, full=True)


@router.post("/posts/{post_id}/same")
def same(post_id: str, db: DBSession, user: CurrentUser, language: Language = "ru") -> dict:
    _enabled()
    target = _post(db, post_id, user)
    _run(club.same_here, db, user, target, _room(db, target.room_id))
    db.commit()
    return club.post_view(db, target, user, language, full=True)


@router.post("/posts/{post_id}/photos", status_code=201)
async def photo(post_id: str, db: DBSession, user: CurrentUser, file: Annotated[UploadFile, File()]) -> dict:
    _enabled()
    target = _post(db, post_id, user)
    if target.user_id != user.id:
        raise HTTPException(403, "NOT_YOUR_POST")
    data = await file.read(club.MAX_PHOTO_BYTES + 1)
    saved = _run(club.save_photo, db, user, target, data)
    db.commit()
    return {"url": f"/club/photos/{saved.id}", "width": saved.width, "height": saved.height}


@router.get("/photos/{photo_id}")
def photo_file(photo_id: str, db: DBSession, user: CurrentUser) -> FileResponse:
    _enabled()
    item = db.get(ClubPhoto, photo_id)
    if item is None:
        raise HTTPException(404, "PHOTO_NOT_FOUND")
    _post(db, item.post_id, user)
    return FileResponse(item.path, media_type="image/jpeg")


@router.post("/reports", status_code=201)
def report(value: ReportIn, db: DBSession, user: CurrentUser) -> dict:
    _enabled()
    target = db.get(ClubPost if value.target_type == "POST" else ClubComment, value.target_id)
    if target is None or not club.visible(target, user):
        raise HTTPException(404, "TARGET_NOT_FOUND")
    club.report(db, user, value.target_type, target, value.reason, value.note)
    db.commit()
    return {"ok": True}


@router.patch("/profile")
def profile(value: ProfileIn, db: DBSession, user: CurrentUser, language: Language = "ru") -> dict:
    _enabled()
    name = club.mask_personal(value.display_name.strip(), language)
    if club.screen(db, name):
        raise HTTPException(422, "NAME_NOT_ALLOWED")
    user.display_name = name
    db.commit()
    return {"display_name": user.display_name}


# --- moderators ----------------------------------------------------------------------------------
@router.get("/moderation")
def moderation(db: DBSession, moderator: AdminUser, language: Language = "ru") -> dict:
    _enabled()
    held_posts = db.scalars(select(ClubPost).where(ClubPost.status.in_(("HELD", "HIDDEN"))))
    held_comments = db.scalars(select(ClubComment).where(ClubComment.status.in_(("HELD", "HIDDEN"))))
    reports = db.scalars(select(ClubReport).where(ClubReport.status == "OPEN").order_by(ClubReport.created_at))
    queue = db.scalars(select(ClubReviewItem).where(ClubReviewItem.status == "PENDING"))
    return {
        "posts": [club.post_view(db, p, moderator, language) | {"author_ref": p.user_id} for p in held_posts],
        "comments": [{"id": c.id, "post_id": c.post_id, "body": c.body, "status": c.status, "author_ref": c.user_id} for c in held_comments],
        "reports": [{"id": r.id, "target_type": r.target_type, "target_id": r.target_id, "reason": r.reason, "note": r.note} for r in reports],
        "review": [{"id": q.id, "owners": q.owners, "post": club.post_view(db, db.get(ClubPost, q.post_id), moderator, language),
                    "room": club.room_view(db.get(ClubRoom, q.room_id), language)} for q in queue],
    }


@router.post("/moderation/targets/{target_type}/{target_id}")
def moderate(target_type: Literal["POST", "COMMENT"], target_id: str, value: ModerateIn, db: DBSession, moderator: AdminUser) -> dict:
    _enabled()
    target = db.get(ClubPost if target_type == "POST" else ClubComment, target_id)
    if target is None:
        raise HTTPException(404, "TARGET_NOT_FOUND")
    club.moderate(db, moderator, target_type, target, value.action, value.reason)
    db.commit()
    return {"status": target.status}


@router.post("/moderation/ban", status_code=201)
def ban(value: BanIn, db: DBSession, moderator: AdminUser) -> dict:
    """Ban the author of a post or comment (moderators see authors only through their texts)."""
    _enabled()
    source = db.get(ClubPost, value.post_id) if value.post_id else db.get(ClubComment, value.comment_id) if value.comment_id else None
    if source is None or not source.user_id:
        raise HTTPException(404, "AUTHOR_NOT_FOUND")
    item = club.ban(db, moderator, db.get(User, source.user_id), value.reason, value.days)
    db.commit()
    return {"id": item.id, "until": item.until.isoformat() if item.until else None}


@router.post("/moderation/review/{item_id}")
def review(item_id: str, value: ReviewIn, db: DBSession, moderator: AdminUser) -> dict:
    _enabled()
    item = db.get(ClubReviewItem, item_id)
    if item is None or item.status != "PENDING":
        raise HTTPException(404, "REVIEW_ITEM_NOT_FOUND")
    issue = club.review(db, moderator, item, value.approve, value.severity, value.note)
    db.commit()
    return {"status": item.status, "known_issue_id": issue.id if issue else None}


@router.get("/moderation/log")
def moderation_log(db: DBSession, moderator: AdminUser) -> list[dict]:
    _enabled()
    rows = db.scalars(select(ClubModerationLog).order_by(ClubModerationLog.created_at.desc()).limit(500))
    return [{"at": r.created_at.isoformat() if r.created_at else None, "actor": r.actor, "action": r.action, "target_type": r.target_type,
             "target_id": r.target_id, "reason": r.reason} for r in rows]


@router.delete("/posts/{post_id}", status_code=204)
def delete_own_post(post_id: str, db: DBSession, user: CurrentUser) -> Response:
    _enabled()
    target = _post(db, post_id, user)
    if target.user_id != user.id:
        raise HTTPException(403, "NOT_YOUR_POST")
    target.status = "REMOVED"
    club.log(db, user.id, "AUTHOR_REMOVE", "POST", target.id)
    db.commit()
    return Response(status_code=204)
