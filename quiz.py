import streamlit as st
import requests
import html
import random
import json
import os
from datetime import datetime, timedelta

STREAK_FILE = "streak.json"
TRIVIA_API_URL = "https://opentdb.com/api.php"
CATEGORIES_URL = "https://opentdb.com/api_category.php"

# --------------------------
# Streak Management Functions
# --------------------------
def load_streak_data():
    """Load streak data from JSON file"""
    if os.path.exists(STREAK_FILE):
        with open(STREAK_FILE, "r") as f:
            return json.load(f)
    return {"streak": 0, "last_play_date": None}

def save_streak_data(streak, last_play_date):
    """Save streak data to JSON file"""
    with open(STREAK_FILE, "w") as f:
        json.dump({"streak": streak, "last_play_date": last_play_date}, f)

def calculate_streak(current_streak, last_play_date):
    """Calculate new streak based on last play date"""
    today = datetime.now().date()
    if not last_play_date:
        return 1
    
    last_play = datetime.strptime(last_play_date, "%Y-%m-%d").date()
    days_since_last = (today - last_play).days
    
    if days_since_last == 1:  # Consecutive day
        return current_streak + 1
    elif days_since_last == 0:  # Same day
        return current_streak
    else:  # Broken streak
        return 1

# --------------------------
# Quiz Core Functions
# --------------------------
def get_categories():
    """Fetch available quiz categories"""
    response = requests.get(CATEGORIES_URL)
    return response.json()["trivia_categories"]

def fetch_question(category_id):
    """Fetch a new question from API"""
    try:
        params = {"amount": 1, "category": category_id, "type": "multiple"}
        response = requests.get(TRIVIA_API_URL, params=params, timeout=10)
        data = response.json()
        if data["response_code"] != 0 or not data["results"]:
            return None
        
        question_data = data["results"][0]
        return {
            "question": html.unescape(question_data["question"]),
            "correct": html.unescape(question_data["correct_answer"]),
            "options": [html.unescape(ans) for ans in question_data["incorrect_answers"]] + [html.unescape(question_data["correct_answer"])]
        }
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

