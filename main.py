from flask import Flask, render_template, redirect, request, abort, jsonify
from data import db_session
from data.users import User
from data.businesses import Business
from forms.loginform import LoginForm
from forms.registrationform import RegisterForm
from forms.addbusinessform import AddBusinessForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from dotenv import dotenv_values
from forms.redactbusinessform import RedactBusinessForm
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = dotenv_values('.env')['SECRET_KEY']
login_manager = LoginManager()
login_manager.init_app(app)


def main():
    db_session.global_init("db/todo_list.db")
    app.run(debug=True)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/")
def index():
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        businesses = []
        for business in db_sess.query(Business).filter(Business.user_id == current_user.id):
            businesses.append(business)
        cur_time = datetime.datetime.now()
        return render_template('main.html', title='Главная страница', businesses=businesses, cur_time=cur_time)
    else:
        return redirect('/registration')


@app.route('/registration', methods=['GET', 'POST'])
def reqistration():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('registration.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.login == form.login.data).first():
            return render_template('registration.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            login=form.login.data,
            surname=form.surname.data,
            name=form.name.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('registration.html', title='Регистрация', form=form)


@app.route('/add_business', methods=['GET', 'POST'])
@login_required
def add_job():
    form = AddBusinessForm()
    if form.validate_on_submit():
        if not form.end_date.data or not form.start_date.data:
            return render_template('add_business.html', title='Добавление задачи',
                                   form=form,
                                   message="Не указана продолжительность задачи")
        db_sess = db_session.create_session()
        if db_sess.query(Business).filter(Business.title == form.title.data).first():
            return render_template('add_business.html', title='Добавление задачи',
                                   form=form,
                                   message="Такая задача уже есть")
        start_time = form.start_date.data
        end_time = form.end_date.data
        if start_time >= end_time:
            return render_template('add_business.html', title='Добавление задачи',
                                   form=form,
                                   message="Время начала позже или равно времени окончания задачи")
        business = Business(
            title=form.title.data,
            priority=form.priority.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            user_id=current_user.id
        )
        db_sess.add(business)
        db_sess.commit()
        return redirect('/')
    return render_template('add_business.html', title='Добавление работы', form=form)


@app.route('/redact_business/<int:id>', methods=['GET', 'POST'])
@login_required
def redact_business(id):
    form = RedactBusinessForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        business = db_sess.query(Business).filter(Business.id == id).first()
        if business:
            form.title.data = business.title
            form.priority.data = business.work_size
            form.end_date.data = business.end_date
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        business = db_sess.query(Business).filter(Business.id == id).first()
        if business:
            if db_sess.query(Business).filter(Business.title == form.title.data,
                                              Business.title != business.title).first():
                return render_template('add_business.html', title='Добавление задачи',
                                       form=form,
                                       message="Такая задача уже есть")
            if business.start_time >= form.end_date.data:
                return render_template('add_business.html', title='Добавление задачи',
                                       form=form,
                                       message="Время начала позже или равно времени окончания задачи")
            business.title = form.title.data
            business.priority = form.priority.data
            business.end_date = form.end_date.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('add_business.html', title='Редактирование работы', form=form)


@app.route('/delete_business/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_business(id):
    db_sess = db_session.create_session()
    job = db_sess.query(Business).filter(Business.id == id,
                                         Business.user_id == current_user.id
                                         ).first()
    if job:
        db_sess.delete(job)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.login == form.login.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")



if __name__ == '__main__':
    main()