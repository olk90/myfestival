import os
import shutil

from flask import abort
from flask import current_app as ca
from flask import flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import login_required, current_user as cu
from werkzeug.utils import secure_filename

from app import session
from app.chronicle import bp
from app.chronicle.forms import ChronicleEntryForm
from app.chronicle.logic import get_festival_selection, get_images
from app.models import ChronicleEntry, Festival


@bp.route("/chronicle_overview")
@login_required
def chronicle_overview():
    page = request.args.get("page", 1, type=int)
    entries = session.query(ChronicleEntry).order_by(ChronicleEntry.timestamp.desc()) \
        .paginate(page, ca.config["POSTS_PER_PAGE"], False)
    ca.logger.info(">{}< has loaded chronicle overview"
                   .format(cu.username))
    next_url = \
        url_for("chronicle.chronicle_overview", page=entries.next_num) if entries.has_next else None
    prev_url = \
        url_for("chronicle.chronicle_overview", page=entries.prev_num) if entries.has_prev else None
    return render_template("chronicle/chronicle_overview.html",
                           entries=entries.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route("/add_entry/<f_id>", methods=["GET", "POST"])
@login_required
def add_entry(f_id):
    form = ChronicleEntryForm(f_id)
    form.festival.choices = get_festival_selection()
    if form.validate_on_submit():
        f_id = form.festival.data
        festival = session.query(Festival).get(f_id)
        y = festival.get_year()
        entry = ChronicleEntry(body=form.body.data,
                               festival_id=f_id,
                               chronicler_id=cu.id,
                               year=y)
        session.add(entry)
        session.commit()
        flash(_("Chronicle entry has been added."))
        ca.logger.info(">{}< has added chronicle entry >{}<"
                       .format(cu.username, entry.id))
        return redirect(url_for("chronicle.chronicle_entry",
                                entry_id=entry.id))
    elif f_id and request.method == "GET":
        ca.logger.info("pre select festival >{}<".format(f_id))
        form.festival.process_data(f_id)
    return render_template("chronicle/setup_entry.html",
                           form=form,
                           images=get_images(f_id),
                           f_id=f_id)


@bp.route("/upload_images/<f_id>", methods=["POST"])
def upload_images(f_id):
    uploaded_file = request.files["file"]
    filename = secure_filename(uploaded_file.filename)
    if filename != "":
        file_ext = os.path.splitext(filename)[1]
        if file_ext.lower() not in ca.config["UPLOAD_EXTENSIONS"]:
            abort(400)

        # make sure the upload target exists
        path = os.path.join(ca.config["UPLOAD_PATH"], "{}/{}".format(f_id, cu.id))
        if not os.path.exists(path):
            os.makedirs(path)

        file_path = os.path.join(ca.config["UPLOAD_PATH"], "{}/{}/{}".format(f_id, cu.id, filename))
        uploaded_file.save(file_path)

    return "", 200


@bp.route("/edit_entry/<entry_id>", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id):
    entry = session.query(ChronicleEntry).get(entry_id)
    if cu == entry.chronicler:
        form = ChronicleEntryForm(entry_id=entry_id, is_edit=True)
        form.festival.choices = get_festival_selection()
        if form.validate_on_submit():
            f_id = form.festival.data
            entry.festival_id = f_id
            entry.body = form.body.data
            festival = session.query(Festival).get(f_id)
            entry.year = festival.get_year()
            session.commit()
            flash(_("Your changes have been saved."))
            ca.logger.info(">{}< has edited chronicle entry >{}<"
                           .format(cu.username, entry.id))
            return redirect(url_for("chronicle.chronicle_entry",
                                    entry_id=entry.id))
        elif request.method == "GET":
            festival_id = entry.festival_id
            if festival_id:
                form.festival.data = festival_id
            form.body.data = entry.body

        festival = session.query(Festival).get(entry.festival_id)
        f_id = festival.id
        return render_template("chronicle/setup_entry.html",
                               f_id=f_id,
                               images=get_images(f_id),
                               form=form,
                               entry_id=entry.id)

    else:
        ca.logger.warn("Blocked editing chronicle entry>{}< for >{}<"
                       .format(entry.id, cu.username))
        abort(403)


@bp.route("/chronicle_entry/<entry_id>")
@login_required
def chronicle_entry(entry_id):
    entry = session.query(ChronicleEntry).filter_by(id=entry_id).first_or_404()
    ca.logger.info(">{}< has entered chronicle page >{}<"
                   .format(cu.username, entry.id))
    return render_template("chronicle/chronicle_entry.html", entry=entry)


@bp.route("/delete_entry/<entry_id>", methods=["GET", "POST"])
@login_required
def delete_entry(entry_id):
    entry = session.query(ChronicleEntry).get(entry_id)
    if cu.is_admin() or cu == entry.chronicler:
        name = entry.chronicler.username

        # remove image directory, if exists
        f_id = entry.festival_id
        u_id = entry.chronicler.id
        path = os.path.join(ca.config["UPLOAD_PATH"], "{}/{}".format(f_id, u_id))
        if os.path.exists(path):
            shutil.rmtree(path)

        session.delete(entry)
        session.commit()
        ca.logger.info(">{}< deleted chronicle entry >{}< by >{}<".format(
            cu.username, entry_id, name))
        flash(_("Chronicle entry has been deleted."))
        return redirect(url_for("chronicle.chronicle_overview"))
    else:
        ca.logger.warn("Blocked chronicle entry deletion for >{}<"
                       .format(cu.username))
        abort(403)


@bp.route("/delete_image", methods=["GET", "POST"])
@login_required
def delete_image():
    # POST request
    data = request.get_json()
    filename = data["fileName"]
    f_id = data["festival"]
    u_id = data["user"]
    path = os.path.join(ca.config["UPLOAD_PATH"], "{}/{}/{}".format(f_id, u_id, filename))
    if os.path.exists(path):
        ca.logger.info("Delete file >{}<".format(path))
        os.remove(path)
    return "", 200
