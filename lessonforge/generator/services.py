"""
AI Service for lesson plan generation using Anthropic Claude
"""
import anthropic
from django.conf import settings
import time
import logging

logger = logging.getLogger('lessonforge')


class LessonPlanGenerator:
    """Service class for generating lesson plans using Claude AI"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
    
    def generate_lesson_plan(self, subject, topic, grade_level, curriculum, 
                           duration, objectives, additional_requirements='', 
                           template=None):
        """
        Generate a lesson plan using Claude AI
        
        Args:
            subject: Subject name
            topic: Specific topic
            grade_level: Grade/year level
            curriculum: Curriculum type (IGCSE, A-Level, WASSCE)
            duration: Lesson duration in minutes
            objectives: Learning objectives
            additional_requirements: Any additional requirements
            template: Optional template object
            
        Returns:
            tuple: (generated_content, metadata)
        """
        
        start_time = time.time()
        
        # Build system prompt
        system_prompt = self._build_system_prompt(curriculum, template)
        
        # Build user prompt
        user_prompt = self._build_user_prompt(
            subject, topic, grade_level, curriculum, 
            duration, objectives, additional_requirements
        )
        
        try:
            # Call Claude API with streaming
            full_content = ""
            input_tokens = 0
            output_tokens = 0
            
            with self.client.messages.stream(
                model=self.model,
                max_tokens=4000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0.7,
            ) as stream:
                for text in stream.text_stream:
                    full_content += text
                
                # Get usage metadata
                message = stream.get_final_message()
                input_tokens = message.usage.input_tokens
                output_tokens = message.usage.output_tokens
            
            generation_time = time.time() - start_time
            
            # Calculate estimated cost (Claude Sonnet pricing)
            # Input: $3 per million tokens, Output: $15 per million tokens
            estimated_cost = (input_tokens * 0.000003) + (output_tokens * 0.000015)
            
            metadata = {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                'generation_time': generation_time,
                'estimated_cost': estimated_cost,
                'model': self.model,
            }
            
            logger.info(f"Generated lesson plan: {subject} - {topic}, tokens: {metadata['total_tokens']}, time: {generation_time:.2f}s")
            
            return full_content, metadata
            
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise Exception(f"Failed to generate lesson plan: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in lesson plan generation: {str(e)}")
            raise Exception(f"An unexpected error occurred: {str(e)}")
    
    def _build_system_prompt(self, curriculum, template=None):
        """Build the system prompt for Claude"""
        
        curriculum_names = {
            'IGCSE': 'Cambridge IGCSE',
            'A_LEVEL': 'Cambridge A-Level',
            'WASSCE': 'West African Senior School Certificate Examination (WASSCE)'
        }
        
        curriculum_name = curriculum_names.get(curriculum, curriculum)
        
        base_prompt = f"""You are an expert educator specializing in the Ghanaian education system and {curriculum_name} curriculum. 

Your role is to create comprehensive, pedagogically sound lesson plans that are:
1. Aligned with {curriculum_name} syllabus requirements and assessment objectives
2. Culturally relevant to Ghanaian students and context
3. Practical and implementable in typical Ghanaian classroom settings
4. Based on current best practices in teaching and learning

LESSON PLAN STRUCTURE:
Generate a complete lesson plan with the following sections:

**LESSON INFORMATION**
- Subject, Topic, Grade Level, Duration
- Learning Objectives (clear, measurable, using Bloom's taxonomy)
- Prior Knowledge Required

**RESOURCES & MATERIALS**
- Teaching materials needed
- Student materials
- Technology/equipment (if applicable)
- Local/accessible alternatives for expensive resources

**LESSON STRUCTURE**

1. INTRODUCTION (10-15% of time)
   - Hook/engagement activity
   - Review of prior knowledge
   - Statement of learning objectives

2. MAIN TEACHING (60-70% of time)
   - Explanation and demonstration
   - Guided practice with examples
   - Independent practice activities
   - Differentiation strategies (for different ability levels)
   - Formative assessment checkpoints

3. CONCLUSION (10-15% of time)
   - Summary and review
   - Assessment of learning
   - Homework/extension activities
   - Link to next lesson

**ASSESSMENT**
- Formative assessment strategies during lesson
- Summative assessment tasks
- Success criteria
- Sample questions/tasks

**DIFFERENTIATION**
- Support for struggling learners
- Extensions for advanced students
- Adaptations for different learning styles

**REFLECTION & NOTES**
- Teacher notes and tips
- Common misconceptions to address
- Safety considerations (if applicable)

IMPORTANT GUIDELINES:
- Use clear, professional language suitable for teachers
- Include specific examples and sample questions
- Reference {curriculum_name} syllabus objectives where relevant
- Consider resource constraints in Ghanaian schools
- Include timing for each section
- Make activities practical and engaging
- Address common student difficulties in the topic
"""

        # Add template-specific customization if provided
        if template and template.system_prompt_addition:
            base_prompt += f"\n\nADDITIONAL TEMPLATE GUIDANCE:\n{template.system_prompt_addition}"
        
        return base_prompt
    
    def _build_user_prompt(self, subject, topic, grade_level, curriculum, 
                          duration, objectives, additional_requirements):
        """Build the user prompt with lesson details"""
        
        prompt = f"""Please create a lesson plan with the following specifications:

Subject: {subject}
Topic: {topic}
Grade Level: {grade_level}
Curriculum: {curriculum}
Duration: {duration} minutes

Learning Objectives:
{objectives}
"""

        if additional_requirements:
            prompt += f"\nAdditional Requirements/Notes:\n{additional_requirements}"
        
        prompt += "\n\nPlease generate a complete, detailed lesson plan following the structure and guidelines provided in your system instructions."
        
        return prompt


# Singleton instance
lesson_plan_generator = LessonPlanGenerator()
