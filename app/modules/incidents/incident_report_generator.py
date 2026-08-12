from datetime import datetime
from app.core.logging import get_logger
from app.modules.incidents.models import Incident

log = get_logger("app.modules.incidents.incident_report_generator")

class IncidentReportGenerator:
    """
    Generates comprehensive Markdown/PDF reports for incidents.
    """

    async def generate_markdown_report(self, incident: Incident) -> str:
        """
        Generate a Markdown report for the incident.
        """
        log.info(f"Generating Markdown report for incident {incident.incident_id}")
        
        lines = [
            f"# Incident Report: {incident.title}",
            f"**Incident ID:** {incident.incident_id}",
            f"**State:** {incident.state.value}",
            f"**Severity:** {incident.severity.value}",
            f"**Created At:** {incident.created_at.isoformat()}",
            f"**Updated At:** {incident.updated_at.isoformat()}",
            "",
            "## Description",
            incident.description,
            "",
            "## Timeline"
        ]

        for event in sorted(incident.timeline, key=lambda e: e.timestamp):
            lines.append(f"- **{event.timestamp.isoformat()}** [{event.event_type}]: {event.description}")
            
        return "\\n".join(lines)

    async def generate_pdf_report(self, incident: Incident) -> bytes:
        """
        Generate a PDF report for the incident.
        """
        log.info(f"Generating PDF report for incident {incident.incident_id}")
        # Placeholder for actual PDF generation logic.
        md_content = await self.generate_markdown_report(incident)
        pdf_bytes = f"PDF_CONTENT_MOCK\\n\\n{md_content}".encode("utf-8")
        return pdf_bytes
