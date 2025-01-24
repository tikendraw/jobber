from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from src.llm_base import LLMBase

from .resume_maker.models import FullCVModel


class ResumeGenerator(LLMBase):
    def __init__(self, model_list: list[str], requests_per_minute: int = 15):
        super().__init__(model_list, requests_per_minute)
        
        # Load resume templates
        self.templates = {
            'sb2nov': self._load_template('./resume_maker/template_sb2nov_CV.yaml'),
            'engineeringresumes': self._load_template('./resume_maker/template_engineeringresumes.yaml')
        }

        self.prompt_template = """
You are an expert resume writer with deep knowledge of creating professional resumes. Your task is to generate a resume based on the provided information and job description.

User Information:
{user_info}

Target Job Description:
{job_description}

Additional Instructions:
{instructions}

Guidelines:
1. Format the resume to highlight relevant skills and experiences for the target role
2. Use strong action verbs and quantifiable achievements
3. Customize content to align with job requirements
4. Maintain professional tone and formatting
5. Include only the most relevant and impressive information
6. Quantify achievements where possible (%, numbers, metrics)
7. Use keywords from the job description naturally
8. Keep entries concise but impactful
9. Keep Important Sections on top (Sequence Matters)

Template Style: {template_style}

IMPORTANT: Return response in JSON format that exactly matches this structure:
{json_schema}

Focus on presenting the user's background in the most compelling way for this specific role.
"""

    def _load_template(self, template_name: str) -> dict:
        """Load a YAML template file"""
        template_path = Path(__file__).parent / template_name
        with open(template_path) as f:
            return yaml.safe_load(f)

    def _format_prompt(self, 
                      user_info: str,
                      job_description: str,
                      instructions: str,
                      template_style: str) -> str:
        """Format the prompt with provided information"""
        # Get JSON schema for the expected response format
        json_schema = FullCVModel.model_json_schema()
        
        return self.prompt_template.format(
            user_info=user_info,
            job_description=job_description,
            instructions=instructions,
            template_style=template_style,
            json_schema=json_schema
        )

    async def _process_response(self, 
                              response: Any, 
                              template_style: str, 
                              output_file: Optional[Path] = None) -> FullCVModel:
        """Process LLM response into YAML resume"""
        try:
            # Parse JSON response into Pydantic model
            resume_data = response.choices[0].message.content
            resume_yaml = FullCVModel.model_validate_json(resume_data)
            
            # Validate against template structure
            if not self._validate_resume_structure(resume_yaml, template_style):
                raise ValueError("Generated resume does not match template structure")
            
            # Save to file if requested
            if output_file:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, 'w') as f:
                    yaml.dump(resume_yaml.model_dump(), f, sort_keys=False, allow_unicode=True)
            
            return resume_yaml

        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {str(e)}")

    def _validate_resume_structure(self, resume_yaml: FullCVModel, template_style: str) -> bool:
        """Validate the generated resume against the template structure"""
        template = self.templates[template_style]
        
        # Get required sections from template
        template_sections = template['cv']['sections'].keys()
        resume_sections = resume_yaml.cv.sections.keys()
        
        # Ensure all template sections are present
        return all(section in template_sections for section in resume_sections)

    async def generate_resume(self,
                            user_info: str,
                            job_description: str,
                            template_style: str = 'sb2nov',
                            additional_instructions: str = "",
                            output_file: Optional[Path] = None) -> FullCVModel:
        """Generate a resume asynchronously"""
        if template_style not in self.templates:
            raise ValueError(f"Template style must be one of: {list(self.templates.keys())}")

        prompt = self._format_prompt(
            user_info=user_info,
            job_description=job_description,
            instructions=additional_instructions,
            template_style=template_style
        )

        return await self._execute_with_fallback(
            prompt=prompt,
            template_style=template_style,
            output_file=output_file,
            response_format={"type": "json_object"}  # Enforce JSON response
        )

    def generate_resume_sync(self, *args, **kwargs) -> FullCVModel:
        """Synchronous version of resume generation"""
        return self.execute_sync(*args, **kwargs) 