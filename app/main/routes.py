from datetime import datetime
from os import remove, path
from glob import glob

from flask import render_template, flash, redirect, url_for, request, g, \
    abort, current_app as ca, jsonify
from flask_babel import _, get_locale
from flask_login import login_required, logout_user, current_user as cu

from app import session, photos
from app.containers import NotificationType
from app.main import bp
from app.main.forms import EditProfileForm, PostForm, AdminPostForm, ReplyForm
from app.models import User, Post, Notification
from app.festival.logic import get_partner_selection, remove_partner


@bp.before_app_request
def before_request():
    if cu.is_authenticated:
        cu.last_seen = datetime.utcnow()
        session.commit()
    if not cu.is_anonymous and cu.is_suspended:
        flash(_("Your account has been suspended."))
        ca.logger.info("Suspended user >{}< was kicked from server"
                       .format(cu.username))
        logout_user()
    g.locale = str(get_locale())


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
@login_required
def index():
    form = PostForm()
    if cu.is_admin():
        form = AdminPostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=cu)
        if cu.is_admin():
            post.is_pinned = form.is_pinned.data
        session.add(post)
        session.commit()
        ca.logger.info(">{}< added post >{}<"
                       .format(cu.username, post.id))
        flash(_("Your post is now live!"))
        return redirect(url_for("main.index"))
    page = request.args.get("page", 1, type=int)
    posts = session.query(Post).filter(Post.parent_id == None).order_by(  # noqa: E711
        Post.is_pinned.desc(),
        Post.internal_time.desc()
    ).paginate(page, ca.config["POSTS_PER_PAGE"], False)

    next_url = url_for("main.index", page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for("main.index", page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("main/index.html", title=_("Home"),
                           form=form, posts=posts.items,
                           on_index_page=True,
                           next_url=next_url, prev_url=prev_url)


@bp.route("/reply_post/<post_id>", methods=["GET", "POST"])
@login_required
def reply_post(post_id):
    form = ReplyForm()
    post = session.query(Post).get(post_id)
    if form.validate_on_submit():
        reply = Post(body=form.post.data, author=cu)
        reply.parent_id = post.id
        post.internal_time = datetime.utcnow()
        session.add(post)
        session.commit()
        ca.logger.info(">{}< replied with post >{}<"
                       .format(cu.username, reply.id))
        flash(_("Your reply is now live!"))
        return redirect(url_for("main.index"))
    return render_template("main/reply.html", title=_("Reply to Post"),
                           form=form, post=post, on_index_page=False)


@bp.route("/edit_post/<post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = session.query(Post).get(post_id)
    if post.author == cu:
        if cu.is_admin():
            form = AdminPostForm()
            if request.method == "GET":
                form.post.data = post.body
                form.is_pinned.data = post.is_pinned
            elif form.validate_on_submit():
                post.body = form.post.data
                post.is_pinned = form.is_pinned.data
                post.timestamp = datetime.utcnow()
                post.internal_time = datetime.utcnow()
                if post.parent_id is not None:
                    parent = session.query(Post).get(post.parent_id)
                    parent.internal_time = datetime.utcnow()
        else:
            form = PostForm()
            if request.method == "GET":
                form.post.data = post.body
            elif form.validate_on_submit:
                post.body = form.post.data

        if request.method == "POST":
            session.commit()
            ca.logger.info(
                ">{}< has edited post >{}<"
                .format(cu.username, post.id))
            flash(_("Your changes have been saved."))
            return redirect(url_for("main.index"))

        is_parent = post.parent_id is None
        return render_template("main/edit_post.html",
                               form=form, is_parent=is_parent,
                               heading=_("Edit Post"))
    else:
        ca.logger.warn("Blocked editing of post >{}< for user >{}<".format(
            post_id, cu.username
        ))
        abort(403)


@bp.route("/user/<username>")
@login_required
def user(username):
    u = session.query(User).filter_by(username=username).first_or_404()
    if u == cu:
        cu.add_notification(NotificationType.admin, 0)
        session.commit()
    page = request.args.get("page", 1, type=int)
    if username == cu.username:
        ca.logger.info(">{}< entered own profile page".format(username))
    else:
        ca.logger.info(">{}< stalks >{}<"
                       .format(cu.username, username))
    posts = u.posts.order_by(Post.timestamp.desc()).paginate(
        page, ca.config["POSTS_PER_PAGE"], False)
    next_url = url_for("main.user", username=u.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for("main.user", username=u.username,
                       page=posts.prev_num) if posts.has_prev else None
    return render_template("main/user.html", user=u, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route("/members")
@login_required
def members():
    page = request.args.get("page", 1, type=int)
    users = session.query(User).filter(
        User.username.isnot(None)).order_by(
            User.access_level.desc(), User.username) \
        .paginate(page, ca.config["POSTS_PER_PAGE"], False)
    next_url = url_for("main.members",
                       page=users.next_num) if users.has_next else None
    prev_url = url_for("main.members",
                       page=users.prev_num) if users.has_prev else None
    ca.logger.info(">{}< checksout member\"s page"
                   .format(cu.username))
    return render_template("main/user_overview.html", users=users.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(cu.username, cu.partner_id)
    form.partner.choices = get_partner_selection()
    if form.validate_on_submit():
        cu.username = form.username.data
        cu.about_me = form.about_me.data
        cu.water_demand = form.water.data
        cu.beer_demand = form.beer.data
        cu.mixed_demand = form.mixed.data

        file_storage = request.files.getlist("photo")
        if len(file_storage) > 0 and file_storage[0].filename != "":
            photo_path = ca.config["UPLOADED_PHOTOS_DEST"]
            search_pattern = "/*{}*".format(cu.registration_code)
            result = glob(photo_path + search_pattern)
            if len(result) == 1 and path.exists(result[0]):
                remove(result[0])
            filename = file_storage[0]
            photos.save(filename, name=cu.registration_code + ".")

        # -1 will be returned by partner.data, if no partner was selected
        if form.partner.data != -1:
            partner_id = form.partner.data
            cu.partner_id = partner_id
            partner = session.query(User).get(partner_id)
            partner.partner_id = cu.id
        else:
            remove_partner(cu)
        session.commit()
        flash(_("Your changes have been saved."))
        ca.logger.info(">{}< has changed profile data".format(cu.username))
        return redirect(url_for("main.edit_profile"))
    elif request.method == "GET":
        form.username.data = cu.username
        form.about_me.data = cu.about_me
        form.water.data = cu.water_demand
        form.beer.data = cu.beer_demand
        form.mixed.data = cu.mixed_demand

        partner_id = cu.partner_id
        if partner_id:
            form.partner.data = partner_id
        ca.logger.info(">{}< enters edit profile page"
                       .format(cu.username))
    return render_template("main/edit_profile.html", title=_("Edit Profile"),
                           form=form)


@bp.route("/notifications")
@login_required
def notifications():
    since = request.args.get("since", 0.0, type=float)
    notification_list = cu.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        "name": n.name,
        "data": n.get_data(),
        "timestamp": n.timestamp
    } for n in notification_list])


@bp.route("/user/<username>/popup")
@login_required
def user_popup(username):
    u = session.query(User).filter_by(username=username).first_or_404()
    return render_template("main/user_popup.html", user=u)


@bp.route("/delete_post/<post_id>", methods=["GET", "POST"])
@login_required
def delete_post(post_id):
    if cu.is_admin():
        post = session.query(Post).get(post_id)
        name = post.author.username

        for reply in post.get_replies():
            session.delete(reply)
        session.flush()

        session.delete(post)
        session.commit()
        ca.logger.info(">{}< deleted post >{}< by >{}<".format(
            cu.username, post_id, name
        ))
        flash(_("Post has been deleted."))
        return redirect(url_for("main.index"))
    else:
        ca.logger.warn("Blocked post deletion for >{}<"
                       .format(cu.username))
        abort(403)
