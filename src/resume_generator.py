
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Literal, Optional

import yaml
from litellm import supports_vision
from pydantic import BaseModel, validate_call

from src.llm_base import LLMBase

from .resume_maker.models import CVModel, FullCVModel, rendercv_templates


def make_unformattable(x:str):
    """Make the input string unformattable"""
    return x.replace('{', '{{').replace('}', '}}')


template_doc = Path(__file__).parent/Path('./resume_maker/resume_formatting_code_instructions.md')
template_doc = template_doc.read_text()

formatting_doc = Path(__file__).parent / Path('./resume_maker/resume_formatting_layout_instructions.md')
formatting_doc=formatting_doc.read_text()

class ResumeGenerator(LLMBase):
    def __init__(self, model_list: list[str], requests_per_minute: int = 15):
        super().__init__(model_list, requests_per_minute)
        
        # Load resume templates
        self.templates = {
            'sb2nov': self._load_template('./resume_maker/template_sb2nov.yaml'),
            'example': self._load_template('./resume_maker/example_template.yaml'),
            'full_example':self._load_template('./resume_maker/full_example_CV.yaml')
        }

        self.prompt_template = """
You are an expert resume writer with deep knowledge of creating professional resumes. Your task is to generate a resume based on the provided user information, job description and additional instructions(if any). 
The resume should be tailored to the job description and user information provided.
\n\n
User Information:
{user_info}
\n\n
Target Job Description:
{job_description}
\n\n
Resume Guidelines:
1. Tailor it in such a way that is should match the job description for better ats compatibility. 
2. Format the resume to highlight relevant skills and experiences for the target role
3. Use strong action verbs and quantifiable achievements
4. Customize content to align with job requirements
5. Maintain professional tone and formatting
6. Include only the most relevant and impressive information
7. Quantify achievements where possible (%, numbers, metrics)
8. Use keywords from the job description naturally
9. Keep entries concise but impactful
10. Keep Important Sections on top (Sequence Matters)
11. Use Sections : Education, Projects, Experience, Skills , Certifications and more that may be helpful  
12. Use 3-4 projects that are relevant to the job description with Good Details. 
\n\n
Json guidelines:
* Start with name, email, phone, and LinkedIn profile, github profile, location and a short bio
* For dates use this formats:  YYYY-MM-DD, YYYY-MM, or YYYY format
* Do not end dates with '\n'
* Only return the json schema in a json code block nothing more, no advice, no guidance or disclaimer or someothershit.pure json in a json code block.
* Adhere to Given schema, and the schema is given below. else model validation will fail.
\n\n

\n\n
Additional Instructions:
{instructions}
\n\n
IMPORTANT: Return ONLY the actual CV data in JSON format that matches this schema structure:
{json_schema}
\n\n
Example template:
{example_template}
\n\n
Example format of the response:
```json
{{ 
user content formatted as JSON that represents the resume data 
}}
```
"""
#(which mimics the structure in example template)
# \n\n
# Template Documentation:
# {template_documentation}
# * sections are dictionary with keys as section names and values as list of  dictionaries correspoding to their respective sections.

    def _load_template(self, template_name: str) -> dict:
        """Load a YAML template file"""
        template_path = Path(__file__).parent / template_name
        with open(template_path) as f:
            return yaml.safe_load(f)

    def _format_prompt(self, 
                      user_info: str,
                      job_description: str,
                      instructions: str) -> str:
        """Format the prompt with provided information"""
        # Get JSON schema for the expected response format
        json_schema = CVModel.model_json_schema()
        
        
        # json schema contains { } brackets when we format this into another string
        # there happens chaos , we need to replace { -> {{ and } -> }} , basically double them
        # so they don't get recognized as placeholders
        
        # Escape any curly braces in the schema by doubling them
        json_schema = make_unformattable(str(json_schema))
        example_template = make_unformattable(str(self.templates['example']))
        
        return self.prompt_template.format(
            user_info=user_info,
            job_description=job_description,
            instructions=instructions,
            example_template = example_template,
            json_schema=json_schema,
            # template_documentation=template_doc,
        )

    def get_dict(self, x: Optional[str]) -> dict|str:
        """
        Cleans and parses a string to a Python dictionary, removing
        leading/trailing whitespace and "```json" code blocks only from the ends.
        """
        if not x:
            return {}
        
        # Remove leading and trailing whitespace
        x = re.sub(r"^\s+|\s+$", "", x)
        
        # Remove "```json" if it's at the beginning
        x = re.sub(r"^```json", "", x)
        
        # Remove "```" if it's at the end
        x = re.sub(r"```$", "", x)
        
        # Remove leading and trailing whitespace again
        x = re.sub(r"^\s+|\s+$", "", x)

        try:
            return json.loads(x)
        except json.JSONDecodeError as e:
            print('JSON decode error:', str(e))
            return x
    async def _process_response(self, 
                              response: Any, 
                              output_class:BaseModel,
                              template_style: str='sb2nov',     
                              output_file: Path|str = None) -> FullCVModel:
        """Process LLM response into YAML resume"""
        try:
            # Parse JSON response into Pydantic model
            resume_data = response.choices[0].message.content
            parsed_data = self.get_dict(resume_data)
            
            if not isinstance(parsed_data, dict):
                raise ValueError(f"Failed to parse response as JSON: {parsed_data}")
            
            # Convert to Pydantic model which will handle date serialization
            resume_yaml = output_class.model_validate(parsed_data)
            
            # # Validate against template structure
            # if not self._validate_resume_structure(resume_yaml, template_style):
            #     raise ValueError("Generated resume does not match template structure")
            if isinstance(resume_yaml, CVModel):
                resume_yaml = FullCVModel.from_cvmodel(cv=resume_yaml.cv, theme=template_style)

            # Save to file if requested
            if output_file:
                output_file = Path(output_file) if isinstance(output_file, str) else output_file
                output_file.parent.mkdir(parents=True, exist_ok=True)
                # Use model_dump which will properly serialize dates
                yaml_data = resume_yaml.model_dump(exclude_none=True, exclude_unset=True)
                with open(output_file, 'w') as f:
                    yaml.dump(yaml_data, f, sort_keys=False, allow_unicode=True)
            
            return resume_yaml

        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {str(e)} {e.with_traceback(None)}")

    def _validate_resume_structure(self, resume_yaml: CVModel, template_style: str) -> bool:
        """Validate the generated resume against the template structure"""
        # template = self.templates[template_style]
        
        # # Get required sections from template
        # template_sections = set(template['cv']['sections'].keys())
        # resume_sections = set(resume_yaml.cv.sections.keys())
        
        # # Ensure at least one section exists
        # if not (resume_sections):
        #     return False
            
        # Allow additional sections beyond template
        return True

    async def generate_resume(self,
                            user_info: str,
                            job_description: str,
                            template_style: str = 'sb2nov',
                            additional_instructions: str = "",
                            output_file: Optional[Path] = None) -> FullCVModel:
        """Generate a resume asynchronously"""

        prompt = self._format_prompt(
            user_info=user_info,
            job_description=job_description,
            instructions=additional_instructions,
        )

        return await self._execute_with_fallback(
            prompt=prompt,
            output_file=output_file,
            response_format={"type": "json_object"},  # Enforce JSON response
            # response_format = {"type": "json_schema", "strict": True}
            output_class=CVModel,
            template_style=template_style

        )

    def generate_resume_sync(self, *args, **kwargs) -> FullCVModel:
        """Synchronous version of resume generation"""
        return self.execute_sync(*args, **kwargs) 
    


    async def analyze_and_regenerate(self,
                                   resume_images: list[str],  # paths of resume images or base64 encoded images
                                   original_resume: FullCVModel,
                                   user_info: str,
                                   job_description: str) -> FullCVModel:
        """
        Analyze resume images and regenerate if needed with improvements
        
        Args:
            resume_images: List of image paths or base64 encoded resume images
            original_resume: Original FullCVModel that was used to generate the resume
            user_info: Original user information
            job_description: Original job description
        
        Returns:
            FullCVModel: New or original resume model depending on if changes were needed
        """
        # Verify at least one model supports vision
        vision_models = [m for m in self.model_list if supports_vision(m)]
        if not vision_models:
            raise ValueError("No vision-capable models available for resume analysis")
        
        # Temporarily switch to vision models only
        original_models = self.model_list
        self.model_list = vision_models

        try:
            # Get JSON schema for the expected response format
            json_schema = FullCVModel.model_json_schema()
            json_schema = make_unformattable(str(json_schema))
            
            analysis_prompt = """
        You are an expert resume reviewer and writer. Analyze the provided resume images and suggest improvements for better formatting, content and ATS optimization.
        Current Resume Images (Base64 encoded) are provided for your analysis.
        Original Resume Data:
        {original_resume}
        Original User Information:
        {user_info}
        Target Job Description:
        {job_description}

        Please analyze the resume and provide:
        1. Visual Layout Analysis
        - Check spacing, margins, font sizes
        - Section organization and flow
        - Overall visual appeal and professional look
        
        2. Content Analysis
        - ATS compatibility
        - Keyword optimization for job description
        - Impact of achievements
        - Relevance of information
        
        3. Formatting Analysis
        - Consistency in styling
        - Proper use of sections
        - Date formats
        - Bullet point formatting
        4. Specific Recommendations
        - List exact changes needed
        - Suggest content modifications
        - Propose formatting improvements
        
        Having all that thought , rewrite the resume with the improvements.
        \n\n
        Resume Guidelines:
        1. Tailor it in such a way that is should match the job description for better ats compatibility. 
        2. Format the resume to highlight relevant skills and experiences for the target role
        3. Use strong action verbs and quantifiable achievements
        4. Customize content to align with job requirements
        5. Maintain professional tone and formatting
        6. Include only the most relevant and impressive information
        7. Quantify achievements where possible (%, numbers, metrics)
        8. Use keywords from the job description naturally
        9. Keep entries concise but impactful
        10. Keep Important Sections on top (Sequence Matters)
        11. Use Sections : Education, Projects, Experience, Skills , Certifications and more that may be helpful  
        12. Use 3-4 projects that are relevant to the job description with Good Details. 
        \n\n
        Json guidelines:
        * Start with name, email, phone, and LinkedIn profile, github profile, location and a short bio
        * For dates use this formats:  YYYY-MM-DD, YYYY-MM, or YYYY format
        * Do not end dates with '\n'
        * Only return the json schema in a json code block nothing more, no advice, no guidance or disclaimer or someothershit.pure json in a json code block.
        * Adhere to Given schema, and the schema is given below. else model validation will fail.
        \n\n
        
        \n\n
        formatting Documentation:
        {formatting_documentation}
        \n\n
        IMPORTANT: Return ONLY the actual CV data in JSON format that matches this schema structure:
        {json_schema}
        \n\n
        Example template:
        {example_template}
        \n\n
        Example format of the response:
        ```json
        {{ 
        user content formatted as JSON that represents the resume data 
        }}
        ```
        """
            # Format the analysis prompt
            formatted_prompt = analysis_prompt.format(
                original_resume=make_unformattable(str(original_resume.model_dump_json())),
                user_info=user_info,
                job_description=job_description,
                formatting_documentation=formatting_doc,
                json_schema=json_schema,
                example_template=make_unformattable(str(self.templates['full_example'])),
            )

            # Get analysis response with images
            analysis_response = await self._execute_with_fallback(
                prompt=formatted_prompt,
                image_paths=resume_images,
                output_class=FullCVModel,
                response_format={"type": "json_object"},
                temperature=0.7
            )

            return analysis_response
        finally:
            # Restore original model list
            self.model_list = original_models



