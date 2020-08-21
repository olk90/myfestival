from datetime import datetime
from os import remove, path
from glob import glob

from flask import render_template, flash, redirect, url_for, request, g, \
    abort, current_app as ca, jsonify
from flask_babel import _, get_locale
from flask_login import current_user, login_required, logout_user

from app import db, photos
from app.containers import NotificationType
from app.main import bp
from app.main.forms import EditProfileForm, PostForm, AdminPostForm, ReplyForm
from app.models import User, Post, Notification
from app.festival.logic import get_partner_selection, remove_partner


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    if not current_user.is_anonymous and current_user.is_suspended:
        flash(_('Your account has been suspended.'))
        ca.logger.info('Suspended user >{}< was kicked from server'
                       .format(current_user.username))
        logout_user()
    g.locale = str(get_locale())


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if current_user.is_admin():
        form = AdminPostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        if current_user.is_admin():
            post.is_pinned = form.is_pinned.data
        db.session.add(post)
        db.session.commit()
        ca.logger.info('>{}< added post >{}<'
                       .format(current_user.username, post.id))
        flash(_('Your post is now live!'))
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter(Post.parent_id == None).order_by(  # noqa: E711
        Post.is_pinned.desc(),
        Post.internal_time.desc()
    ).paginate(page, ca.config['POSTS_PER_PAGE'], False)

    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('main/index.html', title=_('Home'),
                           form=form, posts=posts.items,
                           on_index_page=True,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/reply_post/<post_id>', methods=['GET', 'POST'])
@login_required
def reply_post(post_id):
    form = ReplyForm()
    post = Post.query.get(post_id)
    if form.validate_on_submit():
        reply = Post(body=form.post.data, author=current_user)
        reply.parent_id = post.id
        post.internal_time = datetime.utcnow()
        db.session.add(post)
        db.session.commit()
        ca.logger.info('>{}< replied with post >{}<'
                       .format(current_user.username, reply.id))
        flash(_('Your reply is now live!'))
        return redirect(url_for('main.index'))
    return render_template('main/reply.html', title=_('Reply to Post'),
                           form=form, post=post, on_index_page=False)


@bp.route('/edit_post/<post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get(post_id)
    if post.author == current_user:
        if current_user.is_admin():
            form = AdminPostForm()
            if request.method == 'GET':
                form.post.data = post.body
                form.is_pinned.data = post.is_pinned
            elif form.validate_on_submit():
                post.body = form.post.data
                post.is_pinned = form.is_pinned.data
                post.timestamp = datetime.utcnow()
                post.internal_time = datetime.utcnow()
                if post.parent_id is not None:
                    parent = Post.query.get(post.parent_id)
                    parent.internal_time = datetime.utcnow()
        else:
            form = PostForm()
            if request.method == 'GET':
                form.post.data = post.body
            elif form.validate_on_submit:
                post.body = form.post.data

        if request.method == 'POST':
            db.session.commit()
            ca.logger.info(
                '>{}< has edited post >{}<'
                .format(current_user.username, post.id))
            flash(_('Your changes have been saved.'))
            return redirect(url_for('main.index'))

        is_parent = post.parent_id is None
        return render_template('main/edit_post.html',
                               form=form, is_parent=is_parent,
                               heading=_('Edit Post'))
    else:
        ca.logger.warn('Blocked editing of post >{}< for user >{}<'.format(
            post_id, current_user.username
        ))
        abort(403)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user:
        current_user.add_notification(NotificationType.admin, 0)
        db.session.commit()
    page = request.args.get('page', 1, type=int)
    if username == current_user.username:
        ca.logger.info('>{}< entered own profile page'.format(username))
    else:
        ca.logger.info('>{}< stalks >{}<'
                       .format(current_user.username, username))
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, ca.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    return render_template('main/user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/members')
@login_required
def members():
    page = request.args.get('page', 1, type=int)
    users = User.query.filter(
        User.username.isnot(None)).order_by(
            User.access_level.desc(), User.username) \
        .paginate(page, ca.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.members',
                       page=users.next_num) if users.has_next else None
    prev_url = url_for('main.members',
                       page=users.prev_num) if users.has_prev else None
    ca.logger.info('>{}< checksout member\'s page'
                   .format(current_user.username))
    return render_template('main/user_overview.html', users=users.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username, current_user.partner_id)
    form.partner.choices = get_partner_selection()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        current_user.water_demand = form.water.data
        current_user.beer_demand = form.beer.data
        current_user.mixed_demand = form.mixed.data

        file_storage = request.files.getlist('photo')
        if len(file_storage) > 0 and file_storage[0].filename != '':
            photo_path = ca.config['UPLOADED_PHOTOS_DEST']
            search_pattern = '/*{}*'.format(current_user.registration_code)
            result = glob(photo_path + search_pattern)
            if len(result) == 1 and path.exists(result[0]):
                remove(result[0])
            filename = file_storage[0]
            photos.save(filename, name=current_user.registration_code + '.')

        # -1 will be returned by partner.data, if no partner was selected
        if form.partner.data != -1:
            partner_id = form.partner.data
            current_user.partner_id = partner_id
            partner = User.query.get(partner_id)
            partner.partner_id = current_user.id
        else:
            remove_partner(current_user)
        db.session.commit()
        flash(_('Your changes have been saved.'))
        ca.logger.info('>{}< has changed profile data'
                       .format(current_user.username))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
        form.water.data = current_user.water_demand
        form.beer.data = current_user.beer_demand
        form.mixed.data = current_user.mixed_demand

        partner_id = current_user.partner_id
        if partner_id:
            form.partner.data = partner_id
        ca.logger.info('>{}< enters edit profile page'
                       .format(current_user.username))
    return render_template('main/edit_profile.html', title=_('Edit Profile'),
                           form=form)


@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])


@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('main/user_popup.html', user=user)


@bp.route('/delete_post/<post_id>', methods=['GET', 'POST'])
@login_required
def delete_post(post_id):
    if current_user.is_admin():
        post = Post.query.get(post_id)
        name = post.author.username

        for reply in post.get_replies():
            db.session.delete(reply)
        db.session.flush()

        db.session.delete(post)
        db.session.commit()
        ca.logger.info('>{}< deleted post >{}< by >{}<'.format(
            current_user.username, post_id, name
        ))
        flash(_('Post has been deleted.'))
        return redirect(url_for('main.index'))
    else:
        ca.logger.warn('Blocked post deletion for >{}<'
                       .format(current_user.username))
        abort(403)
