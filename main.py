from flask import Flask, render_template, redirect, request, abort, url_for, flash
from data import db_session
from data.categories import Category
from data.users import User
from data.businesses import Business
from data.threadmodel import ThreadModel
from forms.addcategoryform import AddCategoryForm
from forms.loginform import LoginForm
from forms.settingsform import SettingsForm
from forms.registrationform import RegisterForm
from forms.addbusinessform import AddBusinessForm
from forms.resetpasswordform import ResetPasswordForm
from forms.setnewpasswordform import SetNewPasswordForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from dotenv import dotenv_values
from forms.redactbusinessform import RedactBusinessForm
import datetime
from threading import Thread
import time


app = Flask(__name__)
app.config['SECRET_KEY'] = dotenv_values('.env')['SECRET_KEY']
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'todolistbyandmoch@gmail.com'
app.config['MAIL_DEFAULT_SENDER'] = 'todolistbyandmoch@gmail.com'
app.config['MAIL_PASSWORD'] = dotenv_values('.env')['MAIL_PASSWORD']
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)


SPEC_SYMS = r"[ !#$%&'()*+,-./[\\\]^_`{|}~" + r'"]'


def main():
    db_session.global_init("db/todo_list.db")
    app.run(port=8080, debug=True)


def send_reset_email(recipient, token, user):
    msg = Message(subject='Сброс пароля в Todo List', recipients=recipient,
                  html=render_template('reset_password_email.html', token=token, user=user))
    mail.send(msg)


def send_notification_email(subject, recipient, user, business):
    delta = business.end_date - datetime.datetime.now()
    time.sleep(delta.total_seconds())
    with app.app_context():
        db_sess = db_session.create_session()
        thread = db_sess.query(ThreadModel).filter(ThreadModel.title == f"Thread-{business.id}").first()
        if thread:
            msg = Message(subject=subject, recipients=recipient,
                          html=render_template('notification_email.html', user=user, business=business))
            mail.send(msg)
            db_sess.delete(thread)
            db_sess.commit()


def password_check(password):
    if not any(char.isdigit() for char in password):
        return True, 'В пароле должна быть хотя бы одна цифра'
    if not any(char.isupper() for char in password):
        return True, 'В пароле должна быть хотя бы одна буква верхнего регистра'
    if not any(char.islower() for char in password):
        return True, 'В пароле должна быть хотя бы одна буква нижнего регистра'
    if any(char in SPEC_SYMS for char in password):
        return True, f'В пароле не должны присутствовать символы из списка: {SPEC_SYMS}'
    return False, "ОК"


def order_clause(order, param):
    clause = None
    if param == "id":
        clause = Business.id
    elif param == "title":
        clause = Business.title
    elif param == "start_date":
        clause = Business.start_date
    elif param == "end_date":
        clause = Business.end_date
    elif param == "priority":
        clause = Business.priority
    if order == "asc":
        return clause
    else:
        return clause.desc()


def status_update(end_date: datetime.datetime):
    cur_time = datetime.datetime.now()
    if cur_time >= end_date:
        return "Срок выполнения истёк"
    else:
        return "В процессе выполнения"


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/")
def index():
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        businesses = []
        param = request.args.get("param", default="id")
        order = request.args.get("order", default="asc")
        for business in db_sess.query(Business).order_by(order_clause(order, param))\
                .filter(Business.user_id == current_user.id):
            business.status = status_update(business.end_date)
            db_sess.commit()
            businesses.append(business)
            already_running = db_sess.query(ThreadModel).filter(ThreadModel.title == f"Thread-{business.id}").first()
            if business.end_date > datetime.datetime.now() and not already_running\
                    and current_user.notifications_enabled:
                thread = ThreadModel(title=f"Thread-{business.id}")
                db_sess.add(thread)
                thr = Thread(name=f"Thread-{business.id}", target=send_notification_email,
                             args=[f"У задачи \"{business.title}\" истёк срок выполнения",
                                   [current_user.email], current_user.login, business])
                thr.start()
                db_sess.commit()
            elif business.status == "Срок выполнения истёк" and already_running:
                db_sess.delete(already_running)
                db_sess.commit()
        categories = [category for category in db_sess.query(Category).filter(Category.user_id == current_user.id)]
        return render_template('main.html', title='Главная страница', businesses=businesses, categories=categories,
                               param=param, order=order)
    else:
        return redirect('/registration')


