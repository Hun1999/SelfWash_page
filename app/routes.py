from flask import render_template, url_for, flash, redirect, request, abort, jsonify
from app import app, db, bcrypt
from app.forms import RegistrationForm, LoginForm, ReviewForm, CommentForm
from app.models import User, Review, Like, Comment, Ad, Maintenance
from flask_login import login_user, current_user, logout_user, login_required
from flask_paginate import Pagination, get_page_args
import os
import secrets
from PIL import Image
import requests
import random
from datetime import datetime, timedelta
from app.utils import get_kst_now

YOUTUBE_API_KEY = 'AIzaSyCDkt43FwusOEhrzhk7IQnqoUAi2K7aJfE'

@app.route("/")
@app.route("/main")
def main():
    return render_template('main.html')


@app.route("/review/<int:review_id>", methods=['GET', 'POST'])
def review(review_id):
    review = Review.query.get_or_404(review_id)
    review.view_count += 1
    db.session.commit()
    review.likes_count = Like.query.filter_by(review_id=review.id).count()
    ad = Ad.query.order_by(db.func.random()).first()  # 임의의 광고를 선택하여 전달

    form = CommentForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            comment = Comment(content=form.content.data, user_id=current_user.id, review_id=review.id)
            db.session.add(comment)
            db.session.commit()
            flash('Your comment has been posted.', 'success')
            return redirect(url_for('review', review_id=review.id))
        else:
            flash('You need to be logged in to comment.', 'danger')

    comments = Comment.query.filter_by(review_id=review.id).all()
    return render_template('review.html', title=review.title, review=review, ad=ad, form=form, comments=comments)


@app.route("/reviews")
def reviews():
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    per_page = 20
    search = request.args.get('search', '')

    if search:
        reviews_query = Review.query.filter(Review.title.contains(search)).order_by(Review.date_posted.desc())
    else:
        reviews_query = Review.query.order_by(Review.date_posted.desc())

    total = reviews_query.count()
    reviews = reviews_query.offset(offset).limit(per_page).all()
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')
    total_pages = (total + per_page - 1) // per_page  # 총 페이지 수 계산

    for review in reviews:
        review.likes_count = Like.query.filter_by(review_id=review.id).count()

    ad = Ad.query.order_by(db.func.random()).first()  # 랜덤 광고 선택

    return render_template('view_reviews.html', reviews=reviews, pagination=pagination, ad=ad, total_pages=total_pages)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main'))


@app.route("/review/new", methods=['GET', 'POST'])
@login_required
def new_review():
    form = ReviewForm()
    if form.validate_on_submit():
        if form.image_file.data:
            picture_file = save_picture(form.image_file.data)
        else:
            picture_file = None
        review = Review(title=form.title.data, content=form.content.data, author=current_user, date_posted=get_kst_now(), image_file=picture_file)
        db.session.add(review)
        db.session.commit()
        flash('Your review has been created!', 'success')
        return redirect(url_for('reviews'))
    ad = Ad.query.order_by(db.func.random()).first()
    return render_template('new_review.html', title='New Review', form=form, legend='New Review', ad=ad)


@app.route("/mypage")
@login_required
def mypage():
    user_reviews = Review.query.filter_by(user_id=current_user.id).all()
    liked_reviews = Review.query.join(Like, Like.review_id == Review.id).filter(Like.user_id == current_user.id).all()
    maintenances = Maintenance.query.filter_by(user_id=current_user.id).all()

    # 권장 사용 날짜 계산
    for maintenance in maintenances:
        last_date = maintenance.date
        frequency = int(maintenance.frequency)  # 주기를 정수형으로 변환
        next_date = last_date + timedelta(days=frequency)
        maintenance.next_date = next_date

    kst_now = get_kst_now().date()

    ad = Ad.query.order_by(db.func.random()).first()
    return render_template('mypage.html', user_reviews=user_reviews, liked_reviews=liked_reviews,
                           maintenances=maintenances, ad=ad, kst_now=kst_now)


@app.route("/delete_account", methods=['POST'])
@login_required
def delete_account():
    user = User.query.get(current_user.id)
    db.session.delete(user)
    db.session.commit()
    flash('Your account has been deleted.', 'success')
    return redirect(url_for('main'))


