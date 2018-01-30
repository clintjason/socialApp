from flask import Flask, render_template, request, url_for, flash, session, redirect
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, IntegerField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from flask_socketio import SocketIO, emit
from pprint import pprint

app = Flask(__name__)
app.secret_key='secret123'
socketio = SocketIO( app )

def messageRecived():
  print( 'message was received!!!' )


@socketio.on( 'my event' )
def handle_my_custom_event( json ):
  print( 'recived my event: ' + str( json ) )
  # connections.append(json)
  # socketio.emit( 'update connections', connections, callback=updateConnections )
  socketio.emit( 'my response', json, callback=messageRecived )

# connections = []


#Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'XXXX'
app.config['MYSQL_PASSWORD'] = 'XXXX'
app.config['MYSQL_DB'] = 'XXXX'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#init mysql
mysql = MySQL(app)

@app.route('/')
def home():
	return render_template('home.html')

@app.route('/chat')
def chat():
	return render_template('chat.html')

class RegisterForm(Form):
	name = StringField('Name', [validators.Length(min=1, max=50)])
	username = StringField('Username', [validators.Length(min=3, max=25)])
	email = StringField('Email', [validators.Length(min=6, max=50)])
	password = PasswordField('Password', [
		validators.DataRequired(),
		validators.EqualTo('confirm', message='Passwords do not match')
	])
	confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))

		# Create cursor
		cur = mysql.connection.cursor()

		cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))
		#Commit to DB
		mysql.connection.commit()

		#Close connection
		cur.close()

		flash('You are now registered and can log in', 'success')

		return redirect(url_for('login'))

	return render_template('register.html', form=form)

#user login
@app.route('/add_friend', methods=['GET', 'POST'])
def add_friend():
	if request.method == 'POST':
		#get form fields
		sender_id = request.form['sender_id']
		receiver_id = request.form['receiver_id']

		#Create cursor
		cur = mysql.connection.cursor()
		
		# Get user by username
		result = cur.execute("INSERT INTO friend_requests(sender_id, receiver_id) VALUES(%s, %s)", (sender_id, receiver_id))
		#Commit to DB
		mysql.connection.commit()
		
		cur.close()
		
		return receiver_id
	return receiver_id

#user reject friend
@app.route('/reject_friend', methods=['GET', 'POST'])
def reject_friend():
	if request.method == 'POST':
		#get form fields
		sender_id = request.form['sender_id']
		receiver_id = request.form['receiver_id']
		# pprint(sender_id)

		#Create cursor
		cur = mysql.connection.cursor()
		
		# delete
		result = cur.execute("DELETE FROM friend_requests WHERE sender_id=%s AND receiver_id=%s", (sender_id, receiver_id))

		#Commit to DB
		mysql.connection.commit()
		
		cur.close()
		
		return receiver_id
	return receiver_id

#user accept friend
@app.route('/accept_friend', methods=['GET', 'POST'])
def accept_friend():
	if request.method == 'POST':
		#get form fields
		sender_id = request.form['sender_id']
		receiver_id = request.form['receiver_id']
		# pprint(sender_id)

		#Create cursor
		cur = mysql.connection.cursor()
		
		# delete
		result = cur.execute("INSERT INTO friends(sender_id, receiver_id) VALUES(%s, %s)", (sender_id, receiver_id))

		#Commit to DB
		mysql.connection.commit()

		result = cur.execute("DELETE FROM friend_requests WHERE sender_id=%s, receiver_id=%s", (sender_id, receiver_id))

		#Commit to DB
		mysql.connection.commit()
		

		cur.close()
		
		return receiver_id
	return receiver_id

	# 	if result > 0:
	# 		# Get the stored hash
	# 		data = cur.fetchone()
	# 		password = data['password']

	# 		#compare the passwords
	# 		if sha256_crypt.verify(password_candidate, password):
	# 			#passed
	# 			session['logged_in'] = True;
	# 			session['username'] = username
	# 			session['id'] = data['id']

	# 			flash('You are now logged in', 'success')
	# 			return redirect(url_for('profile'))
	# 		else:
	# 			error = 'Invalid login'
	# 			return render_template('login.html', error=error)
	# 			#close connection
	# 		cur.close()
	# 	else:
	# 		error = 'Username not found'
	# 		return render_template('login.html', error=error)

	# return render_template('login.html')




