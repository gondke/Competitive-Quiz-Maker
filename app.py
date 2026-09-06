import streamlit as st
import pandas as pd
import qrcode
import json
import os
from io import BytesIO

# Page configuration
st.set_page_config(page_title="National Testing Portal - Mock Exam", layout="wide")

# ---------------------------------------------------------
# FILE STORAGE FOR PERMANENT QUESTION BANK
# ---------------------------------------------------------
DB_FILE = "question_bank.json"

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

# ---------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------
if "question_bank" not in st.session_state:
    st.session_state.question_bank = load_question_bank()

if "editing_idx" not in st.session_state:
    st.session_state.editing_idx = None

if "current_quiz" not in st.session_state:
    st.session_state.current_quiz = []

if "quiz_active" not in st.session_state:
    st.session_state.quiz_active = False

if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

if "user_responses" not in st.session_state:
    st.session_state.user_responses = {}

if "question_states" not in st.session_state:
    st.session_state.question_states = {}  # 'not_visited', 'not_answered', 'answered', 'review'

if "marking_scheme" not in st.session_state:
    st.session_state.marking_scheme = {"MCQ": (1.0, -0.33), "MSQ": (1.0, 0.0), "NAT": (1.0, 0.0)}

if "cutoff_score" not in st.session_state:
    st.session_state.cutoff_score = 1.0

if "session_code" not in st.session_state:
    st.session_state.session_code = "GATE-2026-TEST"

# Function to generate QR Image bytes
def generate_qr(data_str):
    qr = qrcode.make(data_str)
    buf = BytesIO()
    qr.save(buf)
    return buf.getvalue()

