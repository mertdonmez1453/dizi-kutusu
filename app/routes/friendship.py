# FRIENDSHIP ROUTES: Kullanıcıların birbirini takip etmesi / arkadaşlık işlemleri

from flask import Blueprint, jsonify, request, session
from app.db import db
from app.models.user import User
from app.models.friendship import Friendship

friendship_bp = Blueprint("friendship", __name__, url_prefix="/api/friendships")


def get_current_user():
    """Session'dan giriş yapmış kullanıcıyı döndürür."""
    email = session.get("user")
    if not email:
        return None
    return User.query.filter_by(email=email).first()


# QUERY: Giriş yapan kullanıcının takip ettiği (following) kişileri listeler (SELECT + JOIN)
@friendship_bp.get("/following")
def get_following():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Giriş yapmalısınız"}), 401

    # user.following ilişkisi models'te tanımlandı
    following_list = user.following.all()
    
    result = []
    for f in following_list:
        followed_user = f.followed
        result.append({
            "friendship_id": f.id,
            "user_id": followed_user.id,
            "email": followed_user.email,
            "followed_at": f.created_at.isoformat()
        })
    return jsonify(result)


# QUERY: Giriş yapan kullanıcıyı takip edenleri (followers) listeler (SELECT + JOIN)
@friendship_bp.get("/followers")
def get_followers():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Giriş yapmalısınız"}), 401

    # user.followers ilişkisi models'te tanımlandı
    follower_list = user.followers.all()
    
    result = []
    for f in follower_list:
        follower_user = f.follower
        result.append({
            "friendship_id": f.id,
            "user_id": follower_user.id,
            "email": follower_user.email,
            "followed_at": f.created_at.isoformat()
        })
    return jsonify(result)


# QUERY: Başka bir kullanıcıyı takip et (INSERT)
@friendship_bp.post("/follow")
def follow_user():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Giriş yapmalısınız"}), 401

    data = request.get_json()
    followed_id = data.get("user_id")

    # Kendi kendini takip edemez
    if user.id == followed_id:
        return jsonify({"error": "Kendinizi takip edemezsiniz"}), 400

    # QUERY: Takip edilmek istenen kullanıcı var mı? (SELECT)
    target_user = User.query.get(followed_id)
    if not target_user:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 404

    # QUERY: Zaten takip ediyor mu? (SELECT)
    existing = Friendship.query.filter_by(
        follower_id=user.id, 
        followed_id=followed_id
    ).first()
    
    if existing:
        return jsonify({"error": "Bu kullanıcıyı zaten takip ediyorsunuz"}), 409

    new_follow = Friendship(follower_id=user.id, followed_id=followed_id)
    db.session.add(new_follow)
    db.session.commit()

    return jsonify({"message": f"{target_user.email} başarıyla takip edildi"}), 201


# QUERY: Takipten çık (DELETE)
@friendship_bp.delete("/unfollow/<int:target_user_id>")
def unfollow_user(target_user_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "Giriş yapmalısınız"}), 401

    # QUERY: Takip ilişkisi var mı? (SELECT)
    friendship = Friendship.query.filter_by(
        follower_id=user.id, 
        followed_id=target_user_id
    ).first()

    if not friendship:
        return jsonify({"error": "Bu kullanıcıyı takip etmiyorsunuz"}), 404

    db.session.delete(friendship)
    db.session.commit()

    return jsonify({"message": "Takipten çıkıldı"})
