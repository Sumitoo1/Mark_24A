import streamlit as st
import requests
import pdfplumber
import re
from concurrent.futures import ThreadPoolExecutor
import time
from datetime import datetime
from urllib.parse import quote

# ========== BACKGROUND IMAGE ==========
BACKGROUND_IMAGE = "https://thumbs.dreamstime.com/b/yellow-gradient-plain-background-yellow-gradient-plain-background-image-layering-text-image-125910746.jpg"

# ========== API CONFIGURATIONS ==========
API_KEYS = {
    "ADZUNA_ID": "cae04333",
    "ADZUNA_KEY": "6e9e2ec6062f2d38ba0c3900b2039662",
    "JOOBLE_KEY": "14195947-d5b9-482f-92a5-812b9c9e330b",
    "REMOTIVE_KEY": None
}

# ========== SKILLS DATABASE ==========
COMMON_SKILLS = [
    "Python", "Java", "JavaScript", "SQL", "NoSQL", "Machine Learning",
    "Data Science", "React", "Angular", "Vue", "Node.js", "AWS",
    "Azure", "Google Cloud", "Docker", "Kubernetes", "TensorFlow",
    "PyTorch", "Flask", "Django", "Spring", "Git", "CI/CD", "REST API",
    "GraphQL", "TypeScript", "HTML", "CSS", "SASS", "Redux", "MongoDB",
    "PostgreSQL", "MySQL", "Firebase", "Linux", "Bash", "Pandas",
    "NumPy", "Scikit-learn", "Keras", "Spark", "Hadoop", "Tableau",
    "Power BI", "Excel", "Agile", "Scrum", "JIRA", "Jenkins", "Ansible"
]


# ========== RESUME PARSING ==========
def extract_text_from_pdf(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())


def extract_skills(resume_text):
    if not resume_text: return []
    normalized_text = resume_text.lower()
    return list(set(skill for skill in COMMON_SKILLS
                    if re.search(r'\b' + re.escape(skill.lower()) + r'\b', normalized_text)))


# ========== JOB FETCHING ==========
def fetch_from_adzuna(skills):
    if not skills: return {"Adzuna": []}
    try:
        response = requests.get(
            "https://api.adzuna.com/v1/api/jobs/in/search/1",
            params={
                "app_id": API_KEYS["ADZUNA_ID"],
                "app_key": API_KEYS["ADZUNA_KEY"],
                "what": quote(skills[0]),
                "sort_by": "relevance",
                "results_per_page": "10"
            },
            timeout=10
        )
        return {"Adzuna": response.json().get("results", [])}
    except:
        return {"Adzuna": []}


def fetch_from_remotive(skills):
    try:
        response = requests.get("https://remotive.com/api/remote-jobs", timeout=10)
        jobs = response.json().get("jobs", [])
        return {"Remotive": [job for job in jobs if any(
            skill.lower() in f"{job.get('title', '')} {job.get('description', '')}".lower()
            for skill in skills)]}
    except:
        return {"Remotive": []}


def fetch_from_jooble(skills):
    try:
        response = requests.post(
            f"https://jooble.org/api/{API_KEYS['JOOBLE_KEY']}",
            json={"keywords": " ".join(skills[:3]), "location": "India"},
            timeout=10
        )
        return {"Jooble": response.json().get("jobs", [])}
    except:
        return {"Jooble": []}


def fetch_all_jobs(skills):
    with ThreadPoolExecutor() as executor:
        return {api: jobs.get(api, [])
                for api, jobs in zip(["Adzuna", "Remotive", "Jooble"],
                                     executor.map(lambda f: f(skills),
                                                  [fetch_from_adzuna, fetch_from_remotive, fetch_from_jooble]))}


# ========== ENHANCED UI COMPONENTS ==========
def display_job_card(job):
    title = job.get("title", "Job Title")
    company = (job.get("company", {}).get("display_name", "Company")
               if isinstance(job.get("company"), dict) else job.get("company", "Company"))
    location = (job.get("location", {}).get("display_name", "Location")
                if isinstance(job.get("location"), dict) else job.get("location", "Location"))
    url = job.get("redirect_url") or job.get("url") or job.get("link") or "#"

    st.markdown(f"""
    <div style="
        padding: 16px;
        margin: 12px 0;
        background: rgba(255,255,255,0.93);
        border-radius: 8px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.1);
        border-left: 4px solid #0a66c2;
    ">
        <h3 style="color: #0a66c2; margin-bottom: 8px; font-size: 18px;">{title}</h3>
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="#666" style="margin-right: 8px;">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
            </svg>
            <span style="color: #666;">{location}</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 12px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="#666" style="margin-right: 8px;">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
            </svg>
            <span style="font-weight: 600; color: #333;">{company}</span>
        </div>
        <a href="{url}" target="_blank" style="
            background: #0a66c2;
            color: white;
            padding: 8px 16px;
            text-decoration: none;
            border-radius: 20px;
            font-size: 14px;
            display: inline-block;
            text-align: center;
            width: 100%;
            box-sizing: border-box;
        ">
            Apply Now
        </a>
    </div>
    """, unsafe_allow_html=True)


def main():
    # Page configuration
    st.set_page_config(
        page_title="CareerConnect Pro",
        page_icon="💼",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    # Background image styling
    st.markdown(f"""
    <style>
        .stApp {{
            background-image: url("{BACKGROUND_IMAGE}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        /* Main content container */
        .main-content {{
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 16px;
            padding: 2rem;
            margin: 2rem auto;
            max-width: 800px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}

        /* Title styling */
        .app-title {{
            color: #0a66c2;
            font-size: 2.5rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 1.5rem;
        }}

        /* Skill chips */
        .skill-chip {{
            background-color: rgba(10, 102, 194, 0.1);
            color: #0a66c2;
            padding: 6px 12px;
            border-radius: 16px;
            display: inline-block;
            margin: 4px;
            font-size: 14px;
        }}

        /* Mobile responsiveness */
        @media (max-width: 768px) {{
            .main-content {{
                padding: 1.5rem;
                margin: 1rem;
                border-radius: 12px;
            }}
            .app-title {{
                font-size: 2rem;
            }}
        }}
    </style>
    """, unsafe_allow_html=True)

    # Main content container
    st.markdown('<div class="main-content">', unsafe_allow_html=True)

    # Clean title only (removed subtitle)
    st.markdown('<div class="app-title">CareerConnect Pro</div>', unsafe_allow_html=True)

    # Upload section - now directly under the title
    uploaded_file = st.file_uploader("Upload your resume (PDF) to find matching jobs", type=["pdf"])

    if uploaded_file:
        with st.spinner("Analyzing your resume..."):
            resume_text = extract_text_from_pdf(uploaded_file)
            skills = extract_skills(resume_text)

            if skills:
                # Skills display
                st.markdown("### Your Professional Skills")
                st.markdown("".join(
                    f'<span class="skill-chip">{skill}</span>'
                    for skill in skills
                ), unsafe_allow_html=True)

                # Job recommendations
                st.markdown("---")
                st.markdown("### Recommended Jobs For You")

                with st.spinner("Finding the best opportunities..."):
                    api_jobs = fetch_all_jobs(skills)

                    if any(jobs for jobs in api_jobs.values()):
                        for jobs in api_jobs.values():
                            for job in jobs[:10]:
                                display_job_card(job)
                    else:
                        st.warning("No matching jobs found. Try adjusting your resume or skills.")

    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()