@app.route("/index/<string:category_title>", methods=['GET', 'POST'])
def index_category(category_title):
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        businesses = []
        param = request.args.get("param", default="id")
        order = request.args.get("order", default="asc")
        category = db_sess.query(Category).filter(Category.title == category_title,
                                                  Category.user_id == current_user.id).first()
        for business in db_sess.query(Business).order_by(order_clause(order, param))\
                .filter(Business.category_id == category.id, Business.user_id == current_user.id):
            business.status = status_update(business.end_date)
            db_sess.commit()
            businesses.append(business)
            already_running = db_sess.query(ThreadModel).filter(ThreadModel.title == f"Thread-{business.id}").first()
            if business.end_date > datetime.datetime.now() and not already_running\
                    and current_user.notifications_enabled:
                thread = ThreadModel(title=f"Thread-{business.id}")
                db_sess.add(thread)
                thr = Thread(name=f"Thread-{business.id}", target=send_notification_email,
                             args=[f"У задачи \"{business.title}\" истёк срок выполнения",
                                   [current_user.email], current_user.login, business])
                thr.start()
                db_sess.commit()
            elif business.status == "Срок выполнения истёк" and already_running:
                db_sess.delete(already_running)
                db_sess.commit()
        categories = [category for category in db_sess.query(Category).filter(Category.user_id == current_user.id)]
        return render_template('index_categories.html', title=f'Задачи категории {category_title}',
                               businesses=businesses, categories=categories, category=category,
                               param=param, order=order)
    else:
        return redirect('/registration')


@app.route("/ended_businesses", methods=['GET', 'POST'])
def ended_businesses():
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        businesses = []
        param = request.args.get("param", default="id")
        order = request.args.get("order", default="asc")
        for business in db_sess.query(Business).filter(Business.status != 'Срок выполнения истёк',
                                                       Business.user_id == current_user.id):
            business.status = status_update(business.end_date)
            db_sess.commit()
        for business in db_sess.query(Business).order_by(order_clause(order, param))\
                .filter((Business.status == 'Срок выполнения истёк') | Business.ended_by_user,
                        Business.user_id == current_user.id):
            business.status = status_update(business.end_date)
            db_sess.commit()
            businesses.append(business)
            already_running = db_sess.query(ThreadModel).filter(ThreadModel.title == f"Thread-{business.id}").first()
            if business.end_date > datetime.datetime.now() and not already_running\
                    and current_user.notifications_enabled:
                thread = ThreadModel(title=f"Thread-{business.id}")
                db_sess.add(thread)
                thr = Thread(name=f"Thread-{business.id}", target=send_notification_email,
                             args=[f"У задачи \"{business.title}\" истёк срок выполнения",
                                   [current_user.email], current_user.login, business])
                thr.start()
                db_sess.commit()
            elif business.status == "Срок выполнения истёк" and already_running:
                db_sess.delete(already_running)
                db_sess.commit()
        categories = [category for category in db_sess.query(Category).filter(Category.user_id == current_user.id)]
        return render_template('ended_businesses.html', title='Оконченные задачи', businesses=businesses,
                               categories=categories, param=param, order=order)
    else:
        return redirect('/registration')


