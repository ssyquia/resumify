import streamlit as st
from PyPDF2 import PdfReader
import openai
import streamlit.components.v1 as components

# Set page configuration
st.set_page_config(page_title='📝 Resume Reviewer', page_icon="📝", layout="wide")

# Retrieve the API key from Streamlit secrets
openai_api_key = st.secrets["openai"]["api_key"]
client = openai.OpenAI(api_key=openai_api_key)

# Access the Hotjar ID from secrets
hotjar_id = st.secrets["general"]["hotjar_id"]

# Custom HTML for Hotjar tracking code
tracking_code = f"""
<script>
    (function(h,o,t,j,a,r){{
        h.hj=h.hj||function(){{(h.hj.q=h.hj.q||[]).push(arguments)}};
        h._hjSettings={{hjid:{hotjar_id},hjsv:6}};
        a=o.getElementsByTagName('head')[0];
        r=o.createElement('script');r.async=1;
        r.src=t+h._hjSettings.hjid+j+h._hjSettings.hjsv;
        a.appendChild(r);
    }})(window,document,'https://static.hotjar.com/c/hotjar-','.js?sv=');
</script>
"""

# Embed the tracking code using components.html and set height to 0
components.html(tracking_code, height=0)

def get_gpt_review(data: str, key: str):    
    function_descriptions = [
        {
            "name": "evaluate_resume",
            "description": "Provide a detailed review, enhancement suggestions, and ATS optimization tips for the resume.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Ensure the candidate's name is clearly and prominently displayed on the resume."},
                    "summary": {"type": "string", "description": "Provide a compelling and concise summary highlighting the candidate's most relevant experiences and skills."},
                    "grammar_corrections": {"type": "string", "description": "Identify and suggest corrections for any grammatical errors found throughout the resume to enhance clarity and professionalism."},
                    "quantifiers": {"type": "string", "description": "Recommend adding quantifiers to achievements (e.g., numbers, percentages) to provide measurable results and impacts of the candidate's work."},
                    "ats_optimization": {"type": "string", "description": "Provide suggestions to optimize the resume for Applicant Tracking Systems (ATS), ensuring it includes relevant keywords and follows ATS-friendly formatting."},
                    "company_fit": {"type": "string", "description": "Evaluate how well the candidate fits with the company's culture and values, assessing alignment with the company's mission and vision."},
                    "line_suggestions": {"type": "string", "description": "Offer specific suggestions for improving individual lines in the resume to make them more impactful and relevant to the job role."},
                    "contact_info": {"type": "string", "description": "Verify the presence and accuracy of contact information, including email, phone number, and LinkedIn profile."},
                    "job_titles_dates": {"type": "string", "description": "Check the clarity and consistency of job titles and dates of employment, ensuring they are formatted correctly and easy to understand."},
                    "skills_relevance": {"type": "string", "description": "Assess the relevance of listed technical and soft skills to the desired role, highlighting those that are most pertinent."},
                    "education_certifications": {"type": "string", "description": "Verify the accuracy and relevance of educational background and certifications, highlighting those that are most relevant to the job."},
                    "projects_impact": {"type": "string", "description": "Ensure the outcomes and impacts of projects are clearly stated, demonstrating the candidate's hands-on experience and contributions."},
                    "achievements_impact": {"type": "string", "description": "Highlight significant achievements and their impacts, making sure they are presented in a way that emphasizes their importance."},
                    "action_verbs": {"type": "string", "description": "Suggest the use of strong action verbs to describe responsibilities and achievements, making the resume more dynamic and engaging."},
                    "professional_tone": {"type": "string", "description": "Ensure the language used in the resume is professional and appropriate for the industry, maintaining a polished and respectful tone."},
                    "technical_jargon": {"type": "string", "description": "Ensure technical jargon is used appropriately and is understandable, showcasing the candidate's expertise without overwhelming the reader."},
                    "redundancies": {"type": "string", "description": "Identify and suggest removal of redundant information to streamline the resume and maintain conciseness."},
                    "consistency": {"type": "string", "description": "Ensure consistency in formatting and verb tense throughout the resume, maintaining a uniform and professional appearance."},
                    "additional_data_request": {"type": "string", "description": "Request additional data if necessary to provide a more complete and thorough review of the resume."},
                    "overall_score": {"type": "number", "description": "Provide an overall score for the resume based on all criteria, giving a quick overview of its quality and effectiveness."}
                },
                "required": [
                    "name", "summary", "grammar_corrections", "quantifiers", "ats_optimization",
                    "company_fit", "line_suggestions", "contact_info", "job_titles_dates", "skills_relevance",
                    "education_certifications", "projects_impact", "achievements_impact", "action_verbs",
                    "professional_tone", "technical_jargon", "redundancies", "consistency", "additional_data_request",
                    "overall_score"
                ]
            }
        }
    ]

    messages = [{"role": "user", "content": data}]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        functions=function_descriptions,
        function_call="auto"
    )

    return response

