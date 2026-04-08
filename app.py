from flask import Flask, render_template, request, redirect, session
import sqlite3
import os 

print("PATH:", os.getcwd())

user_data = {}

app = Flask(__name__)
app.secret_key = "secret123"

def init_db():
    print("DB INIT RUNNING")

    conn = sqlite3.connect('career.db')
    c = conn.cursor()


    c.execute('''
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        interest TEXT,
        skill Text,
        personality Text,
        marks INTEGER,
        careers TEXT
    )
    ''')

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/form')
def form():
    return render_template("form.html")

@app.route('/result', methods=['POST'])
def result():
    global user_data

    name = request.form['name']
    interest = request.form['interest']
    skill = request.form['skill']
    personality = request.form['personality']
    marks = int(request.form['marks'])

    # AI function
    best_career, score_data = get_career(interest, skill, personality, marks)

    # Top careers
    sorted_careers = sorted(score_data.items(), key=lambda x: x[1], reverse=True)
    careers = [c[0] for c in sorted_careers[:7]]

    total = sum(score_data.values()) or 1

    percentages = {}
    for k, v in score_data.items():
        percentages[k] = round((v / total) * 100, 2)

    # Save to DB
    conn = sqlite3.connect('career.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (name, interest, skill, personality, marks, careers) VALUES (?,?,?,?,?,?)",
              (name, interest, skill, personality, marks, ", ".join(careers)))
    conn.commit()
    conn.close()

    # Skills
    skills_data = {
        "AI Engineer": ["Python", "Machine Learning", "Data Science"],
        "Doctor": ["Biology", "Patient Care", "Medical Knowledge"],
        "Entrepreneur": ["Business Strategy", "Marketing", "Leadership"],
        "Data Scientist": ["Python", "Statistics", "Data Analysis"],
        "Software Developer": ["Programming", "Problem Solving", "Git"],
        "Graphic Designer": ["Photoshop", "Creativity", "UI/UX"],
        "Teacher": ["Communication", "Subject Knowledge", "Patience"],
        "Business Analyst": ["Excel", "Data Analysis", "Communication"]
    }

    skills = {}
    for c in careers:
        skills[c] = ", ".join(skills_data.get(c, ["Skill not defined"]))

    # Graph
    labels = list(score_data.keys())
    values = list(score_data.values())

    # Reason
    reason = f"Based on your interest in {interest}, skill in {skill}, and personality {personality}, these careers are suitable for you."

    # Save user data
    user_data = {
        "name": name,
        "careers": careers,
        "reason": reason
    }

    return render_template("result.html",
                           careers=careers,
                           name=name,
                           reason=reason,
                           labels=labels,
                           values=values,
                           percentages=percentages,
                           skills=skills)    

def get_career(interest, skill, personality, marks):

    score = {
        "AI Engineer": 0,
        "Doctor": 0,
        "Entrepreneur": 0,
        "Data Scientist": 0,
        "Software Developer": 0,
        "Graphic Designer": 0,
        "Teacher": 0,
        "Business Analyst": 0
    }

    # Interest
    if interest == "coding":
        score["AI Engineer"] += 3
    elif interest == "biology":
        score["Doctor"] += 3
    elif interest == "business":
        score["Entrepreneur"] += 3

    # Skill
    if skill == "medium":
        score["AI Engineer"] += 2
        score["Data Scientist"] += 1

    elif skill == "medium":
        score["AI Engineer"] += 2

    elif skill == "low":
        score["Entrepreneur"] +=1    

    # Personality
    if personality == "analytical":
        score["AI Engineer"] += 2
        score["Business Analyst"] += 2
    elif personality == "caring":
        score["Doctor"] += 2
        score["Teacher"] += 2

    # Extra Logic
    if interest == "coding":
        score["Software Developer"] += 3
        score["Data Scientist"] += 2

    if interest == "design":
        score["Graphic Designer"] += 3

    if interest == "teaching":
        score["Teacher"] += 3

    #  COMBO LOGIC (IMPORTANT)
    if interest == "coding" and skill == "high":
        score["AI Engineer"] += 3
        score["Software Developer"] += 2

    if interest == "biology" and personality == "caring":
        score["Doctor"] += 3

    if interest == "business" and personality == "analytical":
        score["Business Analyst"] += 3

    if skill == "low" and marks < 50:
        score["Entrepreneur"] += 2    

    # Marks
    if marks >= 85:
        score["AI Engineer"] += 2
        score["Doctor"] += 2
        score["Data Scientist"] += 2

    elif marks >= 60:
        score["Software Developer"] += 2
        score["Buisness Analyst"] += 2
    else:
        score["Entrepreneur"] += 2
        score["Graphic Designer"] +=2

    best_career = max(score, key=score.get)
    return best_career, score

@app.route('/history')
def history():

    conn = sqlite3.connect('career.db')
    c = conn.cursor()

    c.execute("SELECT * FROM users")
    data = c.fetchall()

    conn.close()

    return render_template("history.html", data=data)

@app.route('/career/<name>')
def career_detail(name):

    if name == "Software Developer":
        description = "Software Developers create applications, websites, and software systems using programming languages."

    elif name == "AI Engineer":
        description = "AI Engineers build artificial intelligence models and machine learning systems."

    elif name == "Data Scientist":
        description = "Data Scientists analyze large data sets to find patterns and insights."

    elif name == "Doctor":
        description = "Doctors diagnose and treat patients and work in hospitals and clinics."

    elif name == "Entrepreneur":
        description = "Entrepreneurs start and manage their own businesses."

    else:
        description = "This career has many opportunities and a bright future."


    return render_template("career.html", career=name, description=description)


@app.route('/admin')
def admin():

    if 'user' in session:

        conn = sqlite3.connect('career.db')
        c = conn.cursor()

        # 👇 FILTER VALUE
        interest_filter = request.args.get('interest')

        # 👇 FILTER APPLY
        if interest_filter:
            c.execute("SELECT * FROM users WHERE interest=?", (interest_filter,))
        else:
            c.execute("SELECT * FROM users")

        data = c.fetchall()

        # total users
        total_users = len(data)

        # interest count
        interest_count = {"coding":0, "biology":0, "business":0}

        c.execute("SELECT interest FROM users")
        interests = c.fetchall()

        for row in interests:
           if row[0] in interest_count:
              interest_count[row[0]] += 1

        conn.close()      

        return render_template("admin.html",
                               data=data,
                               total_users=total_users,
                               interest_data=list(interest_count.values()))

    else:
        return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        print("DEBUG:", username, password)

        if username == "admin" and password == "1234":
            session['user'] = username
            return redirect('/admin')
        else:
            return "Invalid Login"

    return render_template("login.html") 

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/chat', methods=['GET', 'POST'])
def chat():

    reply = ""

    if request.method == 'POST':
        msg = request.form['message'].lower()

        if "coding" in msg or "programming" in msg:
            reply = "You can become a Software Developer or AI Engineer."
        elif "biology" in msg:
            reply = "You can go for Doctor or Medical field."
        elif "business" in msg:
            reply = "Entrepreneur or Business Analyst is a good option."
        else:
            reply = "Explore your interests more to choose a career."

    return render_template("chat.html", reply=reply)    

if __name__ == "__main__":
    app.run(debug=True)