from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import random

app = Flask(__name__)
app.secret_key = 'super_secret_life_sim_key'

# Setup SQLite Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///life_simulator.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Helper function to clear or initialize game stats
def init_game():
    session['game_started'] = True
    session['cash'] = 1000
    session['happiness'] = 50
    session['relationship'] = 50
    session['job'] = "Unemployed"
    session['phase'] = "career"  # Phases: career -> relationship -> drama -> ending
    session['logs'] = ["Welcome to adulthood! You start with $1,000 and a dream."]

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        
        if User.query.filter((User.username == username) | (User.email == email)).first():
            return render_template('signup.html', error="Username or Email already registered.")
            
        hashed_pw = generate_password_hash(password, method='scrypt')
        new_user = User(username=username, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
        
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            init_game()
            return redirect(url_for('dashboard'))
            
        return render_template('login.html', error="Invalid email or password.")
        
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/game-action', methods=['POST'])
def game_action():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    choice = request.form.get('choice')
    phase = session.get('phase')
    
    if phase == "career":
        if choice == "1":
            session['job'] = "Corporate Drone"
            session['cash'] += 2000
            session['happiness'] -= 15
            session['logs'].append("💼 You became a Corporate Drone. The cubicle is drab, but the direct deposit hits nicely (+$2000, -15 Happiness).")
        elif choice == "2":
            session['job'] = "Indie Artist"
            session['cash'] -= 200
            session['happiness'] += 25
            session['logs'].append("🎨 You followed your artistic passion. Your bank account took a dip, but your spirit is free (-$200, +25 Happiness).")
        elif choice == "3":
            session['job'] = "Crypto Day Trader"
            session['cash'] = random.randint(100, 4500)
            session['happiness'] -= 5
            session['logs'].append(f"🪙 You dumped your savings into meme coins. Volatility strikes! Your cash randomized to ${session['cash']}.")
        session['phase'] = "relationship"

    elif phase == "relationship":
        if choice == "1":
            session['relationship'] += 40
            session['cash'] -= 800
            session['happiness'] += 15
            session['logs'].append("❤️ You went all-in on love with Taylor! Fancy dinners drained your wallet, but affection skyrocketed (-$800, +40 Romance).")
        elif choice == "2":
            session['relationship'] -= 10
            session['happiness'] += 10
            session['logs'].append("🕶️ You kept things casual with Taylor. Focused heavily on yourself (+10 Happiness, -10 Romance).")
        elif choice == "3":
            session['relationship'] = 10
            session['happiness'] -= 20
            session['logs'].append("💀 You ghosted Taylor entirely. You spend your nights scrolling social media full of regret (-20 Happiness, -40 Romance).")
        session['phase'] = "drama"

    elif phase == "drama":
        event = random.choice(["work_crisis", "family_loan", "jackpot"])
        if event == "work_crisis":
            if choice == "1":
                session['cash'] += 3000
                session['happiness'] -= 25
                session['logs'].append("😈 Villain Mode: You threw your coworker under the bus. Got a massive raise but lost your peace of mind (+$3000, -25 Happiness).")
            else:
                session['happiness'] += 20
                session['cash'] -= 500
                session['logs'].append("😇 Integrity Win: You stood up for your coworker. Your wallet suffered a fine, but you sleep great at night (-$500, +20 Happiness).")
        elif event == "family_loan":
            if choice == "1":
                session['cash'] = max(0, session['cash'] - 1500)
                session['happiness'] -= 10
                session['logs'].append("💸 Family emergency: You loaned money to an uncle's sketchy startup. It went bankrupt instantly (-$1500).")
            else:
                session['happiness'] -= 15
                session['relationship'] -= 15
                session['logs'].append("🚫 You blocked your relative. Holiday dinners are going to be incredibly awkward (-15 Happiness, -15 Family Dynamics).")
        elif event == "jackpot":
            session['cash'] += 5000
            session['happiness'] += 20
            session['logs'].append("🎉 Absolute Win: You uncovered a cold wallet with old Bitcoin! You liquidated it instantly (+$5000, +20 Happiness).")
        session['phase'] = "ending"

    # Enforce constraints
    session['happiness'] = max(0, min(100, session['happiness']))
    session['relationship'] = max(0, min(100, session['relationship']))
    session.modified = True
    return redirect(url_for('dashboard'))

@app.route('/restart')
def restart():
    init_game()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Force table creation on production cloud servers
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