def analyze_resume_data(data: str, key: str) -> dict | None:
    gpt_response = get_gpt_review(data, key)
    response_message = gpt_response.choices[0].message
    function_call = response_message.function_call
    if not function_call:
        print("Error: No function call found in the response.")
        return None
    arguments = function_call.arguments
    if isinstance(arguments, str):
        import json
        try:
            arguments_dict = json.loads(arguments)
            review_text = arguments_dict.pop('review_text', '')
            arguments_dict['review_text'] = review_text
            return arguments_dict
        except json.JSONDecodeError as e:
            print("Error: Cannot convert to a JSON object.")
            print(e)
    return None
# Streamlit setup
st.title("💬 Resumify")
st.caption("🚀 A chatbot powered by OpenAI to provide suggestions for improving and optimizing resumes.")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Please attach your resume to the input below then ask a question."}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

uploaded_files = st.file_uploader("Upload a PDF resume", type=["pdf"], accept_multiple_files=False)

if uploaded_files:
    pdf_file = PdfReader(uploaded_files)
    pdf_text = ""
    for page in pdf_file.pages:
        pdf_text += page.extract_text() + "\n"
    st.session_state["messages"].append({"role": "system", "content": "[Attached PDF: " + uploaded_files.name + "]"})

if "first_input" not in st.session_state:
    st.session_state["first_input"] = True

if "user_id" not in st.session_state:
    import uuid
    st.session_state["user_id"] = str(uuid.uuid4())

if prompt := st.chat_input():
    user_message = {"role": "user", "content": prompt}
    if uploaded_files:
        user_message["content"] += "\n\n[Attached PDF: " + uploaded_files.name + "]"

    st.session_state.messages.append(user_message)
    st.chat_message("user").write(user_message["content"])

    try:
        if uploaded_files and st.session_state["first_input"]:
            # Full suite of advice for the first input
            resume_data = analyze_resume_data(pdf_text, openai_api_key)
            if resume_data:
                # ... existing code for full review ...
                st.session_state["first_input"] = False
            else:
                st.error("Could not extract resume data.")
        else:
            # Use base ChatGPT model for subsequent questions
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "You are an AI assistant specializing in resume advice. Provide concise and helpful answers to questions about resumes, job applications, and career development."}] + st.session_state["messages"]
            )
            msg = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.chat_message("assistant").write(msg)
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")

    try:
        if uploaded_files:
            resume_data = analyze_resume_data(pdf_text, openai_api_key)
            if resume_data:
                review_text = resume_data.get('review_text', 'No detailed review available.')

                # Generate another prompt for improvement suggestions
                improvement_prompt = f"""You are a professional HR recruiter with expertise in crafting top-tier resumes for tech companies, business roles, product management, and other industries. Your goal is to transform the following resume into the best version possible. Provide a comprehensive review, addressing all relevant aspects such as grammar, quantifiers, ATS optimization, company fit, and impactful line-specific suggestions. Ensure to quote specific parts from the resume being referred to for suggestions, avoiding comments on names and dates. Your review should be free-flowing and narrative in style, offering actionable advice and strategies to significantly enhance the resume's effectiveness. When giving suggestions, make sure not to make up any information or data, just stick to the facts. Conclude with an overall score that reflects the resume's quality and readiness for competitive job markets.
                Resume Review: {review_text}
                Resume Text: {pdf_text}"""

                improvement_messages = [
                    {"role": "user", "content": improvement_prompt}
                ]

                improvement_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=improvement_messages
                )

                improvement_suggestions = improvement_response.choices[0].message.content

                msg = f"{review_text.strip()}\n\n**Suggestions for Improvement:**\n{improvement_suggestions.strip()}"
                st.session_state.messages.append({"role": "assistant", "content": msg})
                st.chat_message("assistant").write(msg)
            else:
                st.error("Could not extract resume data.")
        else:
            response = client.chat_completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "You should assist users in crafting, refining, and formatting their resumes by providing personalized feedback and suggestions. You should guide users through each section, ensuring relevant information is highlighted and presented effectively. Additionally, you should offer industry-specific advice and examples to help users tailor their resumes to specific job roles. Two column resume's are auful, never reccomend one, and always discourage them, the same goes for any reume with color. These resumes should be fully professional and be optimized for ATS. "}] + st.session_state["messages"]
            )
            msg = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.chat_message("assistant").write(msg)
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")