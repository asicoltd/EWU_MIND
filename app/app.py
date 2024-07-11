from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import csv
from datetime import datetime
app = Flask(__name__)
app.secret_key = 'root'

# Example data structures (replace with actual data parsing)
users = {}
news = {}
recommend = []
userpass = []
# Function to parse behavior.tsv file
def parse_behavior_tsv():
    behavior_file = 'database/behaviors.csv'
    with open(behavior_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            user_id = row[1]
            interaction_time = datetime.strptime(row[2], '%m/%d/%Y %I:%M:%S %p')
            clicked_news_ids = row[4].split()
            
            if user_id not in users:
                users[user_id] = []
            
            users[user_id].append({
                'interaction_time': interaction_time,
                'clicked_news_ids': clicked_news_ids
            })

# Function to parse news.tsv file
def parse_news_tsv():
    news_file = 'database/news.csv'
    with open(news_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            if len(row) >= 7:
                news_id = row[0]
                category = row[1]
                subcategory = row[2]
                title = row[3]
                abstract = row[4]
                url = row[5]
                entities = row[6]  # Assuming entities are in the 7th column
                news[news_id] = {
                    'category': category,
                    'subcategory': subcategory,
                    'title': title,
                    'abstract': abstract,
                    'url': url,
                    'entities': entities
                }

# Function to read recommendations from CSV
def read_recommendations_from_csv():
    recommendations = []
    with open('database/recommendations.csv', 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            user_id = row[0]
            recommended_news_ids = row[1:]
            recommended_news = []
            for news_id in recommended_news_ids:
                if news_id in news:
                    recommended_news.append(news[news_id])
            recommendations.append({'user_id': user_id, 'recommended_news': recommended_news})
    return recommendations

def topNews_from_csv():
    topNews = []
    with open('database/topNews.csv', 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            recommended_news = []
            if row[0] in news:
                recommended_news.append(news[row[0]])
                topNews.append({'news_id': row[0],'Total_click':row[1],'recommended_news': recommended_news})
    return topNews
def userpass_from_csv():
    userpass = []
    with open('database/userpass.csv', 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            userpass.append({'id': row[0],'pass':row[1]})
    return userpass
def NewsData_from_csv():
    NewsData = []
    #NewsID,Likes,Dislikes,Neutrals,Total Clicks
    with open('database/newsData.csv', 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        mosttc = 0
        for row in reader:
            NewsDetails = []
            if row[0] in news:  # Assuming 'news' is a dictionary where keys are news IDs
                NewsDetails.append(news[row[0]])
                NewsData.append({
                    'news_id': row[0],
                    'like': int(row[1]),  # Convert 'like' to integer for sorting
                    'dislike': int(row[2]),
                    'none': int(row[3]),
                    'tc': int(row[4]),
                    'data': NewsDetails
                })
                if int(row[4]) > mosttc:
                    mosttc = int(row[4])
    # Sort NewsData by 'like' in descending order
    sorted_news_data = sorted(NewsData, key=lambda x: x['tc'], reverse=True)
    return sorted_news_data


parse_behavior_tsv()
parse_news_tsv()
recommend = read_recommendations_from_csv()
topNews = topNews_from_csv()
newsStat = NewsData_from_csv()
userpass = userpass_from_csv()
# Routes

@app.route('/')
def index():
    return render_template('index.html')

ADMIN_CREDENTIALS = {
    'admin': 'admin',
}

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/admin', methods=['POST'])
def admin_login():
    admin_id = request.form['admin_id']
    password = request.form['password']

    if admin_id in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[admin_id] == password:
        # Authentication successful, redirect to admin panel
        return redirect(url_for('admin_dashboard'))
    else:
        # Authentication failed, redirect back to login page
        flash('Invalid user ID or password', 'error')
        return redirect(url_for('login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/admin/add_news', methods=['GET', 'POST'])
def add_news():
    if request.method == 'POST':
        # Handle adding new news logic here
        return redirect(url_for('admin_dashboard'))
    return render_template('add_news.html')
def add_news():
    if request.method == 'POST':
        news_id = request.form['news_id']
        title = request.form['title']
        category = request.form['category']
        subcategory = request.form.get('subcategory', '')
        url = request.form['url']
        tags = request.form.get('tags', '')

        # Append the data to news.tsv file
        with open('database/news.tsv', 'a', newline='', encoding='utf-8') as file:
            file.write(f"{news_id}\t{category}\t{subcategory}\t{title}\t{url}\t{tags}\n")
            return 'News added successfully!'
    return redirect(url_for('admin_dashboard'))
    
@app.route('/admin/all_users')
def all_users():
    return render_template('all_users.html', users=users)


@app.route('/news_list')
def news_list():
    return render_template('news_list.html', news=news, newsStat = newsStat[:100])


@app.route('/like_news', methods=['POST'])
def like_news():
    data = request.get_json()
    # Find the news item in newsStat based on news_id and update the like count
    for news_item in newsStat:
        if news_item['news_id'] == data['news_id']:
            if data['user_id'] in users:
                news_item['like'] += 1
                news_item['tc'] += 1
                break
    
    return jsonify({'message': 'Liked!'})

@app.route('/dislike_news', methods=['POST'])
def dislike_news():
    data = request.get_json()
    
    # Find the news item in newsStat based on news_id and update the dislike count
    for news_item in newsStat:
        if news_item['news_id'] == data['news_id']:
            if data['user_id'] in users:
                news_item['dislike'] += 1
                news_item['tc'] += 1
                break
    
    return jsonify({'message': 'Disliked!'})
@app.route('/admin/recommendations')
def recommendations():
    
    return render_template('recommendations.html', recommend = recommend)

@app.route('/user/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        
        # Example authentication logic
        if authenticate_user(user_id, password):
            # Authentication successful
            session['user_id'] = user_id
            return redirect(url_for('user_home'))
        else:
            # Authentication failed
            flash('Invalid user ID or password', 'error')
            return render_template('signin.html')  # Render the template with the flash message

    return render_template('signin.html')

def authenticate_user(user_id, password):
    for data in userpass:
        if user_id == data.get('id'): 
            if password == data.get('pass'):
                return True
    return False

@app.route('/user/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('pass')
        if user_id not in users:
            userpass.append({'id': user_id, 'pass': password})
            users[user_id] = []
            session['user_id'] = user_id
            return redirect(url_for('user_home'))
        else:
            return "User already exists"
    return render_template('signup.html')


@app.route('/user/home')
def user_home():
    user_id = session.get('user_id')
    if user_id:
        for i in users:
            if i == user_id:
                user_interactions = users[i]
        recommend = read_recommendations_from_csv()
        user_recommendations = []
        for i in recommend:
            
            if i['user_id'] == user_id:
                user_recommendations = i
        return render_template('user_home.html', user_id=user_id, user_interactions = user_interactions, topNews = topNews, news = news, user_recommendations = user_recommendations)
    else:
        return redirect(url_for('signin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
