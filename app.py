import os
import json
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from service import CommanderService, DraftingService, UserService, ScoringService
from pgmodels import User, Roles, UserAdmin, RoleAdmin
from flask_security import Security, SQLAlchemySessionUserDatastore, login_required, utils, \
    current_user, roles_required, roles_accepted
from flask_security.forms import RegisterForm, Required, StringField, PasswordField, LoginForm
from database import db_session, init_db
from flask_mail import Mail, Message
from flask_admin import Admin
import copy


class ExtendedRegisterForm(RegisterForm):
    first_name = StringField('First Name', Required())


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
"""
If DEBUG = True, set Test = True in pgmodel and database
"""
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SECURITY_PASSWORD_SALT'] = b'8\xc3\xe5\xb2\xce=\x0f\xceF\xeat\xaf\xfb|\x8b\x961\xc2$:\x07\t*o\x7f\xdb\xa7\x06\xd2![sr\xc0\xf8{l\rgs\x89"\xd8\xed\x8a\x8dN\xc1\xb2\xb7\xc5\x81\x14k2\xd6a\xf7\xbfv\x13\xb0\x1a\x8c\xbf\xb5\x00\xd7Q\x16\x92\xa9]\x06\xfe\xe4\xfe\xc3\x93\x84\xa7\xc0\xc9Tok2\xf8\xeb\xc6\xeb\xe0o\xca[\xab\x8ckZ\xe0\xd62k\x8b\x0ba\xba\x88\xc9\n\x98U\xcfL9\x87\xc4l\xbb\x8e\x83?\x14\x00\xc22V\xca'
app.config['SECURITY_CONFIRMABLE'] = True
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_TRACKABLE'] = True
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'noreply.fluffybunny@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
app.config['MAIL_DEFAULT_SENDER'] = ('Fluffy Bunny Admins', 'noreply.fluffybunny@gmail.com')
app.config['MAIL_MAX_EMAILS'] = 5
app.config['MAIL_SUPPRESS_SEND'] = False
app.config['MAIL_ASCII_ATTACHMENTS'] = False
app.config['FLASK_ADMIN_SWATCH'] = 'sandstone'
app.config['SECURITY_POST_LOGIN_VIEW'] = '/about'
app.config['SECURITY_POST_LOGOUT_VIEW'] = '/home'
app.config['SECURITY_POST_REGISTER_VIEW'] = '/about'
app.config['SECURITY_RESET_PASSWORD_WITHIN'] = '1 hours'
app.config['SECURITY_CONFIRM_EMAIL_WITHIN'] = '24 hours'
app.config['SECURITY_RECOVERABLE'] = True

user_datastore = SQLAlchemySessionUserDatastore(db_session, User, Roles)
security = Security(app, user_datastore, register_form=ExtendedRegisterForm)
mail = Mail(app)


@app.before_first_request
def before_first_request():
    init_db()
    user_datastore.find_or_create_role(name='admin', description='Administrator')
    user_datastore.find_or_create_role(name='commissioner', description='League Commissioner')
    user_datastore.find_or_create_role(name='player', description='League Participant')
    user_datastore.find_or_create_role(name='scorekeeper', description='Designated Scorekeeper')
    db_session.commit()

    # Testing Users and Roles
    # encrypted_password = utils.hash_password('testingflasksec')
    # if not user_datastore.get_user('michaelyeuh@gmail.com'):
    #     user_datastore.create_user(email='michaelyeuh@gmail.com', password=encrypted_password)
    # if not user_datastore.get_user('natelovin@gmail.com'):
    #     user_datastore.create_user(email='natelovin@gmail.com', password=encrypted_password)
    # if not user_datastore.get_user('scorekeeper@fakemail.com'):
    #     user_datastore.create_user(email='scorekeeper@fakemail.com', password=encrypted_password)
    # if not user_datastore.get_user('user@fbc.org'):
    #     user_datastore.create_user(email='user@fbc.org', password=encrypted_password)
    # db_session.commit()
    #
    # user_datastore.add_role_to_user('michaelyeuh@gmail.com', 'admin')
    # user_datastore.add_role_to_user('natelovin@gmail.com', 'commissioner')
    # user_datastore.add_role_to_user('scorekeeper@fakemail.com', 'scorekeeper')
    # user_datastore.add_role_to_user('user@fbc.org', 'player')
    # db_session.commit()


# Initialize Flask-Admin
admin = Admin(app)

# Add Flask-Admin views for Users and Roles
admin.add_view(UserAdmin(User, db_session))
admin.add_view(RoleAdmin(Roles, db_session))


def calculate_standings():
    standings = {}



@app.route("/")
def index():
    return render_template("home.html")


@app.route("/home")
def home():
    # need to add this unless it will be handled by Vue/React
    return render_template("home.html")


@app.route("/about", methods=["GET"])
@login_required
def about():
    return render_template('about.html')


@app.route("/draft", methods=["GET", "POST"])
@login_required
def draft():
    if request.method == 'POST':
        username = request.form['username']
        user_id = DraftingService().userid(username)
        if not user_id:
            error = 'Username does not exist. Please register or contact admin. '
            return render_template('draft.html', error=error)
        comm_check = DraftingService().usercomm(user_id)
        if comm_check:
            commander = comm_check
        else:
            commander = DraftingService().draft(user_id)

        return render_template('draft.html', commander=commander)

    else:
        return render_template('draft.html')


@app.route("/commanders", methods=["GET"])
@login_required
def commanders():
    return render_template('commanders.html')


@app.route("/commanders/create", methods=["GET","POST"])
@login_required
@roles_accepted('admin', 'commissioner')
def create_commanders():
    if request.method == 'POST':
        comm_str = request.form.get("commlist").strip()
        comm_list = comm_str.split('\n')
        for comm in comm_list:
            comm = comm.strip()
            CommanderService().create(comm)

        return redirect(url_for('commanders'))
    else:
        return render_template('createcomm.html')


@app.route("/users", methods=["GET","POST"])
@login_required
def users():
    """
    This was the janky handling of security pre-flask-sec. Remove
    functionality once registration is live.
    """
    if request.method == 'POST':
        uid = request.form['user-id']
        sec = request.form['security'].lower()
        usn = request.form['username']
        if len(usn) > 30:
            error = 'Username must be less than 30 characters. '
            return render_template('users.html', error=error)

        if sec == 'juggernaut2117':
            params = (usn, int(uid))
            do_update = UserService().update_username(params)
            if do_update == 'invalid':
                error = 'User ID incorrect or invalid, please contact admin. '
                return render_template('users.html', error=error)
            elif do_update:
                flash(f'Username successfully updated to {usn}')
                return redirect(url_for('home'))
            else:
                error = "An error occurred while updating, please contact the admin. "
            return render_template('users.html', error=error)
        else:
            error = "Security check failed. "
            return render_template('users.html', error=error)
    else:
        return render_template('users.html')


@app.route("/log_game", methods=["GET", "POST"])
@roles_accepted('admin', 'commissioner', 'scorekeeper')
def log_game():
    if request.method == 'POST':
        # Game Scores will be stored in the DB
        game_score = []

        # map usernames to userids
        un_to_uid = {}
        pairs = ScoringService().get_uid_username_pairs()
        for row in pairs:
            un_to_uid[row[1]] = row[0]

        game_num_to_id = {}
        game_pairs = ScoringService().get_game_num_id()
        for row in game_pairs:
            game_num_to_id[row[1]] = row[0]

        # raw scoring template
        player_scores = {
            "user_id": 0,
            "game_id": 0,
            "username": '',
            "place": 0,
            "pts_total": 0,
            "first_blood": False,
            "commcast": False,
            "commfourplus": False,
            "save": 0,
            "commkill": False,
            "attlast": False,
            "killall": False,
            "popvote": False
        }

        # pts by placement
        # place_scores = {1: 4, 2: 3, 3: 2, 4: 1}

        # copy the scoring template
        p_one = copy.deepcopy(player_scores)
        p_two = copy.deepcopy(player_scores)
        p_three = copy.deepcopy(player_scores)
        p_four = copy.deepcopy(player_scores)

        # Fill player dictionaries and append to games list
        player_dict = {"p_one": "p1", "p_two": "p2", "p_three": "p3", "p_four": "p4"}
        for k in player_dict:
            prefix = player_dict[k]
            if k == 'p_one':
                pdict = p_one
            elif k == 'p_two':
                pdict = p_two
            elif k == 'p_three':
                pdict = p_three
            elif k == 'p_four':
                pdict = p_four
            else:
                pass

            pdict['username'] = request.form[f'{prefix}_username']
            pdict['user_id'] = un_to_uid[pdict['username']]
            pdict['game_id'] = game_num_to_id[int(request.form['game_num'])]

            if request.form[f'{prefix}_place'] == 'first':
                pdict['place'] = 1
                pdict['pts_total'] += 4
            elif request.form[f'{prefix}_place'] == 'second':
                pdict['place'] = 2
                pdict['pts_total'] += 3
            elif request.form[f'{prefix}_place'] == 'third':
                pdict['place'] = 3
                pdict['pts_total'] += 2
            elif request.form[f'{prefix}_place'] == 'fourth':
                pdict['place'] = 4
                pdict['pts_total'] += 1

            if request.form.get(f'{prefix}_firstblood', False):
                pdict['first_blood'] = True
                pdict['pts_total'] += 1

            if request.form.get(f'{prefix}_commcast', False):
                pdict['commcast'] = True

            if not pdict['commcast']:
                pdict['pts_total'] -= 1

            if request.form.get(f'{prefix}_commplus', False):
                pdict['commfourplus'] = True
                pdict['pts_total'] += 1

            if request.form[f'{prefix}_save'] == 'one':
                pdict['save'] = 1
                pdict['pts_total'] += 1
            elif request.form[f'{prefix}_save'] == 'two':
                pdict['save'] = 2
                pdict['pts_total'] += 2
            elif request.form[f'{prefix}_save'] == 'three':
                pdict['save'] = 3
                pdict['pts_total'] += 3

            if request.form.get(f'{prefix}_commkill', False):
                pdict['commkill'] = True
                pdict['pts_total'] += 1

            if request.form.get(f'{prefix}_attlast', False):
                pdict['attlast'] = True
                pdict['pts_total'] -= 1

            if request.form.get(f'{prefix}_killall', False):
                pdict['killall'] = True
                pdict['pts_total'] -= 1

            if request.form.get(f'{prefix}_popvote', False):
                pdict['popvote'] = True
                pdict['pts_total'] += 1

            game_score.append(pdict)

        if len(game_score) == len(player_dict):
            num_scores = len(game_score)
            flash(f'Scores recorded for {num_scores} players. ')

        for score in game_score:
            uid = score['user_id']
            username = score['username']
            game_id = score['game_id']
            pts_total = score['pts_total']

            # add game_id
            insert = ScoringService().add_scores(uid, game_id, pts_total, score)
            if insert:
                flash(f'New score row successfully inserted for user: {username}.')
            else:
                flash(f'Something went wrong insert row for {username}, contact an admin.')

        return render_template('log_game.html')
    else:
        return render_template('log_game.html')

if __name__ == "__main__":
    app.run()
