from flask import Flask, render_template, redirect, request, abort, url_for
from data import db_session
from data.categories import Category
from data.users import User
from data.businesses import Business
from forms.addcategoryform import AddCategoryForm
from forms.loginform import LoginForm
from forms.registrationform import RegisterForm
from forms.addbusinessform import AddBusinessForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from dotenv import dotenv_values
from flask_restful import Api
from forms.redactbusinessform import RedactBusinessForm
import datetime

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = dotenv_values('.env')['SECRET_KEY']
login_manager = LoginManager()
login_manager.init_app(app)


def main():
    db_session.global_init("db/todo_list.db")
    app.run(port=8080, debug=True)


def status_update(end_date: datetime.datetime):
    cur_time = datetime.datetime.now()
    if cur_time >= end_date:
        return "Срок выполнения истёк"
    delta = end_date - cur_time
    if delta >= datetime.timedelta(days=365):
        return "Больше года на выполнение"
    elif datetime.timedelta(days=62) < delta < datetime.timedelta(days=365):
        return f"Около {delta.days // 30} месяцев на выполнение"
    elif datetime.timedelta(days=28) < delta <= datetime.timedelta(days=62):
        return "Около месяца на выполнение"
    elif delta <= datetime.timedelta(days=28):
        return "Меньше месяца на выполнение"
    elif datetime.timedelta(days=2) < delta <= datetime.timedelta(days=7):
        return f"{delta.days} дней на выполнение"
    elif datetime.timedelta(hours=1) < delta <= datetime.timedelta(days=1):
        return "День на выполнение"
    elif delta < datetime.timedelta(hours=1):
        return "Меньше часа на выполнение"


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
            business.status = status_update(business.end_date)
            db_sess.commit()
            businesses.append(business)
        categories = [category for category in db_sess.query(Category).filter(Category.user_id == current_user.id)]
        return render_template('main.html', title='Главная страница', businesses=businesses, categories=categories)
    else:
        return redirect('/registration')


@app.route("/index/<string:category_title>", methods=['GET', 'POST'])
def index_category(category_title):
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        businesses = []
        category = db_sess.query(Category).filter(Category.title == category_title).first()
        for business in db_sess.query(Business).filter(Business.category_id == category.id):
            business.status = status_update(business.end_date)
            db_sess.commit()
            businesses.append(business)
        return render_template('index_categories.html', title='Главная страница', businesses=businesses)
    else:
        return redirect('/registration')


@app.route("/categories")
def index_categories():
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        categories = []
        for category in db_sess.query(Category).filter(Category.user_id == current_user.id):
            categories.append(category)
        return render_template('categories.html', title='Главная страница', categories=categories)
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
        if db_sess.query(Business).filter(Business.title == form.title.data,
                                          Business.user_id == current_user.id).first():
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
            category_id=form.category.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            user_id=current_user.id,
            status=status_update(form.end_date.data)
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
            form.priority.data = business.priority
            form.end_date.data = business.end_date
            form.category.data = business.category_id
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        business = db_sess.query(Business).filter(Business.id == id).first()
        if business:
            if db_sess.query(Business).filter(Business.title == form.title.data,
                                              Business.title != business.title,
                                              Business.user_id == current_user.id).first():
                return render_template('redact_business.html', title='Добавление задачи',
                                       form=form,
                                       message="Такая задача уже есть")
            if business.start_date >= form.end_date.data:
                return render_template('redact_business.html', title='Добавление задачи',
                                       form=form,
                                       message="Время начала позже или равно времени окончания задачи")
            business.title = form.title.data
            business.priority = form.priority.data
            business.end_date = form.end_date.data
            business.status = status_update(form.end_date.data)
            business.category_id = form.category.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('redact_business.html', title='Редактирование работы', form=form)


@app.route('/delete_business/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_business(id):
    db_sess = db_session.create_session()
    business = db_sess.query(Business).filter(Business.id == id,
                                              Business.user_id == current_user.id
                                              ).first()
    if business:
        db_sess.delete(business)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/add_category', methods=['GET', 'POST'])
def add_category():
    form = AddCategoryForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(Category).filter(Category.title == form.title.data,
                                          Category.user_id == current_user.id).first():
            return render_template('add_business.html', title='Добавление задачи',
                                   form=form,
                                   message="Категория с таким именем уже есть")
        category = Category(
            title=form.title.data,
            user_id=current_user.id
        )
        db_sess.add(category)
        db_sess.commit()
        return redirect('/categories')
    return render_template('add_category.html', title='Добавление категории', form=form)


@app.route('/redact_category/<int:id>', methods=['GET', 'POST'])
@login_required
def redact_category(id):
    form = AddCategoryForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        category = db_sess.query(Category).filter(Category.id == id).first()
        if category:
            form.title.data = category.title
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        category = db_sess.query(Category).filter(Category.id == id).first()
        if category:
            if db_sess.query(Category).filter(Category.title == form.title.data,
                                              Category.title != category.title,
                                              Category.user_id == current_user.id).first():
                return render_template('add_category.html', title='Изменение категории',
                                       form=form,
                                       message="Такая категория уже есть")
            category.title = form.title.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('add_category.html', title='Изменение категории', form=form)


@app.route('/delete_category/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_category(id):
    db_sess = db_session.create_session()
    category = db_sess.query(Category).filter(Category.id == id,
                                              Category.user_id == current_user.id
                                              ).first()
    if category:
        db_sess.delete(category)
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