@app.route("/current_businesses", methods=['GET', 'POST'])
def current_businesses():
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        businesses = []
        param = request.args.get("param", default="id")
        order = request.args.get("order", default="asc")
        for business in db_sess.query(Business).order_by(order_clause(order, param))\
                .filter(Business.status != 'Срок выполнения истёк', Business.ended_by_user != True,
                        Business.user_id == current_user.id):
            business.status = status_update(business.end_date)
            db_sess.commit()
            if business.status != "Срок выполнения истёк":
                businesses.append(business)
            already_running = db_sess.query(ThreadModel).filter(ThreadModel.title == f"Thread-{business.id}").first()
            if business.end_date > datetime.datetime.now() and not already_running\
                    and current_user.notifications_enabled:
                thread = ThreadModel(title=f"Thread-{business.id}")
                db_sess.add(thread)
                thr = Thread(name=f"Thread-{business.id}", target=send_notification_email,
                             args=[f"У задачи \"{business.title}\" истёк срок выполнения",
                                   [current_user.email], current_user.login, business])
                thr.start()
                db_sess.commit()
            elif business.status == "Срок выполнения истёк" and already_running:
                db_sess.delete(already_running)
                db_sess.commit()
        categories = [category for category in db_sess.query(Category).filter(Category.user_id == current_user.id)]
        return render_template('current_businesses.html', title='Текущие задачи', businesses=businesses,
                               categories=categories, param=param, order=order)
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
        pass_tup = password_check(form.password.data)
        if pass_tup[0]:
            return render_template('registration.html', title='Регистрация',
                                   form=form,
                                   message=pass_tup[-1])
        if form.password.data != form.password_again.data:
            return render_template('registration.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.login == form.login.data).first():
            return render_template('registration.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('registration.html', title='Регистрация',
                                   form=form,
                                   message="Почта уже занята")
        user = User(
            login=form.login.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('registration.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter((User.login == form.login.data) | (User.email == form.login.data)).first()
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


@app.route('/request_for_password_reset', methods=['GET', 'POST'])
def request_for_password_reset():
    if current_user.is_authenticated:
        return redirect('/')
    form = ResetPasswordForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user:
            token = user.get_reset_password_token()
            send_reset_email([user.email], token, user)
        else:
            return render_template('reset_password.html',
                                   title='Сброс пароля', form=form, message='Пользователя с такой почтой не существует')
        flash('На вашу почту отправлено письмо с ссылкой для сброса пароля')
        return redirect('/login')
    return render_template('reset_password.html',
                           title='Сброс пароля', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect('/')
    user_id = User.verify_reset_password_token(token)
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    if not user:
        return redirect('/')
    form = SetNewPasswordForm()
    if form.validate_on_submit():
        pass_tup = password_check(form.password.data)
        if pass_tup[0]:
            return render_template('set_new_password.html', title='Смена пароля',
                                   form=form,
                                   message=pass_tup[-1])
        user.set_password(form.password.data)
        db_sess.commit()
        return redirect('/login')
    return render_template('set_new_password.html', title='Смена пароля', form=form)


@app.route('/user_settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    form = SettingsForm()
    form.usage_variants.choices = [(3, "Контекстное меню и кнопки"), (2, "Контекстное меню"), (1, "Кнопки")]
    if request.method == "GET":
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        form.email_checkbox.data = user.notifications_enabled
        if user.buttons_enabled and user.context_menu_enabled:
            form.usage_variants.process_data(3)
        elif not user.buttons_enabled and user.context_menu_enabled:
            form.usage_variants.process_data(2)
        elif user.buttons_enabled and not user.context_menu_enabled:
            form.usage_variants.process_data(1)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        user.notifications_enabled = form.email_checkbox.data
        if form.usage_variants.data == 3:
            user.buttons_enabled = True
            user.context_menu_enabled = True
        elif form.usage_variants.data == 2:
            user.context_menu_enabled = True
            user.buttons_enabled = False
        elif form.usage_variants.data == 1:
            user.context_menu_enabled = False
            user.buttons_enabled = True
        db_sess.commit()
        return redirect('/')
    return render_template('user_settings.html', title='Настройки', form=form)


@app.route('/add_business', methods=['GET', 'POST'])
@login_required
def add_business():
    form = AddBusinessForm()
    db_sess = db_session.create_session()
    cur_time = datetime.datetime.strftime(datetime.datetime.now(), format('%Y-%m-%dT%H:%M'))
    categories = [(None, "Без категории")]
    categories.extend([(category.id, category.title)
                       for category in db_sess.query(Category).filter(Category.user_id == current_user.id)])
    form.category.choices = categories
    cat_id = request.args.get("cat_id")
    if request.method == "GET":
        if cat_id:
            form.category.data = cat_id
    if form.validate_on_submit():
        if not form.end_date.data or not form.start_date.data:
            return render_template('add_business.html', title='Добавление задачи',
                                   form=form,
                                   message="Не указана продолжительность задачи",
                                   cur_time=cur_time)
        db_sess = db_session.create_session()
        if db_sess.query(Business).filter(Business.title == form.title.data,
                                          Business.user_id == current_user.id).first():
            return render_template('add_business.html', title='Добавление задачи',
                                   form=form,
                                   message="Такая задача уже есть",
                                   cur_time=cur_time)
        start_time = form.start_date.data
        end_time = form.end_date.data
        if start_time >= end_time:
            return render_template('add_business.html', title='Добавление задачи',
                                   form=form,
                                   message="Время начала позже или равно времени окончания задачи",
                                   cur_time=cur_time)
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
        sender = request.args.get("sender")
        if sender is None:
            return redirect('/')
        elif "index" in sender:
            ind_cat = sender.split('_')
            return redirect('/index/' + ind_cat[1])
        else:
            return redirect('/' + sender)
    return render_template('add_business.html', title='Добавление задачи', form=form, cur_time=cur_time)


@app.route('/redact_business/<int:id>', methods=['GET', 'POST'])
@login_required
def redact_business(id):
    form = RedactBusinessForm()
    db_sess = db_session.create_session()
    categories = [(None, "Без категории")]
    categories.extend([(category.id, category.title)
                       for category in db_sess.query(Category).filter(Category.user_id == current_user.id)])
    form.category.choices = categories
    cat_id = request.args.get("cat_id")
    if request.method == "GET":
        db_sess = db_session.create_session()
        business = db_sess.query(Business).filter(Business.id == id).first()
        if business:
            form.title.data = business.title
            form.priority.data = business.priority
            form.end_date.data = business.end_date
            form.category.data = str(business.category_id)
            if cat_id:
                form.category.data = cat_id
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
                                       message="Такая задача уже есть",
                                       categories=categories, id=id)
            if business.start_date >= form.end_date.data:
                return render_template('redact_business.html', title='Добавление задачи',
                                       form=form,
                                       message="Время начала позже или равно времени окончания задачи",
                                       categories=categories, id=id)
            business.title = form.title.data
            business.priority = form.priority.data
            business.end_date = form.end_date.data
            business.status = status_update(form.end_date.data)
            business.category_id = form.category.data
            db_sess.commit()
            sender = request.args.get("sender")
            if sender is None:
                return redirect('/')
            elif "index" in sender:
                ind_cat = sender.split('_')
                return redirect('/index/' + ind_cat[1])
            else:
                return redirect('/' + sender)
        else:
            abort(404)
    return render_template('redact_business.html', title='Редактирование работы', form=form,
                           categories=categories, id=id)


@app.route('/disable_business/<int:id>', methods=['GET', 'POST'])
@login_required
def disable_business(id):
    db_sess = db_session.create_session()
    business = db_sess.query(Business).filter(Business.id == id,
                                              Business.user_id == current_user.id
                                              ).first()
    sender = request.args.get("sender")
    if business:
        business.ended_by_user = True
        db_sess.commit()
    else:
        abort(404)
    if sender is None:
        return redirect('/')
    elif "index" in sender:
        ind_cat = sender.split('_')
        return redirect('/index/' + ind_cat[1])
    else:
        return redirect('/' + sender)


@app.route('/enable_business/<int:id>', methods=['GET', 'POST'])
@login_required
def enable_business(id):
    db_sess = db_session.create_session()
    business = db_sess.query(Business).filter(Business.id == id,
                                              Business.user_id == current_user.id
                                              ).first()
    sender = request.args.get("sender")
    if business:
        business.ended_by_user = False
        db_sess.commit()
    else:
        abort(404)
    if sender is None:
        return redirect('/')
    elif "index" in sender:
        ind_cat = sender.split('_')
        return redirect('/index/' + ind_cat[1])
    else:
        return redirect('/' + sender)


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
    sender = request.args.get("sender")
    if sender is None:
        return redirect('/')
    elif "index" in sender:
        ind_cat = sender.split('_')
        return redirect('/index/' + ind_cat[1])
    else:
        return redirect('/' + sender)


@app.route('/add_category', methods=['GET', 'POST'])
def add_category():
    form = AddCategoryForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(Category).filter(Category.title == form.title.data,
                                          Category.user_id == current_user.id).first():
            return render_template('add_category.html', title='Добавление задачи',
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


@app.route('/add_category_while_business_adding', methods=['GET', 'POST'])
def add_category_while_business_adding():
    form = AddCategoryForm()
    sender = request.args.get('sender').split('-')
    sender = '/'.join(sender)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(Category).filter(Category.title == form.title.data,
                                          Category.user_id == current_user.id).first():
            return render_template('add_category.html', title='Добавление задачи',
                                   form=form,
                                   message="Категория с таким именем уже есть")
        category = Category(
            title=form.title.data,
            user_id=current_user.id
        )
        db_sess.add(category)
        db_sess.commit()
        sender = request.args.get('sender').split('-')
        if "redact_business" in sender:
            return redirect(f'/{sender[0]}/{sender[1]}?cat_id={category.id}')
        else:
            return redirect(f'/{sender[0]}?cat_id={category.id}')
    return render_template('cat_while_adding.html', title='Добавление категории', form=form, sender=sender)


@app.route('/redact_category/<int:id>', methods=['GET', 'POST'])
@login_required
def redact_category(id):
    form = AddCategoryForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        category = db_sess.query(Category).filter(Category.id == id, Category.user_id == current_user.id).first()
        if category:
            form.title.data = category.title
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        category = db_sess.query(Category).filter(Category.id == id, Category.user_id == current_user.id).first()
        if category:
            if db_sess.query(Category).filter(Category.title == form.title.data,
                                              Category.title != category.title,
                                              Category.user_id == current_user.id).first():
                return render_template('add_category.html', title='Изменение категории',
                                       form=form,
                                       message="Такая категория уже есть")
            category.title = form.title.data
            db_sess.commit()
            return redirect('/categories')
        else:
            abort(404)
    return render_template('add_category.html', title='Изменение категории', form=form)


@app.route('/delete_category/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_category(id):
    db_sess = db_session.create_session()
    category = db_sess.query(Category).filter(Category.id == id,
                                              Category.user_id == current_user.id).first()
    if category:
        db_sess.delete(category)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/categories')


if __name__ == '__main__':
    main()
