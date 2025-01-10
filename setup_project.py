import os

def create_directory_structure():
    # Define the directory structure
    directories = [
        'app',
        'app/services',
        'app/utils',
        'temp_uploads'
    ]
    
    # Create directories
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        # Create __init__.py in Python package directories
        if 'app' in directory:
            with open(os.path.join(directory, '__init__.py'), 'w') as f:
                pass

    # Create all the necessary files
    files = {
        'app/__init__.py': '''from flask import Flask
from flask_cors import CORS
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)  # Enable CORS for all routes

    from app.routes import api
    app.register_blueprint(api)

    return app
''',
        'app/routes.py': '''from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from app.services.resume_analyzer import ResumeAnalyzer
from app.utils.pdf_utils import read_text_from_pdf
import os

api = Blueprint('api', __name__)
analyzer = None

@api.before_app_first_request
def initialize_analyzer():
    global analyzer
    analyzer = ResumeAnalyzer(os.getenv('GROQ_API_KEY'))

@api.route('/api/analyze', methods=['POST'])
def analyze_resume():
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file provided'}), 400
        
        resume_file = request.files['resume']
        job_description = request.form.get('jobDescription')
        
        if not job_description:
            return jsonify({'error': 'No job description provided'}), 400
        
        if resume_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if not resume_file.filename.endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        resume_text = read_text_from_pdf(resume_file)
        feedback = analyzer.analyze_match_with_groq(resume_text, job_description)
        
        return jsonify({
            'feedback': feedback,
            'filename': resume_file.filename
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
''',
        'app/services/resume_analyzer.py': '''from sentence_transformers import SentenceTransformer
from groq import Groq
from typing import List
import re

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
                            'knowledge of', 'familiar with', 'expertise in']
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
                "Include the following sections:\\n"
                "1. Key Skills Match: List the skills that align well with the job requirements\\n"
                "2. Missing Skills: Identify important skills from the job description that are not evident in the resume\\n"
                "3. Experience Alignment: Evaluate how well the candidate's experience matches the role\\n"
                "4. Improvement Suggestions: Specific recommendations for strengthening the application\\n"
                "5. Overall Rating: Score from 1-10 (10 being perfect match) with brief explanation\\n\\n"
                "Focus on concrete evidence from the resume without making assumptions about unlisted skills."
            )}
        ]
        
        try:
            response = self.groq_client.chat.completions.create(
                messages=prompt,
                model="llama3-8b-8192"
            )
            feedback = response.choices[0].message.content
            # Estimate tokens used
            self.used_tokens += len(resume_text.split()) + len(job_description.split())
        except Exception as e:
            feedback = f"An error occurred while analyzing with Groq: {e}"
        
        return feedback
''',
        'app/utils/pdf_utils.py': '''import fitz
import os

def read_text_from_pdf(pdf_file) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_file: File object from request
        
    Returns:
        str: Extracted text from the PDF
    """
    try:
        # Save temporary file
        temp_path = os.path.join(os.getenv('UPLOAD_FOLDER'), pdf_file.filename)
        pdf_file.save(temp_path)
        
        # Extract text
        doc = fitz.open(temp_path)
        text = ""
        for page in doc:
            text += page.get_text()
        
        # Cleanup
        doc.close()
        os.remove(temp_path)
        
        return text.strip()
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")
''',
        'config.py': '''import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'temp_uploads'
''',
        'run.py': '''from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
''',
        '.env': '''GROQ_API_KEY=your_groq_api_key_here
UPLOAD_FOLDER=temp_uploads
''',
        'requirements.txt': '''flask==2.0.1
flask-cors==3.0.10
PyMuPDF==1.19.6
sentence-transformers==2.2.2
python-dotenv==0.19.0
groq==0.4.1
gunicorn==20.1.0
''',
        'render.yaml': '''services:
  - type: web
    name: resume-analyzer-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn run:app
    envVars:
      - key: GROQ_API_KEY
        sync: false
''',
        '.gitignore': '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/

# Environment Variables
.env

# IDE
.idea/
.vscode/
*.swp
*.swo

# Temporary files
temp_uploads/
'''
    }

    # Create all files
    for file_path, content in files.items():
        with open(file_path, 'w') as f:
            f.write(content)

    print("Project structure created successfully!")
    print("\nNext steps:")
    print("1. Update the GROQ_API_KEY in .env file")
    print("2. Create a virtual environment: python -m venv venv")
    print("3. Activate the virtual environment:")
    print("   - Windows: .\\venv\\Scripts\\activate")
    print("   - Unix/MacOS: source venv/bin/activate")
    print("4. Install requirements: pip install -r requirements.txt")
    print("5. Run the application: python run.py")

if __name__ == '__main__':
    create_directory_structure()