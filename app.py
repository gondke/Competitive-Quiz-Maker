import streamlit as st
import pandas as pd
import json
import os
import random

# Page configuration
st.set_page_config(page_title="National Testing Portal - Mock Exam", layout="wide")

# ---------------------------------------------------------
# FILE STORAGE FOR PERMANENT QUESTION BANK & ACTIVE QUIZ
# ---------------------------------------------------------
DB_FILE = "question_bank.json"
QUIZ_FILE = "active_quiz.json"

def load_question_bank():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_question_bank(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_active_quiz():
    if os.path.exists(QUIZ_FILE):
        try:
            with open(QUIZ_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_active_quiz(quiz_data):
    with open(QUIZ_FILE, "w", encoding="utf-8") as f:
        json.dump(quiz_data, f, indent=4)

def generate_numeric_session_code(length=6):
    return ''.join(random.choices("0123456789", k=length))

# ---------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------
if "portal_role" not in st.session_state:
    st.session_state.portal_role = None

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

if "question_bank" not in st.session_state:
    st.session_state.question_bank = load_question_bank()

active_quiz_data = load_active_quiz()

if "editing_idx" not in st.session_state:
    st.session_state.editing_idx = None

if "current_quiz" not in st.session_state:
    st.session_state.current_quiz = active_quiz_data.get("quiz", [])

if "session_code" not in st.session_state:
    # Initialize with saved numeric code or generate a new 6-digit numeric code
    saved_code = active_quiz_data.get("session_code", None)
    if saved_code and str(saved_code).isdigit():
        st.session_state.session_code = str(saved_code)
    else:
        st.session_state.session_code = generate_numeric_session_code()

if "marking_scheme" not in st.session_state:
    st.session_state.marking_scheme = active_quiz_data.get(
        "marking_scheme", {"MCQ": (1.0, -0.33), "MSQ": (1.0, 0.0), "NAT": (1.0, 0.0)}
    )

if "cutoff_score" not in st.session_state:
    st.session_state.cutoff_score = active_quiz_data.get("cutoff_score", 1.0)

if "quiz_active" not in st.session_state:
    st.session_state.quiz_active = False

if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

if "user_responses" not in st.session_state:
    st.session_state.user_responses = {}

if "question_states" not in st.session_state:
    st.session_state.question_states = {}

if "demo_idx" not in st.session_state:
    st.session_state.demo_idx = 0

# ---------------------------------------------------------
# CSS FOR EXAM PALETTE & UI REPLICATION
# ---------------------------------------------------------
st.markdown("""
    <style>
    .exam-header { background-color: #003366; color: white; padding: 12px; font-size: 22px; font-weight: bold; text-align: center; margin-bottom: 20px;}
    .status-btn { width: 100%; border: none; padding: 8px; margin: 2px; color: white; font-weight: bold; border-radius: 4px; }
    .btn-answered { background-color: #28a745; }
    .btn-not-answered { background-color: #dc3545; }
    .btn-not-visited { background-color: #e0e0e0; color: black; }
    .btn-review { background-color: #6f42c1; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# LANDING PAGE: ROLE SELECTION
# ---------------------------------------------------------
if st.session_state.portal_role is None:
    st.markdown('<div class="exam-header">National Testing Portal - Online Examination System</div>', unsafe_allow_html=True)
    st.subheader("Welcome! Please select your portal type to continue:")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("### Student Portal\nAttempt mock tests and view result analysis.")
        if st.button("Enter Student Portal", use_container_width=True, type="primary"):
            st.session_state.portal_role = "Student"
            st.rerun()
            
    with col2:
        st.warning("### Instructor / Teacher Portal\nManage question bank, publish quizzes, and view exam demo.")
        if st.button("Enter Instructor Portal", use_container_width=True):
            st.session_state.portal_role = "Teacher"
            st.rerun()

# =========================================================
# 1. STUDENT PORTAL (TEACHER PORTAL HIDDEN)
# =========================================================
elif st.session_state.portal_role == "Student":
    head_col1, head_col2 = st.columns([6, 1])
    with head_col1:
        st.markdown('<div class="exam-header">IIT JAM / GATE / CSIR NET Student Examination Portal</div>', unsafe_allow_html=True)
    with head_col2:
        if st.button("Change Portal"):
            st.session_state.portal_role = None
            st.session_state.quiz_active = False
            st.session_state.quiz_submitted = False
            st.rerun()

    latest_quiz_data = load_active_quiz()
    published_quiz = latest_quiz_data.get("quiz", [])
    valid_session_code = str(latest_quiz_data.get("session_code", st.session_state.session_code))

    if not published_quiz:
        st.warning("No active quiz available at the moment. Please ask your instructor to configure and publish a test.")
    elif st.session_state.quiz_submitted:
        st.title("Final Exam Performance & Analysis")
        
        total_score = 0.0
        max_possible = 0.0
        details = []

        active_quiz = published_quiz
        marking_scheme = latest_quiz_data.get("marking_scheme", st.session_state.marking_scheme)
        cutoff = latest_quiz_data.get("cutoff_score", st.session_state.cutoff_score)

        for idx, q in enumerate(active_quiz):
            q_type = q["type"]
            pos_m, neg_m = marking_scheme[q_type]
            max_possible += pos_m
            user_ans = st.session_state.user_responses.get(idx, None)
            score = 0.0
            status = "Unanswered"

            if user_ans is not None and user_ans != [] and user_ans != "":
                if q_type == "MCQ":
                    if user_ans == q["correct"][0]:
                        score = pos_m
                        status = "Correct"
                    else:
                        score = neg_m
                        status = "Incorrect"
                elif q_type == "MSQ":
                    if sorted(user_ans) == sorted(q["correct"]):
                        score = pos_m
                        status = "Correct"
                    else:
                        score = neg_m
                        status = "Incorrect"
                elif q_type == "NAT":
                    try:
                        if abs(float(user_ans) - float(q["correct"])) < 0.01:
                            score = pos_m
                            status = "Correct"
                        else:
                            score = neg_m
                            status = "Incorrect"
                    except ValueError:
                        status = "Invalid Input"

            total_score += score
            details.append({
                "Q. No": idx + 1,
                "Type": q_type,
                "Your Answer": str(user_ans),
                "Correct Answer": str(q["correct"]),
                "Status": status,
                "Marks Awarded": score
            })

        st.subheader(f"Total Score: {total_score:.2f} / {max_possible:.2f}")

        if total_score >= cutoff:
            st.balloons()
            st.success(f"🎉 Congratulations! You cleared the exam cutoff score of {cutoff:.2f} marks!")
        else:
            st.error(f"You missed the cutoff score of {cutoff:.2f} marks. Better luck next time!")

        st.write("### Detailed Question Analysis")
        st.dataframe(pd.DataFrame(details), use_container_width=True)

    elif not st.session_state.quiz_active:
        st.subheader("Candidate Login")
        
        input_code = st.text_input("Enter Numeric Exam Session Code:")
        candidate_name = st.text_input("Candidate Name:")
        
        if st.button("Start Examination", type="primary"):
            if input_code.strip() == valid_session_code and candidate_name.strip():
                st.session_state.current_quiz = published_quiz
                st.session_state.question_states = {i: "not_visited" for i in range(len(published_quiz))}
                st.session_state.question_states[0] = "not_answered"
                st.session_state.quiz_active = True
                st.rerun()
            else:
                st.error("Invalid Exam Session Code or Candidate Name.")
    else:
        if "curr_idx" not in st.session_state:
            st.session_state.curr_idx = 0

        curr_q = st.session_state.current_quiz[st.session_state.curr_idx]
        col_main, col_palette = st.columns([3, 1])

        with col_palette:
            st.subheader("Question Palette")
            grid_cols = st.columns(4)
            for i in range(len(st.session_state.current_quiz)):
                col_i = grid_cols[i % 4]
                state = st.session_state.question_states.get(i, "not_visited")
                label = f"{i+1}"
                
                if col_i.button(label, key=f"pal_{i}", use_container_width=True):
                    st.session_state.curr_idx = i
                    if st.session_state.question_states[i] == "not_visited":
                        st.session_state.question_states[i] = "not_answered"
                    st.rerun()

            st.divider()
            if st.button("Submit Exam Final", type="primary", use_container_width=True):
                st.session_state.quiz_submitted = True
                st.rerun()

        with col_main:
            st.markdown(f"### Question No. {st.session_state.curr_idx + 1} ({curr_q['type']})")
            st.markdown(f"**{curr_q['text']}**")
            st.divider()

            q_idx = st.session_state.curr_idx
            existing_ans = st.session_state.user_responses.get(q_idx, None)

            if curr_q["type"] == "MCQ":
                opts = curr_q["options"]
                labels = ["Option A", "Option B", "Option C", "Option D"]
                formatted_opts = [f"{lbl}: {opt}" for lbl, opt in zip(labels, opts)]
                default_idx = labels.index(existing_ans) if existing_ans in labels else None
                sel = st.radio("Choose Option:", formatted_opts, index=default_idx, key=f"radio_{q_idx}")
                selected_val = labels[formatted_opts.index(sel)] if sel else None

            elif curr_q["type"] == "MSQ":
                st.write("Select one or more correct options:")
                labels = ["Option A", "Option B", "Option C", "Option D"]
                opts = curr_q["options"]
                selected_val = existing_ans if isinstance(existing_ans, list) else []
                updated_val = []
                for lbl, opt in zip(labels, opts):
                    chk = st.checkbox(f"{lbl}: {opt}", value=(lbl in selected_val), key=f"msq_{q_idx}_{lbl}")
                    if chk:
                        updated_val.append(lbl)
                selected_val = updated_val

            elif curr_q["type"] == "NAT":
                val = existing_ans if existing_ans is not None else ""
                selected_val = st.text_input("Enter Numerical Answer:", value=str(val), key=f"nat_{q_idx}")

            st.divider()
            b1, b2, b3 = st.columns(3)
            if b1.button("Save & Next"):
                st.session_state.user_responses[q_idx] = selected_val
                st.session_state.question_states[q_idx] = "answered"
                if st.session_state.curr_idx < len(st.session_state.current_quiz) - 1:
                    st.session_state.curr_idx += 1
                st.rerun()

            if b2.button("Clear Response"):
                st.session_state.user_responses.pop(q_idx, None)
                st.session_state.question_states[q_idx] = "not_answered"
                st.rerun()

            if b3.button("Mark for Review & Next"):
                st.session_state.user_responses[q_idx] = selected_val
                st.session_state.question_states[q_idx] = "review"
                if st.session_state.curr_idx < len(st.session_state.current_quiz) - 1:
                    st.session_state.curr_idx += 1
                st.rerun()

# =========================================================
# 2. INSTRUCTOR / TEACHER PORTAL
# =========================================================
elif st.session_state.portal_role == "Teacher":
    st.sidebar.button("Switch Portal", on_click=lambda: st.session_state.update({"portal_role": None, "admin_authenticated": False}))
    
    if not st.session_state.admin_authenticated:
        st.title("Instructor Authentication")
        pin_input = st.text_input("Enter Admin PIN to access Instructor Portal:", type="password")
        if st.button("Login as Instructor"):
            if pin_input == "1234":
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Incorrect PIN. Access denied.")
    else:
        st.title("Instructor Control Center")
        tab1, tab2, tab3 = st.tabs(["Question Bank Management", "Quiz Configuration", "Quiz Demo / Preview"])

        # TAB 1: QUESTION BANK MANAGEMENT
        with tab1:
            editing = st.session_state.editing_idx is not None
            if editing:
                st.subheader(f"Edit Question #{st.session_state.editing_idx + 1}")
                q_to_edit = st.session_state.question_bank[st.session_state.editing_idx]
            else:
                st.subheader("Add New LaTeX Question")
                q_to_edit = None

            with st.form("question_form", clear_on_submit=False):
                default_type = q_to_edit["type"] if editing else "MCQ"
                type_options = ["MCQ", "MSQ", "NAT"]
                type_idx = type_options.index(default_type) if default_type in type_options else 0
                q_type = st.selectbox("Question Type", type_options, index=type_idx)
                
                default_text = q_to_edit["text"] if editing else ""
                q_text = st.text_area("Question Text (LaTeX supported, e.g., $f(x) = \\int_{0}^{x} t^2 dt$):", value=default_text)
                
                opts = []
                nat_answer = 0.0
                correct_opts = []

                if q_type in ["MCQ", "MSQ"]:
                    col1, col2 = st.columns(2)
                    def_opts = q_to_edit["options"] if editing and len(q_to_edit.get("options", [])) == 4 else ["", "", "", ""]
                    with col1:
                        opt_a = st.text_input("Option A (LaTeX allowed)", value=def_opts[0])
                        opt_b = st.text_input("Option B (LaTeX allowed)", value=def_opts[1])
                    with col2:
                        opt_c = st.text_input("Option C (LaTeX allowed)", value=def_opts[2])
                        opt_d = st.text_input("Option D (LaTeX allowed)", value=def_opts[3])
                    opts = [opt_a, opt_b, opt_c, opt_d]

                    if q_type == "MCQ":
                        default_corr = q_to_edit["correct"][0] if editing and isinstance(q_to_edit["correct"], list) and q_to_edit["correct"] else "Option A"
                        corr_options = ["Option A", "Option B", "Option C", "Option D"]
                        corr_idx = corr_options.index(default_corr) if default_corr in corr_options else 0
                        correct_opts = [st.selectbox("Correct Option", corr_options, index=corr_idx)]
                    else:
                        st.write("Select All Correct Options (MSQ):")
                        c1, c2, c3, c4 = st.columns(4)
                        correct_opts = []
                        prev_corr = q_to_edit["correct"] if editing and isinstance(q_to_edit["correct"], list) else []
                        if c1.checkbox("A", value=("Option A" in prev_corr)): correct_opts.append("Option A")
                        if c2.checkbox("B", value=("Option B" in prev_corr)): correct_opts.append("Option B")
                        if c3.checkbox("C", value=("Option C" in prev_corr)): correct_opts.append("Option C")
                        if c4.checkbox("D", value=("Option D" in prev_corr)): correct_opts.append("Option D")
                else:
                    default_nat = float(q_to_edit["correct"]) if editing and q_to_edit["correct"] is not None else 0.0
                    nat_answer = st.number_input("Numerical Correct Answer", value=default_nat, step=0.01)

                btn_label = "Update Question" if editing else "Add Question to Bank"
                submitted = st.form_submit_button(btn_label)

                if submitted and q_text.strip():
                    updated_data = {
                        "id": q_to_edit["id"] if editing else len(st.session_state.question_bank) + 1,
                        "type": q_type,
                        "text": q_text,
                        "options": opts,
                        "correct": correct_opts if q_type in ["MCQ", "MSQ"] else nat_answer,
                        "selected": q_to_edit["selected"] if editing else False
                    }
                    if editing:
                        st.session_state.question_bank[st.session_state.editing_idx] = updated_data
                        st.session_state.editing_idx = None
                        save_question_bank(st.session_state.question_bank)
                        st.success("Question updated successfully!")
                    else:
                        st.session_state.question_bank.append(updated_data)
                        save_question_bank(st.session_state.question_bank)
                        st.success("Question successfully added!")
                    st.rerun()

            if editing:
                if st.button("Cancel Edit"):
                    st.session_state.editing_idx = None
                    st.rerun()

            st.divider()
            st.subheader("Question Bank Repository")
            if st.session_state.question_bank:
                to_delete = []
                for idx, q in enumerate(st.session_state.question_bank):
                    cols = st.columns([0.5, 0.5, 6, 1, 1])
                    q["selected"] = cols[0].checkbox("", value=q["selected"], key=f"select_{idx}")
                    cols[1].write(f"**Q{idx+1} ({q['type']})**")
                    
                    with cols[2]:
                        st.write(f"**Question:** {q['text']}")
                        if q['type'] in ["MCQ", "MSQ"]:
                            labels = ["A", "B", "C", "D"]
                            for lbl, opt in zip(labels, q['options']):
                                st.write(f"- ({lbl}) {opt}")
                            st.write(f"*Correct Answer(s):* {', '.join(q['correct'])}")
                        else:
                            st.write(f"*Correct Answer:* {q['correct']}")

                    if cols[3].button("Edit", key=f"edit_{idx}"):
                        st.session_state.editing_idx = idx
                        st.rerun()

                    if cols[4].button("Delete", key=f"del_{idx}"):
                        to_delete.append(idx)

                if to_delete:
                    for idx in sorted(to_delete, reverse=True):
                        st.session_state.question_bank.pop(idx)
                        if st.session_state.editing_idx == idx:
                            st.session_state.editing_idx = None
                    save_question_bank(st.session_state.question_bank)
                    st.rerun()
            else:
                st.info("No questions added to the bank yet.")

        # TAB 2: QUIZ CONFIGURATION
        with tab2:
            st.subheader("Configure Exam Rules & Numeric Session Code")
            
            c_code1, c_code2 = st.columns([2, 1])
            with c_code1:
                st.text_input("Active Numeric Exam Session Code", value=st.session_state.session_code, disabled=True)
            with c_code2:
                st.write(" ")
                st.write(" ")
                if st.button("Generate New Numeric Code", type="secondary"):
                    new_code = generate_numeric_session_code()
                    st.session_state.session_code = new_code
                    
                    # Update active quiz persistence file if a quiz exists
                    if st.session_state.current_quiz:
                        quiz_payload = {
                            "session_code": new_code,
                            "quiz": st.session_state.current_quiz,
                            "marking_scheme": st.session_state.marking_scheme,
                            "cutoff_score": st.session_state.cutoff_score
                        }
                        save_active_quiz(quiz_payload)
                    st.rerun()

            st.divider()
            c1, c2, c3 = st.columns(3)
            with c1:
                mcq_pos = st.number_input("MCQ Correct Marks", value=1.0)
                mcq_neg = st.number_input("MCQ Negative Marks", value=-0.33)
            with c2:
                msq_pos = st.number_input("MSQ Correct Marks", value=2.0)
                msq_neg = st.number_input("MSQ Negative Marks", value=0.0)
            with c3:
                nat_pos = st.number_input("NAT Correct Marks", value=2.0)
                nat_neg = st.number_input("NAT Negative Marks", value=0.0)

            st.session_state.marking_scheme = {
                "MCQ": (mcq_pos, mcq_neg),
                "MSQ": (msq_pos, msq_neg),
                "NAT": (nat_pos, nat_neg)
            }
            st.session_state.cutoff_score = st.number_input("Pass Cutoff Score", value=5.0)

            if st.button("Generate & Publish Quiz", type="primary"):
                selected_qs = [q for q in st.session_state.question_bank if q["selected"]]
                if not selected_qs:
                    st.warning("Please select at least one question from the Question Bank tab using checkboxes.")
                else:
                    st.session_state.current_quiz = selected_qs
                    quiz_payload = {
                        "session_code": st.session_state.session_code,
                        "quiz": selected_qs,
                        "marking_scheme": st.session_state.marking_scheme,
                        "cutoff_score": st.session_state.cutoff_score
                    }
                    save_active_quiz(quiz_payload)
                    st.success(f"Quiz successfully generated and published globally with {len(selected_qs)} questions!")

            if st.session_state.current_quiz:
                st.divider()
                st.subheader("📢 Active Quiz Access Information")
                st.metric("Current Numeric Session Code", st.session_state.session_code)
                st.write(f"**Total Questions Published:** {len(st.session_state.current_quiz)}")

        # TAB 3: QUIZ DEMO / PREVIEW
        with tab3:
            st.subheader("Quiz Demo / Preview")
            demo_quiz = st.session_state.current_quiz

            if not demo_quiz:
                st.info("No active quiz configured yet. Please select questions and click 'Generate & Publish Quiz' under Quiz Configuration.")
            else:
                st.caption("This is an interactive preview mode showing how students will view the published exam interface.")
                
                demo_col_main, demo_col_palette = st.columns([3, 1])

                with demo_col_palette:
                    st.subheader("Palette Preview")
                    grid_cols = st.columns(4)
                    for i in range(len(demo_quiz)):
                        col_i = grid_cols[i % 4]
                        label = f"{i+1}"
                        if col_i.button(label, key=f"demo_pal_{i}", use_container_width=True):
                            st.session_state.demo_idx = i
                            st.rerun()

                with demo_col_main:
                    curr_demo_q = demo_quiz[st.session_state.demo_idx]
                    st.markdown(f"### Question No. {st.session_state.demo_idx + 1} ({curr_demo_q['type']})")
                    st.markdown(f"**{curr_demo_q['text']}**")
                    st.divider()

                    if curr_demo_q["type"] in ["MCQ", "MSQ"]:
                        labels = ["Option A", "Option B", "Option C", "Option D"]
                        for lbl, opt in zip(labels, curr_demo_q["options"]):
                            st.write(f"- **{lbl}:** {opt}")
                    elif curr_demo_q["type"] == "NAT":
                        st.info("Students will enter a numerical answer in a text box.")

                    st.divider()
                    st.write(f"**Correct Answer key:** `{curr_demo_q['correct']}`")

                    d_col1, d_col2 = st.columns(2)
                    if d_col1.button("Previous Question", disabled=(st.session_state.demo_idx == 0)):
                        st.session_state.demo_idx -= 1
                        st.rerun()
                    if d_col2.button("Next Question", disabled=(st.session_state.demo_idx == len(demo_quiz) - 1)):
                        st.session_state.demo_idx += 1
                        st.rerun()
