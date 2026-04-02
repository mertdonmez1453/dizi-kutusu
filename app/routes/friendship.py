from flask import Blueprint, jsonify, request, g
from app.db import db
from app.models.user import User
from app.models.friendship import Friendship
from app.models.watchlist import Watchlist
from app.models.review import Review
from app.utils import login_required
from sqlalchemy import desc

friendship_bp = Blueprint("friendship", __name__, url_prefix="/api/friendships")


# QUERY: Giriş yapan kullanıcının takip ettiği kişileri listeler (SELECT + JOIN)
@friendship_bp.get("/following")
@login_required
def get_following():
    user = g.current_user
    following_list = user.following.all()

    return jsonify([
        {
            "friendship_id": f.id,
            "user_id": f.followed.id,
            "email": f.followed.email,
            "followed_at": f.created_at.isoformat()
        }
        for f in following_list
    ])


# QUERY: Giriş yapan kullanıcıyı takip edenleri listeler (SELECT + JOIN)
@friendship_bp.get("/followers")
@login_required
def get_followers():
    user = g.current_user
    follower_list = user.followers.all()

    return jsonify([
        {
            "friendship_id": f.id,
            "user_id": f.follower.id,
            "email": f.follower.email,
            "followed_at": f.created_at.isoformat()
        }
        for f in follower_list
    ])


# QUERY: Bir kullanıcıyı takip edip etmediğini kontrol eder (SELECT)
@friendship_bp.get("/check/<int:target_user_id>")
@login_required
def check_friendship(target_user_id):
    user = g.current_user
    existing = Friendship.query.filter_by(
        follower_id=user.id, followed_id=target_user_id
    ).first()
    return jsonify({"is_following": existing is not None})


# QUERY: Başka bir kullanıcıyı takip et (INSERT)
@friendship_bp.post("/follow/<int:target_user_id>")
@login_required
def follow_user(target_user_id):
    user = g.current_user

    if user.id == target_user_id:
        return jsonify({"error": "Kendinizi takip edemezsiniz."}), 400

    target_user = User.query.get_or_404(target_user_id)

    existing = Friendship.query.filter_by(
        follower_id=user.id, followed_id=target_user_id
    ).first()
    if existing:
        return jsonify({"error": "Bu kullanıcıyı zaten takip ediyorsunuz."}), 409

    new_follow = Friendship(follower_id=user.id, followed_id=target_user_id)
    db.session.add(new_follow)
    db.session.commit()

    return jsonify({"message": f"'{target_user.email}' takip edildi."}), 201


# QUERY: Takipten çık (DELETE)
@friendship_bp.delete("/unfollow/<int:target_user_id>")
@login_required
def unfollow_user(target_user_id):
    user = g.current_user

    friendship = Friendship.query.filter_by(
        follower_id=user.id, followed_id=target_user_id
    ).first()
    if not friendship:
        return jsonify({"error": "Bu kullanıcıyı takip etmiyorsunuz."}), 404

    db.session.delete(friendship)
    db.session.commit()

    return jsonify({"message": "Takipten çıkıldı."})


# QUERY: Kullanıcı arama — arkadaş eklemek için e-posta ile arama (SELECT)
@friendship_bp.get("/search")
@login_required
def search_users():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Arama parametresi gerekli (?q=...)"}), 400

    user = g.current_user
    users = User.query.filter(
        User.email.ilike(f"%{q}%"),
        User.id != user.id
    ).limit(20).all()

    following_ids = {f.followed_id for f in user.following.all()}

    return jsonify([
        {
            "id": u.id,
            "email": u.email,
            "is_following": u.id in following_ids
        }
        for u in users
    ])


# QUERY: Bir arkadaşın izleme listesini görüntüle (SELECT + JOIN)
@friendship_bp.get("/<int:target_user_id>/watchlist")
@login_required
def get_friend_watchlist(target_user_id):
    user = g.current_user

    is_following = Friendship.query.filter_by(
        follower_id=user.id, followed_id=target_user_id
    ).first()
    if not is_following:
        return jsonify({"error": "Bu kullanıcının listesini görmek için takip etmelisiniz."}), 403

    items = Watchlist.query.filter_by(user_id=target_user_id).all()

    return jsonify([
        {
            "series_id": item.series.id,
            "title": item.series.title,
            "image_url": item.series.image_url,
            "status": item.status,
            "rating": item.series.rating
        }
        for item in items
    ])


# QUERY: Bir arkadaşın verdiği puanları/yorumları görüntüle (SELECT + JOIN)
@friendship_bp.get("/<int:target_user_id>/reviews")
@login_required
def get_friend_reviews(target_user_id):
    user = g.current_user

    is_following = Friendship.query.filter_by(
        follower_id=user.id, followed_id=target_user_id
    ).first()
    if not is_following:
        return jsonify({"error": "Bu kullanıcının yorumlarını görmek için takip etmelisiniz."}), 403

    reviews = Review.query.filter_by(user_id=target_user_id).order_by(Review.created_at.desc()).all()

    return jsonify([
        {
            "id": r.id,
            "series_id": r.series_id,
            "series_title": r.series.title,
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat()
        }
        for r in reviews
    ])


@friendship_bp.get("/feed")
@login_required
def activity_feed():
    user = g.current_user
    limit = request.args.get("limit", 20, type=int)
    limit = max(1, min(limit, 50))

    following_ids = [f.followed_id for f in user.following.all()]
    if not following_ids:
        return jsonify([])

    activities = []

    recent_reviews = Review.query.filter(
        Review.user_id.in_(following_ids)
    ).order_by(desc(Review.created_at)).limit(limit).all()

    for r in recent_reviews:
        activity = {
            "type": "comment" if r.comment else "rating",
            "user_id": r.user.id,
            "email": r.user.email,
            "series_id": r.series_id,
            "series_title": r.series.title,
            "series_image": r.series.image_url,
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat()
        }
        activities.append(activity)

    recent_watchlist = Watchlist.query.filter(
        Watchlist.user_id.in_(following_ids)
    ).order_by(desc(Watchlist.added_at)).limit(limit).all()

    for w in recent_watchlist:
        activity = {
            "type": "watchlist",
            "user_id": w.user.id,
            "email": w.user.email,
            "series_id": w.series_id,
            "series_title": w.series.title,
            "series_image": w.series.image_url,
            "status": w.status,
            "created_at": w.added_at.isoformat()
        }
        activities.append(activity)

    activities.sort(key=lambda x: x["created_at"], reverse=True)

    return jsonify(activities[:limit])
