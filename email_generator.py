import random
import json
from typing import Dict, List, Optional
from lead_manager import Lead
import os
from datetime import datetime


class EmailGenerator:
    def __init__(self, config: Dict):
        self.config = config
        self.templates = config.get('email_templates', {})
        self.personalization = config.get('personalization', {})
        self.output_config = config.get('output', {})

    def _get_random_template(self, template_type: str) -> str:
        """Get a random template from the specified type"""
        templates = self.templates.get(f"{template_type}_templates", [])
        if not templates:
            return ""
        return random.choice(templates)

    def _personalize_content(self, template: str, lead: Lead, context: Dict = None) -> str:
        """Personalize template content with lead data"""
        if context is None:
            context = {}

        # Basic lead data
        replacements = {
            '{first_name}': lead.first_name,
            '{last_name}': lead.last_name,
            '{full_name}': f"{lead.first_name} {lead.last_name}",
            '{company_name}': lead.company_name,
            '{position}': lead.position,
            '{industry}': lead.industry,
            '{location}': lead.location or 'your area',
        }

        # Add context data
        replacements.update(context)

        # Apply replacements
        personalized = template
        for placeholder, value in replacements.items():
            if value:
                personalized = personalized.replace(placeholder, str(value))

        return personalized

    def _generate_subject_line(self, lead: Lead, context: Dict = None) -> str:
        """Generate a personalized subject line"""
        subject_template = self._get_random_template('subject')
        if not subject_template:
            # Fallback subject line
            return f"Quick question about {lead.company_name}"

        return self._personalize_content(subject_template, lead, context)

    def _generate_email_body(self, lead: Lead, context: Dict = None) -> str:
        """Generate the main email body"""
        opening_template = self._get_random_template('opening')

        # Build the email body
        body_parts = []

        # Opening
        if opening_template:
            body_parts.append(self._personalize_content(opening_template, lead, context))
        else:
            body_parts.append(f"Hi {lead.first_name},")

        # Main content based on personalization settings
        main_content = self._generate_main_content(lead, context)
        body_parts.append(main_content)

        # Closing
        body_parts.append(self._generate_closing(lead))

        return "\n\n".join(body_parts)

    def _generate_main_content(self, lead: Lead, context: Dict = None) -> str:
        """Generate the main content of the email"""
        if context is None:
            context = {}

        # Determine content based on research depth
        research_depth = self.personalization.get('research_depth', 'medium')

        if research_depth == 'high' and context.get('company_research'):
            # Use detailed company research
            return self._generate_researched_content(lead, context)
        elif research_depth == 'medium':
            # Use industry and position-based content
            return self._generate_medium_content(lead, context)
        else:
            # Use basic personalized content
            return self._generate_basic_content(lead, context)

    def _generate_researched_content(self, lead: Lead, context: Dict) -> str:
        """Generate content using detailed company research"""
        company_research = context.get('company_research', {})

        content = f"I've been following {lead.company_name}'s work"

        if company_research.get('recent_news'):
            content += f", especially your recent {company_research['recent_news']}"

        content += f". Your focus on {lead.industry} aligns perfectly with what we're building."

        if context.get('solution_benefit'):
            content += f"\n\nI believe our {context['solution_benefit']} could be particularly valuable for {lead.company_name} given your current challenges with {context.get('pain_point', 'industry regulations')}."

        return content

    def _generate_medium_content(self, lead: Lead, context: Dict) -> str:
        """Generate medium-depth personalized content"""
        content = f"Given your role as {lead.position} at {lead.company_name}, I thought you'd be interested in how we're helping {lead.industry} companies"

        if context.get('solution_benefit'):
            content += f" {context['solution_benefit']}"
        else:
            content += " streamline their operations"

        if context.get('pain_point'):
            content += f", especially when it comes to {context['pain_point']}."
        else:
            content += "."

        return content

    def _generate_basic_content(self, lead: Lead, context: Dict) -> str:
        """Generate basic personalized content"""
        content = f"I noticed {lead.company_name} operates in the {lead.industry} space, and I thought you might be interested in our solution"

        if context.get('solution_benefit'):
            content += f" that {context['solution_benefit']}"

        content += "."

        return content

    def _generate_closing(self, lead: Lead) -> str:
        """Generate email closing"""
        tone = self.personalization.get('tone', 'professional_friendly')

        if tone == 'formal':
            return f"I would welcome the opportunity to discuss how we might support {lead.company_name}'s objectives.\n\nBest regards,\n[Your Name]"
        elif tone == 'casual':
            return f"Would love to chat about this if you're interested!\n\nCheers,\n[Your Name]"
        else:  # professional_friendly
            return f"Would you be open to a quick 15-minute call to discuss how this might benefit {lead.company_name}?\n\nBest,\n[Your Name]"

    def generate_email(self, lead: Lead, context: Dict = None) -> Dict:
        """Generate a complete personalized email"""
        if context is None:
            context = {}

        # Generate subject and body
        subject = self._generate_subject_line(lead, context)
        body = self._generate_email_body(lead, context)

        # Ensure email length is within limits
        max_length = self.personalization.get('max_email_length', 300)
        if len(body) > max_length:
            # Truncate and add ellipsis
            body = body[:max_length-3] + "..."

        email_data = {
            'to': lead.email,
            'to_name': f"{lead.first_name} {lead.last_name}",
            'subject': subject,
            'body': body,
            'company': lead.company_name,
            'position': lead.position,
            'industry': lead.industry
        }

        # Add metadata if requested
        if self.output_config.get('include_metadata'):
            email_data['metadata'] = {
                'generated_at': str(datetime.now()),
                'lead_source': 'csv' if hasattr(lead, 'source') else 'snov',
                'personalization_level': self.personalization.get('research_depth', 'medium'),
                'tone': self.personalization.get('tone', 'professional_friendly')
            }

        return email_data

    def save_emails(self, emails: List[Dict], output_dir: str = None):
        """Save generated emails to file"""
        if not output_dir:
            output_dir = self.output_config.get('output_directory', 'output')

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        output_format = self.output_config.get('format', 'json')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if output_format == 'json':
            file_path = os.path.join(output_dir, f'emails_{timestamp}.json')
            with open(file_path, 'w') as f:
                json.dump(emails, f, indent=2)
        elif output_format == 'text':
            file_path = os.path.join(output_dir, f'emails_{timestamp}.txt')
            with open(file_path, 'w') as f:
                for email in emails:
                    f.write(f"To: {email['to_name']} <{email['to']}>\n")
                    f.write(f"Subject: {email['subject']}\n")
                    f.write(f"Company: {email['company']}\n")
                    f.write(f"Position: {email['position']}\n")
                    f.write(f"Industry: {email['industry']}\n")
                    f.write("-" * 50 + "\n")
                    f.write(email['body'])
                    f.write("\n\n" + "=" * 50 + "\n\n")
        else:  # markdown
            file_path = os.path.join(output_dir, f'emails_{timestamp}.md')
            with open(file_path, 'w') as f:
                for i, email in enumerate(emails, 1):
                    f.write(f"## Email {i}\n\n")
                    f.write(f"**To:** {email['to_name']} <{email['to']}>\n\n")
                    f.write(f"**Subject:** {email['subject']}\n\n")
                    f.write(f"**Company:** {email['company']}\n\n")
                    f.write(f"**Position:** {email['position']}\n\n")
                    f.write(f"**Industry:** {email['industry']}\n\n")
                    f.write("**Body:**\n\n")
                    f.write(email['body'])
                    f.write("\n\n---\n\n")

        return file_path
