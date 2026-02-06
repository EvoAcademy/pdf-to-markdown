from django import forms
from django.conf import settings


class UploadForm(forms.Form):
    """PDF upload form with an editable transcription prompt."""

    pdf_file = forms.FileField(
        label="PDF file",
        help_text=f"{settings.MAX_PDF_SIZE_MB} MB",
        widget=forms.ClearableFileInput(
            attrs={
                "accept": ".pdf,application/pdf",
                "class": (
                    "block w-full text-sm text-gray-500 "
                    "file:mr-4 file:py-2 file:px-4 file:rounded-lg "
                    "file:border-0 file:text-sm file:font-semibold "
                    "file:bg-indigo-50 file:text-indigo-700 "
                    "hover:file:bg-indigo-100 cursor-pointer"
                ),
            }
        ),
    )

    prompt = forms.CharField(
        label="Transcription prompt",
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "class": (
                    "w-full rounded-lg border border-gray-300 px-3 py-2 "
                    "text-sm focus:border-indigo-500 focus:ring-indigo-500"
                ),
                "placeholder": "Enter your transcription prompt...",
            }
        ),
        initial=settings.DEFAULT_PROMPT,
        required=True,
    )

    max_pages = forms.IntegerField(
        label="Max pages",
        initial=0,
        min_value=0,
        required=False,
        help_text="0 = all pages",
        widget=forms.NumberInput(
            attrs={
                "class": (
                    "w-24 rounded-lg border border-gray-300 px-3 py-2 "
                    "text-sm focus:border-indigo-500 focus:ring-indigo-500"
                ),
            }
        ),
    )

    def clean_pdf_file(self):
        pdf = self.cleaned_data["pdf_file"]

        # Validate extension
        if not pdf.name.lower().endswith(".pdf"):
            raise forms.ValidationError("Only PDF files are accepted.")

        # Validate size
        max_bytes = settings.MAX_PDF_SIZE_MB * 1024 * 1024
        if pdf.size > max_bytes:
            raise forms.ValidationError(
                f"File too large. Max size is {settings.MAX_PDF_SIZE_MB} MB."
            )

        return pdf
