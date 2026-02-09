from django import forms
from django.conf import settings

INPUT_CLASS = (
    "w-full rounded-lg border border-gray-300 px-3 py-2 "
    "text-sm focus:border-indigo-500 focus:ring-indigo-500"
)

NUMBER_CLASS = (
    "w-24 rounded-lg border border-gray-300 px-3 py-2 "
    "text-sm focus:border-indigo-500 focus:ring-indigo-500"
)


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
                "class": INPUT_CLASS,
                "placeholder": "Enter your transcription prompt...",
            }
        ),
        initial=settings.DEFAULT_PROMPT,
        required=True,
    )

    start_page = forms.IntegerField(
        label="Start page",
        initial=1,
        min_value=1,
        required=True,
        widget=forms.NumberInput(attrs={"class": NUMBER_CLASS, "id": "id_start_page"}),
    )

    end_page = forms.IntegerField(
        label="End page",
        initial=0,
        min_value=0,
        required=False,
        help_text="0 = last page",
        widget=forms.NumberInput(attrs={"class": NUMBER_CLASS, "id": "id_end_page"}),
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

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_page", 1)
        end = cleaned.get("end_page", 0)

        if end and end < start:
            raise forms.ValidationError(
                "End page must be greater than or equal to start page."
            )

        return cleaned


# ── Settings form ─────────────────────────────────────────────

OPENAI_MODEL_CHOICES = [
    ("gpt-5-mini", "gpt-5-mini"),
    ("custom", "Custom (enter below)"),
]

GEMINI_MODEL_CHOICES = [
    ("gemini-3-flash-preview", "gemini-3-flash-preview"),
    ("custom", "Custom (enter below)"),
]


class SettingsForm(forms.Form):
    """Form to select vision backend and model (overrides env when set)."""

    vision_backend = forms.ChoiceField(
        label="Vision backend",
        choices=[
            ("", "Use environment default"),
            ("openai", "OpenAI (GPT)"),
            ("gemini", "Google Gemini"),
        ],
        required=False,
        widget=forms.Select(attrs={"class": INPUT_CLASS}),
    )
    openai_model = forms.ChoiceField(
        label="OpenAI model",
        choices=OPENAI_MODEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": INPUT_CLASS}),
    )
    openai_model_custom = forms.CharField(
        label="OpenAI custom model ID",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={"class": INPUT_CLASS, "placeholder": "e.g. gpt-4o"}
        ),
    )
    gemini_model = forms.ChoiceField(
        label="Gemini model",
        choices=GEMINI_MODEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": INPUT_CLASS}),
    )
    gemini_model_custom = forms.CharField(
        label="Gemini custom model ID",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={"class": INPUT_CLASS, "placeholder": "e.g. gemini-1.5-pro"}
        ),
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("openai_model") == "custom":
            custom = (cleaned.get("openai_model_custom") or "").strip()
            if not custom:
                self.add_error(
                    "openai_model_custom",
                    "Enter a model ID when using Custom.",
                )
            else:
                cleaned["openai_model"] = custom
        if cleaned.get("gemini_model") == "custom":
            custom = (cleaned.get("gemini_model_custom") or "").strip()
            if not custom:
                self.add_error(
                    "gemini_model_custom",
                    "Enter a model ID when using Custom.",
                )
            else:
                cleaned["gemini_model"] = custom
        return cleaned
