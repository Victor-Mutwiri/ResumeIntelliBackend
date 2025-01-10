from sentence_transformers import SentenceTransformer
from groq import Groq
from typing import List
import re
import logging

class ResumeAnalyzer:
    """
    A class to analyze the match between a resume and job description.
    """
    def __init__(self, groq_api_key):
        self.groq_client = Groq(api_key=groq_api_key)
        self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        self.max_token_limit = 15000
        self.used_tokens = 0

    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text using simple keyword matching."""
        skill_indicators = ['proficient in', 'experience with', 'skilled in', 
                            'knowledge of', 'familiar with', 'expertise in',
                            'qualifications', 'skills', 'abilities']
        skills = set()
        sentences = text.lower().split('.')
        
        for sentence in sentences:
            for indicator in skill_indicators:
                if indicator in sentence:
                    parts = sentence.split(indicator)
                    if len(parts) > 1:
                        potential_skills = re.split(r'[,;&]', parts[1])
                        skills.update(skill.strip() for skill in potential_skills if skill.strip())
        
        return list(skills)


    def analyze_match_with_groq(self, resume_text: str, job_description: str) -> str:
        """
        Analyze how well a resume matches a job description using Groq.
        """
        if self.used_tokens >= self.max_token_limit:
            return "Token limit reached. Please try again later."
        
        prompt = [
            {"role": "system", "content": "You are a career coach assessing a resume against a job description."},
            {"role": "user", "content": f"Job Description: {job_description}"},
            {"role": "user", "content": f"Resume: {resume_text}"},
            {"role": "user", "content": (
                "Please provide a detailed analysis of how well this resume matches the job description. "
                "Focus on concrete evidence from the resume without making assumptions about unlisted skills."
                "Include the following sections:\n"
                "Key Skills Match: List the skills that align well with the job requirements\n"
                "Missing Skills: Identify important skills from the job description that are not evident in the resume\n"
                "Experience Alignment: Evaluate how well the candidate's experience matches the role\n"
                "Improvement Suggestions: Specific recommendations for strengthening the application\n"
                "Overall Rating: Score from 1-10 (10 being perfect match) with brief explanation\n\n"
            )}
        ]
        
        try:
            response = self.groq_client.chat.completions.create(
                messages=prompt,
                model="llama3-70b-8192"
            )
            feedback = response.choices[0].message.content
            # Estimate tokens used
            self.used_tokens += len(resume_text.split()) + len(job_description.split())
        except Exception as e:
            feedback = f"An error occurred while analyzing with Groq: {e}"
        
        return feedback
 
 
    def generate_custom_resume_logic(self, resume_text: str, job_description: str) -> str:
        """
        Generate a custom resume by incorporating job description details.
        
        STRICT TEMPLATE COMPLIANCE IS MANDATORY
        """
        
        template_example = '''
        PROFESSIONAL SUMMARY
        3-4 sentences strategic overview highlighting top qualifications and directly addressing job requirements.

        KEY SKILLS
        - Technical skills matching job description
        - Soft skills and additional competencies
        - Prioritize skills from job posting

        PROFESSIONAL EXPERIENCE
        **Company Name** | *Job Title* (***Employment Dates***)
        - Achievement-focused bullet point with quantifiable result
        - Another metric-driven accomplishment
        - Demonstrates impact using strong action verbs

        [Repeat for each professional experience]

        EDUCATION
        University Name
        **Degree** | *Graduation Period*
        - Relevant academic achievements or honors

        ADDITIONAL INFORMATION
        LANGUAGES
        - Language - proficiencies

        CERTIFICATIONS
        - Professional certifications

        OPTIONAL SECTIONS
        - Volunteer work
        - Additional achievements
        '''
        # Example prompt for a language model
        prompt = (
        f"TEMPLATE REFERENCE:\n{template_example}\n\n"
        f"User Resume:\n{resume_text}\n\n"
        f"Job Description:\n{job_description}\n\n"
        "Resume Writing Instructions:\n"
        "You are an expert resume writer specializing in creating ATS-optimized, job-specific resumes by STRICTLY following the template provided. "
        "Your task is to craft a strategic, compelling resume that positions the candidate as the ideal match for the role.\n"
        "You  should start from the Summary section as the user will handle adding their own information to the resume"
        "STRICT FORMATTING RULES:\n"
        "1. Section Headings:\n"
        "   - ALL UPPERCASE\n"
        "   - NO BOLDING OF SECTION TITLES\n"
        "   - Consistent spacing before and after sections\n"
        
        "2. Professional Summary:\n"
        "   - Craft a 3-4 sentence strategic overview\n"
        "   - Highlight top 2-3 most relevant qualifications\n"
        "   - Directly address key requirements from the job description\n"
        "   - Use powerful, action-oriented language\n"
        "   - Emphasize unique value proposition\n"
        
        "3. Key Skills Section:\n"
        "   - Extract skills directly matching job description keywords\n"
        "   - Include technical skills, programming languages, tools\n"
        "   - Balance hard skills and soft skills\n"
        "   - Prioritize skills explicitly mentioned in job posting\n"
        
        "4. Professional Experience Format:\n"
        
        "   - CONSISTENT FORMAT: Company Name | Job Title (Employment Dates)\n"
        "   - 3-5 achievement-focused bullet points per role with quantifiable results even if not mentioned in the resume\n"
        "   - Quantify achievements wherever possible even if not mentioned in the resume eg 'reduced costs by 15% '\n"
        "   - Use strong action verbs: 'Developed', 'Implemented', 'Led', 'Optimized'\n"
        "   - Demonstrate impact through metrics and outcomes using numbers\n"
        "   - Align experience bullets with job description requirements and add more details if not mentioned in the resume where possible\n"
        
        "5. Education Section:\n"
        "   - Degree, Major, University, Graduation Year\n"
        "   - Include relevant academic achievements or honors\n"
        "   - List certifications or ongoing professional development\n"
        
        "6. Additional Information:\n"
        "   - Languages\n"
        "   - Professional certifications\n"
        "   - Relevant soft skills\n"
        "   - Volunteer work or significant achievements\n"
        
        "7. Typography Rules:\n"
        "   - Minimal use of bolding\n"
        "   - ONLY bold: Company Names in Experience\n"
        "   - No bolding of name or section headers\n"
        "   - Maintain clean, professional appearance\n"
        
        "Resume Optimization Principles:\n"
        "- Prioritize relevance to the specific job description\n"
        "- Use keywords from the job posting naturally\n"
        "- Maintain professional tone and concise language\n"
        "- Ensure ATS compatibility\n"
        "- Highlight transferable skills\n"
        "- Showcase potential for growth and impact\n"
        
        "Constraints:\n"
        "- Do NOT fabricate experiences or skills but you can include some actionable achievements that are not mentioned in the resume in terms of numbers only where possible and make it relevant\n"
        "- Use only information from the original resume and job description but add more details if not mentioned in the resume where possible but briefly\n"
        "- Enhance and reframe existing content\n"
        "- Focus on authentic representation of candidate's capabilities\n"
        
        "Desired Outcome:\n"
        "Generate a compelling, tailored resume that positions the candidate "
        "as an exceptional match for the specific role, maximizing interview potential. Ensure the resume strictly adheres to the template provided."
        
        "CRITICAL INSTRUCTION: ABSOLUTELY MIRROR THE PROVIDED TEMPLATE FORMAT. "
        )
        
        try:
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model = "llama-3.3-70b-versatile",
                temperature=0.8,
                
            )
            custom_resume = response.choices[0].message.content
        except Exception as e:
            custom_resume = f"An error occurred while generating the custom resume: {e}"
        
        return custom_resume
 
 
    def generate_cover_letter(self, resume_text: str, job_description: str) -> str:
        """
        Generate a custom cover letter based on resume and job description.
        """
        prompt = (
            f"User Resume:\n{resume_text}\n\n"
            f"Job Description:\n{job_description}\n\n"
            "You are a professional cover letter writer. Create a custom, engaging cover letter that:\n"
            "\n1. **Introduction**:\n"
            "   - Starts with a strong, personalized opening paragraph.\n"
            "   - States the candidate's interest in the role and enthusiasm for the company.\n"
            "   - Briefly mentions how their skills align with the job.\n"
            "\n2. **Skills and Experience**:\n"
            "   - Highlights the most relevant skills, accomplishments, and experiences from the resume.\n"
            "   - Draws direct connections between the candidates background and the job requirements.\n"
            "   - Uses concrete examples of achievements that demonstrate their value to the company.\n"
            "\n3. **Company Focus**:\n"
            "   - Shows a clear understanding of the companys mission, values, or goals based on the job description.\n"
            "   - Explains how the candidate can contribute to these objectives.\n"
            "\n4. **Conclusion and Call to Action**:\n"
            "   - Ends with a short compelling call to action (e.g., expressing eagerness for an interview).\n"
            "   - Restates enthusiasm for the role and appreciation for the opportunity.\n"
            "\n**Additional Requirements**:\n"
            "   - Format professionally with proper paragraphs and spacing.\n"
            "- Keep the tone personable yet professional.\n"
            "- Limit the length to approximately 150-200 words.\n"
            "- Use only information from the provided resume and job description.\n"
            "- Avoid generic phrases; focus on tailored and specific content that demonstrates value."
        )
        
        try:
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="gemma2-9b-it",
                temperature=0.7,
            )
            cover_letter = response.choices[0].message.content
        except Exception as e:
            cover_letter = f"An error occurred while generating the cover letter: {e}"
        
        return cover_letter
