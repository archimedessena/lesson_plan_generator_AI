"""
PDF Generation Service for lesson plans using ReportLab
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from io import BytesIO
import os
from datetime import datetime
import logging

logger = logging.getLogger('lessonforge')


class LessonPlanPDFGenerator:
    """Generate professional PDF documents for lesson plans"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Create custom paragraph styles"""
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a365d'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c5282'),
            spaceAfter=6,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Subsection style
        self.styles.add(ParagraphStyle(
            name='SubSection',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=4,
            spaceBefore=8,
            fontName='Helvetica-Bold'
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        ))
        
        # Metadata style
        self.styles.add(ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#4a5568'),
            spaceAfter=4,
        ))
    
    def generate_pdf(self, lesson_plan, output_path=None):
        """
        Generate PDF for a lesson plan
        
        Args:
            lesson_plan: LessonPlan model instance
            output_path: Optional path to save PDF, if None returns BytesIO
            
        Returns:
            BytesIO or path to saved file
        """
        
        try:
            # Create PDF buffer or file
            if output_path:
                buffer = output_path
            else:
                buffer = BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=1*inch,
                bottomMargin=0.75*inch,
                title=lesson_plan.title,
                author='LessonForge'
            )
            
            # Build PDF content
            story = []
            
            # Header with logo/branding
            story.extend(self._build_header(lesson_plan))
            
            # Metadata section
            story.extend(self._build_metadata(lesson_plan))
            
            story.append(Spacer(1, 0.3*inch))
            
            # Main content
            story.extend(self._build_content(lesson_plan))
            
            # Footer info
            story.extend(self._build_footer(lesson_plan))
            
            # Build PDF
            doc.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
            
            logger.info(f"Generated PDF for lesson plan: {lesson_plan.uuid}")
            
            if not output_path:
                buffer.seek(0)
                return buffer
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            raise
    
    def _build_header(self, lesson_plan):
        """Build PDF header section"""
        elements = []
        
        # LessonForge branding
        title = Paragraph("LessonForge", self.styles['CustomTitle'])
        elements.append(title)
        
        subtitle = Paragraph(
            "AI-Powered Lesson Planning for Ghanaian Educators",
            ParagraphStyle(
                'subtitle',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#718096'),
                alignment=TA_CENTER,
                spaceAfter=12
            )
        )
        elements.append(subtitle)
        
        # Horizontal line
        elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _build_metadata(self, lesson_plan):
        """Build metadata section with lesson details"""
        elements = []
        
        # Create metadata table
        metadata = [
            ['Subject:', lesson_plan.subject],
            ['Topic:', lesson_plan.topic],
            ['Grade Level:', lesson_plan.grade_level],
            ['Curriculum:', lesson_plan.get_curriculum_display()],
            ['Duration:', f"{lesson_plan.duration} minutes"],
            ['Generated:', lesson_plan.created_at.strftime('%B %d, %Y at %I:%M %p')],
        ]
        
        table = Table(metadata, colWidths=[1.5*inch, 4.5*inch])
        table.setStyle(TableStyle([
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#4a5568')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _build_content(self, lesson_plan):
        """Build main content section"""
        elements = []
        
        # Split content into sections
        content = lesson_plan.content
        
        # Simple parsing - split by common section headers
        sections = self._parse_content_sections(content)
        
        for section_title, section_content in sections:
            if section_title:
                elements.append(Paragraph(section_title, self.styles['SectionHeader']))
            
            # Process content paragraphs
            paragraphs = section_content.split('\n\n')
            for para in paragraphs:
                para = para.strip()
                if para:
                    # Check if it's a bullet point or numbered list
                    if para.startswith('- ') or para.startswith('• '):
                        # Bullet point
                        para = para.replace('- ', '• ', 1)
                        elements.append(Paragraph(para, self.styles['CustomBody']))
                    elif len(para) > 0 and para[0].isdigit() and '. ' in para[:5]:
                        # Numbered list
                        elements.append(Paragraph(para, self.styles['CustomBody']))
                    else:
                        # Regular paragraph
                        # Check for bold markers
                        para = para.replace('**', '<b>', 1).replace('**', '</b>', 1)
                        elements.append(Paragraph(para, self.styles['CustomBody']))
                    
                    elements.append(Spacer(1, 0.05*inch))
        
        return elements
    
    def _parse_content_sections(self, content):
        """Parse content into sections based on headers"""
        sections = []
        
        # Common section headers
        headers = [
            'LESSON INFORMATION',
            'LEARNING OBJECTIVES',
            'RESOURCES & MATERIALS',
            'RESOURCES AND MATERIALS',
            'LESSON STRUCTURE',
            'INTRODUCTION',
            'MAIN TEACHING',
            'DEVELOPMENT',
            'CONCLUSION',
            'ASSESSMENT',
            'DIFFERENTIATION',
            'REFLECTION & NOTES',
            'TEACHER NOTES',
            'HOMEWORK',
            'EXTENSION ACTIVITIES'
        ]
        
        lines = content.split('\n')
        current_section = ('', '')
        current_content = []
        
        for line in lines:
            line_upper = line.strip().upper()
            is_header = False
            
            # Check if line is a header
            for header in headers:
                if header in line_upper or line_upper == header:
                    # Save previous section
                    if current_content:
                        sections.append((current_section, '\n'.join(current_content)))
                    current_section = line.strip()
                    current_content = []
                    is_header = True
                    break
            
            if not is_header:
                current_content.append(line)
        
        # Add last section
        if current_content:
            sections.append((current_section, '\n'.join(current_content)))
        
        return sections
    
    def _build_footer(self, lesson_plan):
        """Build footer section"""
        elements = []
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Divider line
        footer_text = Paragraph(
            f"<i>Generated by LessonForge • www.lessonforge.com</i>",
            ParagraphStyle(
                'footer',
                parent=self.styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#a0aec0'),
                alignment=TA_CENTER,
            )
        )
        elements.append(footer_text)
        
        return elements
    
    def _add_page_number(self, canvas, doc):
        """Add page numbers to each page"""
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.HexColor('#a0aec0'))
        canvas.drawRightString(
            doc.pagesize[0] - 0.75*inch,
            0.5*inch,
            text
        )
        canvas.restoreState()


# Singleton instance
pdf_generator = LessonPlanPDFGenerator()
