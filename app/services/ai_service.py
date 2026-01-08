"""
AI service for text generation.
"""

import os
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Default model configuration
DEFAULT_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
DEFAULT_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
DEFAULT_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '1000'))


def build_prompt(job_description: str, normalized_resume: Dict[str, Any], field_name: str = "cover_letter") -> str:
    """
    Build a prompt for AI text generation.
    
    Args:
        job_description: Job description text
        normalized_resume: Normalized resume data dictionary
        field_name: Name of the field being generated (e.g., "cover_letter", "personal_statement")
        
    Returns:
        Formatted prompt string
    """
    # Extract key resume information
    name = normalized_resume.get('name', 'Candidate')
    email = normalized_resume.get('email', '')
    phone = normalized_resume.get('phone', '')
    
    # Extract education
    education = normalized_resume.get('education', [])
    education_text = ""
    if education:
        education_text = "\n".join([
            f"- {edu.get('degree', '')} from {edu.get('institution', '')} ({edu.get('end_year', '')})"
            for edu in education[:3]  # Top 3 most recent
        ])
    
    # Extract experience
    experience = normalized_resume.get('experience', [])
    experience_text = ""
    if experience:
        experience_text = "\n".join([
            f"- {exp.get('title', '')} at {exp.get('company', '')} ({exp.get('start_year', '')}-{exp.get('end_year', 'Present')})"
            for exp in experience[:3]  # Top 3 most recent
        ])
    
    # Extract skills
    skills = normalized_resume.get('skills', [])
    skills_text = ""
    if isinstance(skills, list):
        if skills and isinstance(skills[0], dict):
            # Skills as objects with name and confidence
            skills_list = [s.get('name', '') for s in skills[:10]]
        else:
            # Skills as strings
            skills_list = skills[:10]
        skills_text = ", ".join(skills_list)
    
    # Build prompt based on field type
    if field_name.lower() in ['cover_letter', 'cover letter', 'letter']:
        prompt = f"""Write a professional cover letter for the following job application.

Job Description:
{job_description}

Candidate Information:
Name: {name}
Email: {email}
Phone: {phone}

Education:
{education_text if education_text else "Not specified"}

Work Experience:
{experience_text if experience_text else "Not specified"}

Skills:
{skills_text if skills_text else "Not specified"}

Please write a compelling cover letter that:
1. Addresses the specific requirements mentioned in the job description
2. Highlights relevant experience and skills
3. Demonstrates enthusiasm for the role
4. Is professional, concise, and well-structured
5. Is approximately 300-400 words

Cover Letter:"""
    
    elif field_name.lower() in ['personal_statement', 'personal statement', 'statement']:
        prompt = f"""Write a professional personal statement for the following job application.

Job Description:
{job_description}

Candidate Information:
Name: {name}
Email: {email}
Phone: {phone}

Education:
{education_text if education_text else "Not specified"}

Work Experience:
{experience_text if experience_text else "Not specified"}

Skills:
{skills_text if skills_text else "Not specified"}

Please write a personal statement that:
1. Explains why you are interested in this position
2. Highlights your relevant qualifications and experience
3. Demonstrates your passion and fit for the role
4. Is professional, authentic, and engaging
5. Is approximately 200-300 words

Personal Statement:"""
    
    else:
        # Generic text field generation
        prompt = f"""Generate professional text for a job application field: "{field_name}"

Job Description:
{job_description}

Candidate Information:
Name: {name}
Email: {email}
Phone: {phone}

Education:
{education_text if education_text else "Not specified"}

Work Experience:
{experience_text if experience_text else "Not specified"}

Skills:
{skills_text if skills_text else "Not specified"}

Please generate appropriate text for the "{field_name}" field that:
1. Is relevant to the job description
2. Highlights the candidate's qualifications
3. Is professional and well-written
4. Is appropriate in length for the field type

Generated Text:"""
    
    return prompt


def generate_text(
    job_description: str,
    normalized_resume: Dict[str, Any],
    field_name: str = "cover_letter",
    model: str = None,
    temperature: float = None,
    max_tokens: int = None
) -> Dict[str, Any]:
    """
    Generate text using AI.
    
    Args:
        job_description: Job description text
        normalized_resume: Normalized resume data dictionary
        field_name: Name of the field being generated
        model: AI model to use (defaults to DEFAULT_MODEL)
        temperature: Temperature for generation (defaults to DEFAULT_TEMPERATURE)
        max_tokens: Maximum tokens (defaults to DEFAULT_MAX_TOKENS)
        
    Returns:
        Dictionary with:
            - generated_text: The generated text
            - prompt: The prompt used
            - raw_response: Full API response
            - tokens_used: Number of tokens used
            - cost_estimate: Estimated cost
    """
    if not client:
        raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY environment variable.")
    
    # Use defaults if not provided
    model = model or DEFAULT_MODEL
    temperature = temperature if temperature is not None else DEFAULT_TEMPERATURE
    max_tokens = max_tokens or DEFAULT_MAX_TOKENS
    
    # Build prompt
    prompt = build_prompt(job_description, normalized_resume, field_name)
    
    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional career advisor helping candidates write compelling job application materials. Generate professional, authentic, and well-structured text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Extract generated text
        generated_text = response.choices[0].message.content.strip()
        
        # Calculate usage
        tokens_used = response.usage.total_tokens if response.usage else 0
        
        # Estimate cost (rough estimates for GPT-4 and GPT-3.5)
        cost_per_1k_tokens = {
            'gpt-4': 0.03,  # $0.03 per 1K tokens (input + output)
            'gpt-4-turbo': 0.01,
            'gpt-3.5-turbo': 0.002,
        }.get(model, 0.002)
        
        cost_estimate = (tokens_used / 1000) * cost_per_1k_tokens
        
        return {
            'generated_text': generated_text,
            'prompt': prompt,
            'raw_response': {
                'id': response.id,
                'model': response.model,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                    'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                    'total_tokens': tokens_used
                } if response.usage else None
            },
            'tokens_used': tokens_used,
            'cost_estimate': cost_estimate,
            'model_name': model
        }
        
    except Exception as e:
        raise ValueError(f"AI generation failed: {str(e)}")