#user login
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		#get form fields
		username = request.form['username']
		password_candidate = request.form['password']

		#Create cursor
		cur = mysql.connection.cursor()

		# Get user by username
		result = cur.execute("SELECT * FROM users WHERE username=%s", [username])

		if result > 0:
			# Get the stored hash
			data = cur.fetchone()
			password = data['password']

			#compare the passwords
			if sha256_crypt.verify(password_candidate, password):
				#passed
				session['logged_in'] = True;
				session['username'] = username
				session['id'] = data['id']

				flash('You are now logged in', 'success')
				return redirect(url_for('profile'))
			else:
				error = 'Invalid login'
				return render_template('login.html', error=error)
				#close connection
			cur.close()
		else:
			error = 'Username not found'
			return render_template('login.html', error=error)

	return render_template('login.html')


# Check if user logged in
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorized, Please login', 'danger')
			return redirect(url_for('login'))
	return wrap

#Dashboard
@app.route('/profile')
@is_logged_in
def profile():
	# Create cursor
	cur = mysql.connection.cursor()

	# Get users
	result = cur.execute("SELECT * FROM users")

	users = cur.fetchall()

	# Get users
	result = cur.execute("SELECT * FROM posts WHERE username=%s", [session['username']])

	posts = cur.fetchall()

	# Get users
	result = cur.execute("SELECT * FROM friends WHERE sender_id=%s OR receiver_id=%s", [session['id'], session['id']])

	friends = []

	for id in cur.fetchall():
		if get_user_by_id(id['receiver_id']) != session['id']:
			friends.append(get_user_by_id(id['receiver_id']))
			
		if get_user_by_id(id['sender_id']) == session['id']:
			friends.append(get_user_by_id(id['sender_id']))
			
		# pprint(friend_requests)

	# result = cur.execute("SELECT sender_id FROM friend_requests WHERE receiver_id=%s", [session['id']])
	result = cur.execute("SELECT * FROM friend_requests WHERE receiver_id=%s", [session['id']])
	# request_ids = get_user_by_id(result)
	friend_requests = []

	for id in cur.fetchall():
		friend_requests.append(get_user_by_id(id['sender_id']))
		# pprint(friend_requests)

	# Close connection
	cur.close()
	# print(friend_requests)
	return render_template('profile.html', users=users, posts=posts, friend_requests=friend_requests, friends=friends)



# Logout
@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash('You are now logged out', 'success')
	return redirect(url_for('login'))


# # Posts form class
class PostForm(Form):
	title = StringField('Title', [validators.Length(min=1, max=200)])
	post = TextAreaField('Post', [validators.required()])
	


# Socialze
@app.route('/socialize', methods=['GET', 'POST'])
@is_logged_in
def socialize():
	form = PostForm(request.form)
	if request.method == 'POST' and form.validate():
		title = form.title.data
		post = form.post.data
		username = session['username']
		

		# Create Cursor
		cur = mysql.connection.cursor()

		# Execute
		cur.execute("INSERT INTO posts (username, title, post) VALUES (%s, %s, %s)", (username, title, post))

		#Commit to DB
		mysql.connection.commit()

		# Close connection
		cur.close()

		flash('Post added', 'success')

		return redirect(url_for('profile'))


	# Create cursor
	cur = mysql.connection.cursor()

	# Get users
	result = cur.execute("SELECT * FROM users")

	users = cur.fetchall()

	# Get users
	result = cur.execute("SELECT * FROM posts")

	posts = cur.fetchall()

	# result = cur.execute("SELECT sender_id FROM friend_requests WHERE receiver_id=%s", [session['id']])
	result = cur.execute("SELECT * FROM friend_requests WHERE receiver_id=%s", [session['id']])
	# request_ids = get_user_by_id(result)
	friend_requests = []

	for id in cur.fetchall():
		friend_requests.append(get_user_by_id(id['sender_id']))
		# pprint(friend_requests)

	# Close connection
	cur.close()
	# print(friend_requests)
	return render_template('socialize.html', users=users, friend_requests=friend_requests, form=form, posts=posts)


def get_user_by_id(id):
	# Create cursor
	cur = mysql.connection.cursor()

	# Get users
	result = cur.execute("SELECT * FROM users WHERE id=%s", [id])

	user = cur.fetchone()

	
	# Close connection
	cur.close()	
	return user






if __name__=='__main__':
	# socketio.run( app, debug = True, host'10.42.0.12' )
	socketio.run( app, debug = True )