@validate_call
async def make_resume(user_info:str, job_description:str, model_list:list[str], output_file:Path=None, requests_per_minute:int=15,):
    rm = ResumeGenerator(model_list=model_list, requests_per_minute=requests_per_minute)
    return await rm.generate_resume(user_info=user_info, job_description=job_description,  output_file=output_file)

# @validate_call
async def fix_resume(user_info:str, job_description:str, model_list:list[str], original_resume:FullCVModel,resume_images:list[str]=None, output_file:Path|None=None, requests_per_minute:int=15):
    rm = ResumeGenerator(model_list=model_list, requests_per_minute=requests_per_minute)
    return await rm.analyze_and_regenerate(resume_images=resume_images, original_resume=original_resume, user_info=user_info, job_description=job_description)



@validate_call
def render_resume(resume_model:FullCVModel, output_dir:Path=None) -> Path:
    try:
        import rendercv #noqa
    except ImportError:
        raise ImportError('Install rendercv with `pip install rendercv')
    
    if output_dir is None:
        output_dir = Path.cwd()/'rendered_cv'

    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')
    out_dir = output_dir / now
    out_dir.mkdir(exist_ok=True, parents=True)
    output_yaml = out_dir/f'{now}.yaml'
    resume_model.to_yaml(output_yaml, model_dump_kwargs={'exclude_unset':True, 'exclude_none':True})
    out_dir_str = out_dir.absolute().as_posix()
    os.system(f'rendercv render {output_yaml.absolute().as_posix()}  --output-folder-name {out_dir_str}') 
    
    return {'pdf_file': list(out_dir.glob('*.pdf')), 'png_file': [i for i in out_dir.glob('*.png')]}