# --------------------------
# Quiz Display Functions
# --------------------------
def display_quiz_page():
    """Main quiz interface"""
    # Load streak data
    streak_data = load_streak_data()
    current_streak = streak_data["streak"]
    last_play_date = streak_data["last_play_date"]
    today = datetime.now().date()
    today_str = today.strftime("%Y-%m-%d")
    
    # Initialize session state
    if 'quiz' not in st.session_state:
        st.session_state.quiz = {
            'current_question': None,
            'selected_answer': None,
            'daily_attempt_used': last_play_date == today_str,
            'categories': get_categories(),
            'selected_category': None,
            'result_data': None,
            'practice_mode': False,
            'show_practice_button': False,
            'force_refresh': False,
            'retry_count': 0
        }

    # Custom styling
    st.markdown("""
    <style>
        .quiz-card {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .option-btn {
            width: 100% !important;
            padding: 15px !important;
            border-radius: 10px !important;
            border: 2px solid #74b9ff !important;
            background: white !important;
            color: #2d3436 !important;
            margin-bottom: 12px !important;
        }
        .option-btn:hover {
            background: #74b9ff !important;
            color: white !important;
        }
    </style>
    """, unsafe_allow_html=True)

    st.title("Daily Quiz")
    st.subheader(f"🔥 Current Streak: {current_streak} days")

    # Show results if available
    if st.session_state.quiz['result_data']:
        is_correct, correct_answer = st.session_state.quiz['result_data']
        result_color = "#2ecc71" if is_correct else "#e74c3c"
        
        st.markdown(f"""
        <div style="padding:20px; border-radius:10px; 
                    background:{"#d1fae5" if is_correct else "#fee2e2"}; 
                    margin:20px 0;">
            <h3 style="color:{result_color}; margin:0;">
                {'✅ Correct!' if is_correct else '❌ Incorrect!'}
            </h3>
            <p style="color:{result_color};">
                {f"Correct answer: {correct_answer}" if not is_correct else "Well done!"}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show practice mode button only after daily attempt
        if not st.session_state.quiz['practice_mode'] and st.session_state.quiz['show_practice_button']:
            if st.button("🌱 Enter Practice Mode"):
                st.session_state.quiz.update({
                    'practice_mode': True,
                    'current_question': None,
                    'selected_answer': None,
                    'result_data': None
                })
                st.rerun()
        
        # Show next question button in practice mode
        if st.session_state.quiz['practice_mode']:
            if st.button(" Next  Challenge", type="primary"):
                st.session_state.quiz.update({
                    'current_question': None,
                    'selected_answer': None,
                    'result_data': None,
                    'show_practice_button': False
                })
                st.rerun()
        return

    # Daily attempt check
    if st.session_state.quiz['daily_attempt_used'] and not st.session_state.quiz['practice_mode']:
        st.warning("You've already played today!")
        if st.button("🌱 Enter Practice Mode"):
            st.session_state.quiz.update({
                'practice_mode': True,
                'daily_attempt_used': False
            })
            st.rerun()
        return

    # Category selection
    if not st.session_state.quiz['selected_category']:
        category_names = [cat['name'] for cat in st.session_state.quiz['categories']]
        selected = st.selectbox("Select Quiz Category:", category_names)
        
        if st.button("Start Quiz"):
            selected_category = next(cat for cat in st.session_state.quiz['categories'] if cat['name'] == selected)
            st.session_state.quiz['selected_category'] = selected_category['id']
            with st.spinner("🌍 Loading  question..."):
                question_data = fetch_question(st.session_state.quiz['selected_category'])
            if question_data:
                random.shuffle(question_data['options'])
                st.session_state.quiz['current_question'] = question_data
                st.rerun()
            else:
                st.error("Failed to load questions. Please try another category.")

    # Question handling
    if st.session_state.quiz['current_question']:
        q = st.session_state.quiz['current_question']
        
        with st.container():
            st.markdown(f"""
            <div class="quiz-card">
                <h3>{q['question']}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            options = q['options']
            
            with col1:
                if st.button(options[0], key="opt1"):
                    st.session_state.quiz['selected_answer'] = options[0]
                if st.button(options[1], key="opt2"):
                    st.session_state.quiz['selected_answer'] = options[1]
            
            with col2:
                if st.button(options[2], key="opt3"):
                    st.session_state.quiz['selected_answer'] = options[2]
                if st.button(options[3], key="opt4"):
                    st.session_state.quiz['selected_answer'] = options[3]
    else:
        # Automatically fetch new question when in practice mode
        if st.session_state.quiz['practice_mode'] and st.session_state.quiz['selected_category']:
            try:
                with st.spinner("🌱 Growing your next question..."):
                    question_data = fetch_question(st.session_state.quiz['selected_category'])
                
                if question_data:
                    random.shuffle(question_data['options'])
                    st.session_state.quiz['current_question'] = question_data
                    st.session_state.quiz['selected_answer'] = None
                    st.rerun()
                else:
                    st.error("⚠️ Couldn't find more questions in this category. Try another one!")
                    
            except Exception as e:
                st.error(f"🌪️ Oops! A storm blocked our connection: {str(e)}")

    # Handle answer submission
    if st.session_state.quiz['selected_answer']:
        is_correct = st.session_state.quiz['selected_answer'] == st.session_state.quiz['current_question']['correct']
        correct_answer = st.session_state.quiz['current_question']['correct']
        
        # Update streak only for daily attempts
        if not st.session_state.quiz['practice_mode'] and last_play_date != today_str:
            new_streak = calculate_streak(current_streak, last_play_date)
            save_streak_data(new_streak, today_str)
            st.session_state.quiz.update({
                'daily_attempt_used': True,
                'show_practice_button': True
            })
        
        # Store result and update UI
        st.session_state.quiz['result_data'] = (is_correct, correct_answer)
        st.balloons()
        st.rerun()