# ---------------------------------------------------------
# CSS FOR EXAM PALETTE & UI REPLICATION
# ---------------------------------------------------------
st.markdown("""
    <style>
    .exam-header { background-color: #003366; color: white; padding: 10px; font-size: 20px; font-weight: bold; }
    .status-btn { width: 100%; border: none; padding: 8px; margin: 2px; color: white; font-weight: bold; border-radius: 4px; }
    .btn-answered { background-color: #28a745; }
    .btn-not-answered { background-color: #dc3545; }
    .btn-not-visited { background-color: #e0e0e0; color: black; }
    .btn-review { background-color: #6f42c1; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# NAVIGATION & MODE SELECTION
# ---------------------------------------------------------
sidebar_mode = st.sidebar.radio("Select Portal Role", ["Admin / Instructor Portal", "Student Exam Portal"])

# =========================================================
# ADMIN / INSTRUCTOR PORTAL
# =========================================================
if sidebar_mode == "Admin / Instructor Portal":
    st.title("Instructor Control Center")
    tab1, tab2, tab3 = st.tabs(["Question Bank Management", "Quiz Configuration", "Session & QR Code"])

    # -----------------------------------------------------
    # TAB 1: QUESTION BANK MANAGEMENT (ADD / EDIT)
    # -----------------------------------------------------
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

    # -----------------------------------------------------
    # TAB 2: QUIZ CONFIGURATION & MARKING SCHEME
    # -----------------------------------------------------
    with tab2:
        st.subheader("Configure Exam Rules & Marking Scheme")
        
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

        if st.button("Generate Quiz from Ticked Questions"):
            selected_qs = [q for q in st.session_state.question_bank if q["selected"]]
            if not selected_qs:
                st.warning("Please select at least one question from the Question Bank tab using checkboxes.")
            else:
                st.session_state.current_quiz = selected_qs
                st.session_state.question_states = {i: "not_visited" for i in range(len(selected_qs))}
                st.session_state.question_states[0] = "not_answered"
                st.session_state.user_responses = {}
                st.session_state.quiz_submitted = False
                st.session_state.quiz_active = False
                st.success(f"Quiz successfully generated with {len(selected_qs)} questions!")

        # Display generated Quiz Join Info right away if quiz is available
        if st.session_state.current_quiz:
            st.divider()
            st.subheader("📢 Active Quiz Access Information")
            st.info("Give students the session code or display this QR code to let them join:")
            col_info, col_qr = st.columns([2, 1])
            with col_info:
                st.metric("Exam Session Code", st.session_state.session_code)
                st.write(f"**Total Questions Selected:** {len(st.session_state.current_quiz)}")
            with col_qr:
                qr_bytes = generate_qr(st.session_state.session_code)
                st.image(qr_bytes, caption=f"Scan to Join Code: {st.session_state.session_code}", width=180)

    # -----------------------------------------------------
    # TAB 3: SESSION CODE & QR GENERATION
    # -----------------------------------------------------
    with tab3:
        st.subheader("Student Joining Info Settings")
        st.session_state.session_code = st.text_input("Session Code", value=st.session_state.session_code)
        
        qr_bytes = generate_qr(st.session_state.session_code)
        st.image(qr_bytes, caption=f"Scan QR Code to retrieve Session Code: {st.session_state.session_code}", width=200)

# =========================================================
# STUDENT EXAM PORTAL
# =========================================================
else:
    st.markdown('<div class="exam-header">IIT JAM / GATE / CSIR NET Online Examination Portal</div>', unsafe_allow_html=True)

    if not st.session_state.current_quiz:
        st.warning("No active quiz available. Please ask the instructor to configure and publish a quiz.")
    elif st.session_state.quiz_submitted:
        # -------------------------------------------------
        # RESULT ANALYSIS PAGE
        # -------------------------------------------------
        st.title("Final Exam Performance & Analysis")
        
        total_score = 0.0
        max_possible = 0.0
        details = []

        for idx, q in enumerate(st.session_state.current_quiz):
            q_type = q["type"]
            pos_m, neg_m = st.session_state.marking_scheme[q_type]
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

        if total_score >= st.session_state.cutoff_score:
            st.balloons()
            st.success(f"🎉 Congratulations! You cleared the exam cutoff score of {st.session_state.cutoff_score:.2f} marks!")
        else:
            st.error(f"You missed the cutoff score of {st.session_state.cutoff_score:.2f} marks. Better luck next time!")

        st.write("### Detailed Question Analysis")
        st.dataframe(pd.DataFrame(details), use_container_width=True)

    elif not st.session_state.quiz_active:
        # -------------------------------------------------
        # LOGIN / SESSION VERIFICATION
        # -------------------------------------------------
        st.subheader("Enter Details to Start Test")
        input_code = st.text_input("Enter Session Code or Code Scanned from QR:")
        candidate_name = st.text_input("Candidate Name:")
        
        if st.button("Start Examination"):
            if input_code.strip() == st.session_state.session_code and candidate_name.strip():
                st.session_state.quiz_active = True
                st.rerun()
            else:
                st.error("Invalid Session Code or Candidate Name.")
    else:
        # -------------------------------------------------
        # LIVE EXAM INTERFACE (GATE/JAM PALETTE)
        # -------------------------------------------------
        if "curr_idx" not in st.session_state:
            st.session_state.curr_idx = 0

        curr_q = st.session_state.current_quiz[st.session_state.curr_idx]

        col_main, col_palette = st.columns([3, 1])

        # Question Palette Panel (Right Side)
        with col_palette:
            st.subheader("Question Palette")
            
            # Palette grid
            grid_cols = st.columns(4)
            for i in range(len(st.session_state.current_quiz)):
                col_i = grid_cols[i % 4]
                state = st.session_state.question_states.get(i, "not_visited")
                
                label = f"{i+1}"
                if state == "answered":
                    btn_type = "primary"
                elif state == "review":
                    btn_type = "secondary"
                else:
                    btn_type = "secondary"

                if col_i.button(label, key=f"pal_{i}", use_container_width=True):
                    st.session_state.curr_idx = i
                    if st.session_state.question_states[i] == "not_visited":
                        st.session_state.question_states[i] = "not_answered"
                    st.rerun()

            st.divider()
            if st.button("Submit Exam Final", type="primary", use_container_width=True):
                st.session_state.quiz_submitted = True
                st.rerun()

        # Question Content Panel (Left Side)
        with col_main:
            st.markdown(f"### Question No. {st.session_state.curr_idx + 1} ({curr_q['type']})")
            st.markdown(f"**{curr_q['text']}**")
            st.divider()

            q_idx = st.session_state.curr_idx
            existing_ans = st.session_state.user_responses.get(q_idx, None)

            # Input controls based on question type
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

            # Navigation buttons
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
