import os
import time
import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder

# --- PAGE CONFIGURATION & CSS TO HIDE AUDIO PLAYER ---
st.set_page_config(page_title="EchoSpeech SLP Coach", layout="wide")

st.markdown("""
    <style>
        /* Hides the native audio player UI completely while allowing audio playback execution */
        [data-testid="stAudio"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

# --- MOCK USER DATABASE (Stores credentials and profiles) ---
if "user_credentials" not in st.session_state:
    st.session_state.user_credentials = {
        "ralph": "speech2026"
    }

if "user_profiles" not in st.session_state:
    st.session_state.user_profiles = {}

# --- INITIALIZE AUTHENTICATION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# --- LOGIN / SIGN UP GATEWAY ---
if not st.session_state.logged_in:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=200)
    st.title("🔐 Secure Portal")
    st.write("Welcome! Please sign in to your personal profile or create a new account to track your fluency, homework, and session analytics.")
    
    auth_tab1, auth_tab2 = st.tabs(["Sign In", "Create Account (Sign Up)"])
    
    with auth_tab1:
        st.subheader("Sign In to Existing Account")
        
        login_user = st.text_input("Username", key="login_user").strip().lower()
        login_pass = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Sign In", key="btn_signin"):
            if login_user in st.session_state.user_credentials and st.session_state.user_credentials[login_user] == login_pass:
                st.session_state.logged_in = True
                st.session_state.username = login_user
                st.success(f"Welcome back, {login_user}!")
                st.rerun()
            else:
                st.error("Invalid username or password. Please check your credentials or create a new account.")
                
    with auth_tab2:
        with st.form("signup_form"):
            st.subheader("Create a New Account")
            new_user = st.text_input("Choose Username", key="new_user").strip().lower()
            new_pass = st.text_input("Choose Password", type="password", key="new_pass")
            confirm_pass = st.text_input("Confirm Password", type="password", key="confirm_pass")
            
            submit_signup = st.form_submit_button("Register Account")
            
            if submit_signup:
                if not new_user or not new_pass:
                    st.error("Please fill in both username and password fields.")
                elif new_user in st.session_state.user_credentials:
                    st.error("That username already exists. Please pick another or sign in.")
                elif new_pass != confirm_pass:
                    st.error("Passwords do not match.")
                else:
                    st.session_state.user_credentials[new_user] = new_pass
                    st.session_state.logged_in = True
                    st.session_state.username = new_user
                    st.success(f"Account created successfully! Welcome, {new_user}!")
                    st.rerun()
                
    st.stop()

# --- INITIALIZE USER-SPECIFIC PROFILE DATA ---
current_user = st.session_state.username
if current_user not in st.session_state.user_profiles:
    st.session_state.user_profiles[current_user] = {
        "filler_count": 0,
        "pause_count": 0,
        "stutter_count": 0,
        "turns_practiced": 0,
        "current_homework": "Practice conscious diaphragmatic breathing paired with light articulatory contact and gentle onsets.",
        "homework_assigned_this_session": False,
        "avatar": "🧑‍💼",
        "custom_avatar_file": None,
        "latest_audio_bytes": None,
        "messages": []
    }

user_data = st.session_state.user_profiles[current_user]

# --- SIDEBAR CONTROLS & USER PROFILE DASHBOARD ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=80)
    st.markdown("---")
    st.subheader("👤 User Profile")

col_av1, col_av2 = st.sidebar.columns([1, 2])
with col_av1:
    if user_data["custom_avatar_file"] is not None:
        st.image(user_data["custom_avatar_file"], width=50)
    else:
        st.markdown(f"<h1 style='text-align: center; margin: 0;'>{user_data['avatar']}</h1>", unsafe_allow_html=True)
with col_av2:
    st.write(f"**{current_user.capitalize()}**")

with st.sidebar.expander("🖼️ Change Profile Photo/Avatar"):
    avatar_choice = st.selectbox(
        "Choose Preset Emoji Avatar:",
        ["🧑‍💼", "👨‍🎤", "👩‍💻", "🧑‍🎓", "🦸‍♂️", "🦊", "🌟"],
        index=0
    )
    if st.button("Update Emoji Avatar"):
        user_data["avatar"] = avatar_choice
        user_data["custom_avatar_file"] = None
        st.success("Avatar updated!")
        st.rerun()

    uploaded_avatar = st.file_uploader("Or Upload Custom Photo", type=["png", "jpg", "jpeg"])
    if uploaded_avatar is not None:
        user_data["custom_avatar_file"] = uploaded_avatar
        st.success("Profile photo uploaded!")
        st.rerun()

if st.sidebar.button("Log Out"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ Session Settings")

age_group = st.sidebar.selectbox(
    "User Age / Vocabulary Level:",
    ["Child (Ages 6–10)", "Teenager (Ages 11–17)", "Adult / Professional (18+)" ],
    key=f"{current_user}_age"
)

scenario = st.sidebar.selectbox(
    "Choose Practice Scenario:",
    ["Clinical Fluency & General Conversation", "Job Interview Simulation", "Public Speaking Presentation Q&A", "Casual Social Small Talk"],
    key=f"{current_user}_scenario"
)

speech_speed = st.sidebar.slider("Coach Voice Speed:", 0.75, 1.25, 0.90, 0.05, key=f"{current_user}_speed")

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Personal Analytics")
st.sidebar.metric(label="Total Turns Practiced", value=user_data["turns_practiced"])
st.sidebar.metric(label="Logged Fillers", value=user_data["filler_count"])
st.sidebar.metric(label="Caught Pauses/Blocks", value=user_data["pause_count"])
st.sidebar.metric(label="Caught Stuttering/Repetitions", value=user_data["stutter_count"])

# Persistent Homework Panel with Interactive Controls
st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Active Home Exercise")
st.sidebar.info(user_data["current_homework"])

if st.sidebar.button("Discuss Homework / Start Practice"):
    homework_prompt = f"Let's review my current technical home assignment: {user_data['current_homework']}. Evaluate my clinical progress and give me expert speech pathology feedback."
    user_data["messages"].append({"role": "user", "content": homework_prompt})
    
    response = OpenAI().chat.completions.create(model="gpt-4o-mini", messages=user_data["messages"])
    coach_reply = response.choices[0].message.content
    user_data["messages"].append({"role": "assistant", "content": coach_reply})
    
    speech_file_path = "assistant_voice.mp3"
    voice_resp = OpenAI().audio.speech.create(model="tts-1", voice="alloy", input=coach_reply, speed=speech_speed)
    voice_resp.stream_to_file(speech_file_path)
    with open(speech_file_path, "rb") as f:
        user_data["latest_audio_bytes"] = f.read()
    if os.path.exists(speech_file_path):
        os.remove(speech_file_path)
    st.rerun()

if st.sidebar.button("Exit Homework / Return to General Session"):
    exit_prompt = "Let's move on from the assignment discussion and continue our general clinical speech therapy session."
    user_data["messages"].append({"role": "user", "content": exit_prompt})
    
    response = OpenAI().chat.completions.create(model="gpt-4o-mini", messages=user_data["messages"])
    coach_reply = response.choices[0].message.content
    user_data["messages"].append({"role": "assistant", "content": coach_reply})
    
    speech_file_path = "assistant_voice.mp3"
    voice_resp = OpenAI().audio.speech.create(model="tts-1", voice="alloy", input=coach_reply, speed=speech_speed)
    voice_resp.stream_to_file(speech_file_path)
    with open(speech_file_path, "rb") as f:
        user_data["latest_audio_bytes"] = f.read()
    if os.path.exists(speech_file_path):
        os.remove(speech_file_path)
    st.rerun()

# --- MAIN APP UI ---
st.title("EchoSpeech: Clinical Speech Pathology & Fluency Coach")
st.write(f"Logged in as **{current_user}**. Your custom profile, ongoing session, analytics, and homework assignments remain active.")

with st.expander("🧘 Pre-Speech Pacing Anchor"):
    st.write("Take a relaxed breath, pace your phrasing naturally, and respond as you would in a normal, everyday conversation.")

# --- DYNAMIC AGE VOCABULARY MAPPING ---
if "Child" in age_group:
    age_guideline = "Use simple, direct, and straightforward language appropriate for a child aged 6-10."
elif "Teenager" in age_group:
    age_guideline = "Use straightforward, concise, and direct language appropriate for a teenager aged 11-17."
else:
    age_guideline = "Use professional, objective, and clinical language appropriate for an adult."

# --- SYSTEM PROMPT BUILDER ---
if user_data["homework_assigned_this_session"]:
    homework_rule = "STRICT RULE: A targeted speech therapy homework assignment HAS ALREADY BEEN GIVEN during this session. You are strictly forbidden from ever mentioning, referencing, or repeating homework assignments again during this conversation."
else:
    homework_rule = "STRICT RULE: You must assign EXACTLY ONE targeted speech therapy homework assignment during this session focused on overcoming the specific speech challenges detected, using the exact format 'Homework Assignment: [task]'. Once given, you must never mention homework again for the rest of the session."

vocab_guideline = (
    f"You are a licensed Speech-Language Pathologist (SLP) specializing in fluency disorders and advanced motor-speech mechanics. {age_guideline} "
    "TONE DIRECTIVE: Be highly technical, objective, and precise. Completely avoid excessive praise or generic encouragement. Focus deeply on explicit speech pathology interventions, physiological mechanics (e.g., vocal fold adduction, airflow management, articulatory contact pressure, rate control, and proprioceptive monitoring). "
    "ANTI-ECHO RULE: Do NOT repeat, echo, or paraphrase what the user just said at the beginning of your response. Instead, give a brief, clinical acknowledgement (e.g., 'Acknowledged.', 'Data noted.', 'Let's examine the mechanics.') followed immediately by your technical analysis and coaching. "
    "Your core functions are strictly focused on three pillars: "
    "1. Be a Speech Pathologist: Provide advanced clinical diagnoses of blocks, prolongations, and repetitions, prescribing specific fluency-shaping techniques (e.g., easy onsets, light articulatory contacts, prolonged speech, variable rate control) or stuttering-modification techniques (e.g., cancellations, pull-outs, preparatory sets). "
    "2. Recommend Better Sentence Structuring: Provide advanced syntactic restructuring guidance to reduce cognitive and articulatory load on complex utterances. "
    "3. Be a Speech Coach: Guide breath support, respiratory-phonatory coordination, and pacing dynamics rigorously. "
    f"{homework_rule} "
    "Maintain an ongoing, clinical dialogue, and always conclude your response with a targeted, technical open-ended question to drive the session forward."
)

system_prompt = f"{vocab_guideline} Current scenario: {scenario} for {age_group}. Active homework assignment: {user_data['current_homework']}"

if not user_data["messages"]:
    user_data["messages"] = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": f"Hello. I am your clinical Speech-Language Pathologist and fluency coach. Let's begin our session. State your opening phrase, and we will analyze your motor-speech mechanics and syntax."}
    ]

for message in user_data["messages"]:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.write(message["content"])

client = OpenAI()

# --- HIDDEN AUTOPLAY AUDIO PROCESSOR ---
if user_data["latest_audio_bytes"] is not None:
    audio_to_play = user_data["latest_audio_bytes"]
    user_data["latest_audio_bytes"] = None
    st.audio(audio_to_play, format="audio/mp3", autoplay=True)

# --- RECORDING & PROCESSING SECTION ---
st.write("### Your Turn to Speak:")
audio_data = mic_recorder(start_prompt="🔴 Start Recording", stop_prompt="⏹️ Stop Recording", just_once=False, key=f'{current_user}_speech_recorder')

if audio_data and isinstance(audio_data, dict) and audio_data.get('bytes'):
    audio_bytes = audio_data['bytes']
    
    if audio_bytes and audio_data != st.session_state.get('last_processed_audio'):
        st.session_state['last_processed_audio'] = audio_data
        
        with st.spinner("Executing acoustic and phonetic analysis, evaluating motor-speech mechanics..."):
            audio_file_path = "temp_audio.wav"
            with open(audio_file_path, "wb") as f:
                f.write(audio_bytes)

            with open(audio_file_path, "rb") as audio_file:
                transcript_response = client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file, response_format="verbose_json", timestamp_granularities=["word"]
                )
            
            user_text = transcript_response.text
            words_data = getattr(transcript_response, "words", [])

            long_pause_detected = False
            pause_details = ""
            if words_data and len(words_data) > 1:
                for i in range(len(words_data) - 1):
                    end_current = getattr(words_data[i], "end", 0)
                    start_next = getattr(words_data[i+1], "start", 0)
                    gap = start_next - end_current
                    if gap > 1.5:
                        long_pause_detected = True
                        user_data["pause_count"] += 1
                        pause_details += f" (Phonatory block/latency of {gap:.1f}s)"

            stutter_detected = False
            stutter_details = ""
            if words_data and len(words_data) > 1:
                for i in range(len(words_data) - 1):
                    w1 = words_data[i].word.strip().lower()
                    w2 = words_data[i+1].word.strip().lower()
                    if w1 == w2 and len(w1) > 0:
                        stutter_detected = True
                        user_data["stutter_count"] += 1
                        stutter_details += f" (Syllable/word iteration loop on '{w1}')"
                        break

            fillers_found = sum(user_text.lower().count(f) for f in ["um", "uh", "like", "you know", "ah", "so"])
            user_data["filler_count"] += fillers_found
            user_data["turns_practiced"] += 1

            user_display_msg = f"*(Spoken Transcript)*: {user_text}"
            tags = []
            if long_pause_detected:
                tags.append("Phonatory block detected")
            if stutter_detected:
                tags.append("Repetition/clonic behavior detected")
            if tags:
                tag_str = ", ".join(tags)
                user_display_msg += f" *[Acoustic Telemetry: {tag_str}]*"

            user_data["messages"].append({"role": "user", "content": user_display_msg})
            with st.chat_message("user"):
                st.write(user_display_msg)

            if user_data["homework_assigned_this_session"]:
                dynamic_hw_instruction = "REMINDER: A technical intervention protocol has ALREADY been assigned this session. You are strictly forbidden from mentioning homework again."
            else:
                dynamic_hw_instruction = "You MUST assign EXACTLY ONE technical speech therapy exercise or modification technique (e.g., cancellations, pull-outs, easy onsets) targeting the identified speech error, using the exact format 'Homework Assignment: [task]'. Once given, never mention it again."

            note_content = (
                f"Clinical Telemetry Report: User audio stream analyzed. "
                f"Metrics -> Fillers: {fillers_found}, Phonatory block/pause: {long_pause_detected} {pause_details}, Repetition/Clonic event: {stutter_detected} {stutter_details}. "
                f"As a clinical Speech-Language Pathologist and technical fluency coach, you MUST maintain a rigorous, highly technical tone with zero fluff, provide a brief clinical acknowledgement instead of echoing the user, and execute your three core pillars: "
                f"1. Speech Pathology: Provide a precise technical diagnosis of the motor-speech breakdown and prescribe explicit fluency-shaping or stuttering-modification techniques (e.g., breath flow management, light articulatory contacts, pull-outs). "
                f"2. Sentence Structuring Coach: Recommend optimized syntactic phrasing to lower cognitive load and manage respiratory breath groups. "
                f"3. Speech Coach: Instruct precise pacing, co-articulation, and vocal tract tension reduction. "
                f"4. {dynamic_hw_instruction} "
                f"5. Formulate a technical, open-ended clinical inquiry to continue the session."
            )
            user_data["messages"].append({"role": "system", "content": note_content})

            response = client.chat.completions.create(model="gpt-4o-mini", messages=user_data["messages"])
            coach_reply = response.choices[0].message.content

            user_data["messages"].pop(-2)

            if "Homework Assignment:" in coach_reply:
                if not user_data["homework_assigned_this_session"]:
                    user_data["homework_assigned_this_session"] = True
                    parts = coach_reply.split("Homework Assignment:")
                    if len(parts) > 1:
                        user_data["current_homework"] = parts[1].strip()
                else:
                    coach_reply = coach_reply.replace("Homework Assignment:", "Clinical Protocol Note:")

            user_data["messages"].append({"role": "assistant", "content": coach_reply})
            with st.chat_message("assistant"):
                st.write(coach_reply)

            speech_file_path = "assistant_voice.mp3"
            voice_resp = client.audio.speech.create(model="tts-1", voice="alloy", input=coach_reply, speed=speech_speed)
            voice_resp.stream_to_file(speech_file_path)
            
            with open(speech_file_path, "rb") as f:
                user_data["latest_audio_bytes"] = f.read()
            
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            if os.path.exists(speech_file_path):
                os.remove(speech_file_path)
            
            st.rerun()

# --- SESSION EXPORT ---
st.sidebar.markdown("---")
st.sidebar.subheader("📥 Export Profile Data")
chat_export = f"# Speech Therapy Log for {current_user}\n\n" + "\n\n".join([f"**{m['role'].upper()}**: {m['content']}" for m in user_data["messages"] if m['role'] != 'system'])
st.sidebar.download_button(
    label="Download Personal Log",
    data=chat_export,
    file_name=f"{current_user}_speech_log.md",
    mime="text/markdown"
)
