from app.modules.agents.document.providers.email import EmailProvider
from app.modules.agents.document.providers.excel import ExcelProvider
from app.modules.agents.document.providers.html import HTMLProvider
from app.modules.agents.document.providers.image import ImageProvider
from app.modules.agents.document.providers.pdf import PDFProvider
from app.modules.agents.document.providers.word import WordProvider

__all__ = [
    "PDFProvider",
    "WordProvider",
    "ExcelProvider",
    "HTMLProvider",
    "ImageProvider",
    "EmailProvider",
]