def get_random_youtube_video(query):
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&q={query}&key={YOUTUBE_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        items = data.get('items', [])
        if items:
            selected_video = random.choice(items)
            video_id = selected_video['id']['videoId']
            return f"https://www.youtube.com/embed/{video_id}"
    return None


@app.route('/car_wash_process')
def car_wash_process():
    beginner_video = get_random_youtube_video('초보 세차 가이드')
    detailer_video = get_random_youtube_video('디테일링 가이드')
    ad = Ad.query.order_by(db.func.random()).first()  # 랜덤 광고 선택
    return render_template('car_wash_process.html', beginner_video=beginner_video, detailer_video=detailer_video, ad=ad)


@app.route("/dilution_ratio_calculator")
def dilution_ratio_calculator():
    ad = Ad.query.order_by(db.func.random()).first()
    return render_template('dilution_ratio_calculator.html', ad=ad)


@app.route("/like/<int:review_id>", methods=['POST'])
@login_required
def like_review(review_id):
    review = Review.query.get_or_404(review_id)
    like = Like.query.filter_by(user_id=current_user.id, review_id=review_id).first()
    if like:
        db.session.delete(like)
        review.likes_count -= 1
    else:
        new_like = Like(user_id=current_user.id, review_id=review_id)
        db.session.add(new_like)
        review.likes_count += 1
    db.session.commit()
    return redirect(url_for('review', review_id=review_id))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/review_pics', picture_fn)

    i = Image.open(form_picture)
    i.save(picture_path)

    return picture_fn


@app.route("/review/<int:review_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    review = Review.query.get_or_404(review_id)
    ad = Ad.query.order_by(db.func.random()).first()
    if review.author != current_user:
        flash('자신이 작성한 글만 수정/삭제 할 수 있습니다', 'danger')
        return redirect(url_for('review', review_id=review_id))
    form = ReviewForm()
    if form.validate_on_submit():
        review.title = form.title.data
        review.content = form.content.data
        if form.image_file.data:
            review.image_file = save_picture(form.image_file.data)
        review.date_posted = get_kst_now()
        db.session.commit()
        flash('Your review has been updated!', 'success')
        return redirect(url_for('review', review_id=review.id))
    elif request.method == 'GET':
        form.title.data = review.title
        form.content.data = review.content
    return render_template('new_review.html', title='Update Review', form=form, legend='Update Review', ad=ad)


import os


@app.route("/review/<int:review_id>/delete", methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.author != current_user:
        flash('You can only delete your own reviews.', 'danger')
        return redirect(url_for('review', review_id=review.id))

    # 관련된 댓글 삭제
    comments = Comment.query.filter_by(review_id=review.id).all()
    for comment in comments:
        db.session.delete(comment)

    # 리뷰에 첨부된 사진 삭제
    if review.image_file:
        picture_path = os.path.join(app.root_path, 'static/review_pics', review.image_file)
        if os.path.exists(picture_path):
            os.remove(picture_path)

    db.session.delete(review)
    db.session.commit()
    flash('Your review has been deleted!', 'success')
    return redirect(url_for('reviews'))


@app.route("/comment/<int:comment_id>/edit", methods=['POST'])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.author != current_user:
        flash('You can only edit your own comments.', 'danger')
        return redirect(url_for('review', review_id=comment.review_id))
    comment.content = request.form['content']
    db.session.commit()
    flash('Your comment has been updated!', 'success')
    return redirect(url_for('review', review_id=comment.review_id))

@app.route("/comment/<int:comment_id>/delete", methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.author != current_user:
        flash('You can only delete your own comments.', 'danger')
        return redirect(url_for('review', review_id=comment.review_id))
    db.session.delete(comment)
    db.session.commit()
    flash('Your comment has been deleted.', 'success')
    return redirect(url_for('review', review_id=comment.review_id))


@app.route("/maintenance/<int:id>", methods=['GET'])
@login_required
def get_maintenance(id):
    maintenance = Maintenance.query.get_or_404(id)
    if maintenance.user_id != current_user.id:
        return jsonify({"message": "Unauthorized"}), 403
    return jsonify({
        "item": maintenance.item,
        "date": maintenance.date.strftime('%Y-%m-%d'),
        "frequency": maintenance.frequency,
        "note": maintenance.note
    }), 200

@app.route("/maintenance", methods=['POST'])
@login_required
def add_maintenance():
    data = request.get_json()
    maintenance = Maintenance(
        item=data['item'],
        date=datetime.strptime(data['date'], '%Y-%m-%d'),
        frequency=int(data['frequency']),  # 주기를 정수형으로 변환
        note=data['note'],
        user_id=current_user.id
    )
    db.session.add(maintenance)
    db.session.commit()
    return jsonify({"message": "Maintenance item added successfully"}), 201

@app.route("/maintenance/<int:id>", methods=['PUT'])
@login_required
def edit_maintenance(id):
    data = request.get_json()
    maintenance = Maintenance.query.get_or_404(id)
    if maintenance.user_id != current_user.id:
        return jsonify({"message": "Unauthorized"}), 403
    maintenance.item = data['item']
    maintenance.date = datetime.strptime(data['date'], '%Y-%m-%d')
    maintenance.frequency = int(data['frequency'])  # 주기를 정수형으로 변환
    maintenance.note = data['note']
    db.session.commit()
    return jsonify({"message": "Maintenance item updated successfully"}), 200

@app.route("/maintenance/<int:id>", methods=['DELETE'])
@login_required
def delete_maintenance(id):
    maintenance = Maintenance.query.get_or_404(id)
    if maintenance.user_id != current_user.id:
        return jsonify({"message": "Unauthorized"}), 403
    db.session.delete(maintenance)
    db.session.commit()
    return jsonify({"message": "Maintenance item deleted successfully"}), 200
