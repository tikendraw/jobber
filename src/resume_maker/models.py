from datetime import date, datetime
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field, HttpUrl, field_validator
from rendercv.data import RenderCommandSettings

from config.baseconfig import YAMLConfigModel

rendercv_templates = Literal[
    "classic", "sb2nov", "engineeringresumes", "engineeringclassic", "moderncv"
]


def format_date(date_obj: Union[int, str, None]) -> str | int | None:
    """Format date object to string in YYYY-MM-DD format"""
    if date_obj is None:
        return None
    date_obj = str(date_obj).strip("\n")
    try:
        return int(date_obj)
    except ValueError as e:
        return date_obj


class BaseModelWithConfig(BaseModel):
    """Base model that excludes unset and None values when dumping"""

    class Config:
        exclude_unset = True
        exclude_none = True
        json_encoders = {type(None): lambda _: None}


class HighlightEntry(BaseModelWithConfig):
    bullet: Optional[str] = None


class EntryWithDate(BaseModelWithConfig):
    date: Union[int, str]


class PublicationEntry(EntryWithDate):
    title: str
    authors: List[str]
    doi: Optional[str] = None
    date: Optional[Union[int, str]] = Field(
        None, description="Date in YYYY-MM-DD, YYYY-MM, or YYYY format"
    )
    url: Optional[HttpUrl] = None
    journal: Optional[str] = None

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        if "date" in data and data["date"]:
            data["date"] = format_date(data["date"])
        return data


class SkillEntry(BaseModelWithConfig):
    label: str
    details: str


class OneLineEntry(BaseModelWithConfig):
    """Minimal version of entry_types.OneLineEntry"""

    label: str
    details: str


class BulletEntry(BaseModelWithConfig):
    """Minimal version of entry_types.BulletEntry"""

    bullet: str


class EntryBase(BaseModelWithConfig):
    """Common fields shared by entry types"""

    location: Optional[str] = None
    start_date: Optional[Union[int, str]] = None
    end_date: Optional[Union[int, str, Literal["present"]]] = None
    date: Optional[Union[int, str]] = None
    highlights: Optional[List[str]] = None
    summary: Optional[str] = None

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        if "start_date" in data and data["start_date"]:
            data["start_date"] = format_date(data["start_date"])
        if "end_date" in data and data["end_date"]:
            data["end_date"] = format_date(data["end_date"])
        if "date" in data and data["date"]:
            data["date"] = format_date(data["date"])
        return data


class NormalEntry(EntryBase):
    """Minimal version of entry_types.NormalEntry"""

    name: str


class ExperienceEntry(EntryBase):
    """Minimal version of entry_types.ExperienceEntry"""

    company: str
    position: str


class EducationEntry(EntryBase):
    """Minimal version of entry_types.EducationEntry
    Required fields: institution and area
    """

    institution: str  # Required
    area: str  # Required
    degree: Optional[str] = None


SocialNetworkName = Literal[
    "LinkedIn",
    "GitHub",
    "GitLab",
    "Instagram",
    "ORCID",
    "Mastodon",
    "StackOverflow",
    "ResearchGate",
    "YouTube",
    "Google Scholar",
    "Telegram",
]


class SocialNetwork(BaseModelWithConfig):
    network: SocialNetworkName
    username: str


class CVContent(BaseModelWithConfig):
    name: str
    location: str
    email: str
    phone: str
    social_networks: List[SocialNetwork]
    sections: dict[
        str,
        List[
            Union[
                OneLineEntry,
                NormalEntry,
                ExperienceEntry,
                EducationEntry,
                PublicationEntry,
                BulletEntry,
                str,
            ]
        ],
    ] = Field(
        description="Sections of the CV containing different types of entries",
    )


# ----------------------------------


class ColorSettings(BaseModelWithConfig):
    text: str
    name: str
    connections: str
    section_titles: str
    links: str
    last_updated_date_and_page_numbering: str


class PageSettings(BaseModelWithConfig):
    size: str
    top_margin: str
    bottom_margin: str
    left_margin: str
    right_margin: str
    show_page_numbering: bool
    show_last_updated_date: bool


class TextSettings(BaseModelWithConfig):
    font_family: str
    font_size: str
    leading: str
    alignment: str
    date_and_location_column_alignment: str


class LinksSettings(BaseModelWithConfig):
    underline: bool
    use_external_link_icon: bool


class HeaderSettings(BaseModelWithConfig):
    name_font_size: str
    name_bold: bool
    photo_width: str
    vertical_space_between_name_and_connections: str
    vertical_space_between_connections_and_first_section: str
    horizontal_space_between_connections: str
    separator_between_connections: str
    use_icons_for_connections: bool
    alignment: str


class SectionTitlesSettings(BaseModelWithConfig):
    type: str
    font_size: str
    bold: bool
    small_caps: bool
    line_thickness: str
    vertical_space_above: str
    vertical_space_below: str
    line_type: str


class EntriesSettings(BaseModelWithConfig):
    date_and_location_width: str
    left_and_right_margin: str
    horizontal_space_between_columns: str
    vertical_space_between_entries: str
    allow_page_break_in_entries: bool
    short_second_row: bool
    show_time_spans_in: List[str]


class HighlightsSettings(BaseModelWithConfig):
    bullet: str
    top_margin: str
    left_margin: str
    vertical_space_between_highlights: str
    horizontal_space_between_bullet_and_highlight: str
    summary_left_margin: str


class EntryTypeTemplate(BaseModelWithConfig):
    """Template for different entry types in the CV"""

    template: str | None = Field(default=None, exclude_none=True, exclude_unset=True)
    main_column_first_row_template: str | None = Field(
        default=None, exclude_none=True, exclude_unset=True
    )
    main_column_second_row_template: str | None = Field(
        default=None, exclude_none=True, exclude_unset=True
    )
    degree_column_width: str | None = Field(
        default=None, exclude_none=True, exclude_unset=True
    )
    date_and_location_column_template: str | None = Field(
        default=None, exclude_none=True, exclude_unset=True
    )
    main_column_second_row_without_journal_template: str | None = Field(
        default=None, exclude_none=True, exclude_unset=True
    )
    main_column_second_row_without_url_template: str | None = Field(
        default=None, exclude_none=True, exclude_unset=True
    )


class DesignSettings(BaseModelWithConfig):
    """Settings for CV design"""

    theme: str
    page: PageSettings
    colors: ColorSettings
    text: TextSettings
    links: LinksSettings
    header: HeaderSettings
    section_titles: SectionTitlesSettings
    entries: EntriesSettings
    highlights: HighlightsSettings
    entry_types: dict[str, EntryTypeTemplate]


class LocaleSettings(BaseModelWithConfig):
    """This class is the data model of the locale catalog. The values of each field
    updates the `locale` dictionary.
    """

    language: str = Field(
        default="en",
    )
    phone_number_format: Optional[Literal["national", "international", "E164"]] = Field(
        default="national",
    )
    page_numbering_template: str = Field(
        default="NAME - Page PAGE_NUMBER of TOTAL_PAGES",
    )
    last_updated_date_template: str = Field(
        default="Last updated in TODAY",
    )
    date_template: Optional[str] = Field(
        default="MONTH_ABBREVIATION YEAR",
    )
    month: Optional[str] = Field(
        default="month",
    )
    months: Optional[str] = Field(
        default="months",
    )
    year: Optional[str] = Field(
        default="year",
    )
    years: Optional[str] = Field(
        default="years",
    )
    present: Optional[str] = Field(
        default="present",
    )
    to: Optional[str] = Field(
        default="–",  # NOQA: RUF001
    )
    abbreviations_for_months: list[str] = Field(
        # Month abbreviations are taken from
        # https://web.library.yale.edu/cataloging/months:
        default=[
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "June",
            "July",
            "Aug",
            "Sept",
            "Oct",
            "Nov",
            "Dec",
        ],
        title="Abbreviations of Months",
        description="Abbreviations of the months in the locale.",
    )
    full_names_of_months: list[str] = Field(
        default=[
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ],
        title="Full Names of Months",
        description="Full names of the months in the locale.",
    )


# from rendercv.data import RenderCVSettings # has some extra fields that doesn't apear on yaml


class RenderCVSettings(BaseModelWithConfig):
    date: Union[int, str] = Field(
        default_factory=lambda: date.today().strftime("%Y-%m-%d"),
        description="Date in YYYY-MM-DD format",
    )
    bold_keywords: List[str]

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        if "date" in data and data["date"]:
            data["date"] = format_date(data["date"])
        return data


class CVModel(BaseModelWithConfig):
    cv: CVContent


# instances of theme
# sb2nov Theme
sb2nov_design = DesignSettings(
    theme="sb2nov",
    page=PageSettings(
        size="us-letter",
        top_margin="1.5cm",
        bottom_margin="1.5cm",
        left_margin="2cm",
        right_margin="2cm",
        show_page_numbering=True,
        show_last_updated_date=False,
    ),
    colors=ColorSettings(
        text="black",
        name="black",
        connections="black",
        section_titles="black",
        links="#004f90",
        last_updated_date_and_page_numbering="grey",
    ),
    text=TextSettings(
        font_family="New Computer Modern",
        font_size="8pt",
        leading="0.6em",
        alignment="justified",
        date_and_location_column_alignment="right",
    ),
    links=LinksSettings(underline=False, use_external_link_icon=True),
    header=HeaderSettings(
        name_font_size="20pt",
        name_bold=True,
        photo_width="3.5cm",
        vertical_space_between_name_and_connections="0.7cm",
        vertical_space_between_connections_and_first_section="0.7cm",
        horizontal_space_between_connections="0.5cm",
        separator_between_connections="",
        use_icons_for_connections=True,
        alignment="center",
    ),
    section_titles=SectionTitlesSettings(
        type="with-parial-line",
        font_size="1.0em",
        bold=True,
        small_caps=False,
        line_thickness="0.5pt",
        vertical_space_above="0.2cm",
        vertical_space_below="0.1cm",
        line_type="with-full-line",
    ),
    entries=EntriesSettings(
        date_and_location_width="4.15cm",
        left_and_right_margin="0.2cm",
        horizontal_space_between_columns="0.1cm",
        vertical_space_between_entries="1.0em",
        allow_page_break_in_entries=True,
        short_second_row=False,
        show_time_spans_in=[],
    ),
    highlights=HighlightsSettings(
        bullet="◦",
        top_margin="0.15cm",
        left_margin="0.4cm",
        vertical_space_between_highlights="0.15cm",
        horizontal_space_between_bullet_and_highlight="0.5em",
        summary_left_margin="0cm",
    ),
    entry_types={
        "one_line_entry": EntryTypeTemplate(template="**LABEL:** DETAILS"),
        "education_entry": EntryTypeTemplate(
            main_column_first_row_template=r"**INSTITUTION**\n*DEGREE in AREA*",
            degree_column_width="1cm",
            main_column_second_row_template=r"SUMMARY\nHIGHLIGHTS",
            date_and_location_column_template=r"*LOCATION*\n*DATE*",
        ),
        "normal_entry": EntryTypeTemplate(
            main_column_first_row_template=r"**NAME**",
            main_column_second_row_template=r"SUMMARY\nHIGHLIGHTS",
            date_and_location_column_template=r"*LOCATION*\n*DATE*",
        ),
        "experience_entry": EntryTypeTemplate(
            main_column_first_row_template=r"**POSITION**\n*COMPANY*",
            main_column_second_row_template=r"SUMMARY\nHIGHLIGHTS",
            date_and_location_column_template=r"*LOCATION*\n*DATE*",
        ),
        "publication_entry": EntryTypeTemplate(
            main_column_first_row_template=r"**TITLE**",
            main_column_second_row_template=r"AUTHORS\nURL (JOURNAL)",
            main_column_second_row_without_journal_template=r"AUTHORS\nURL",
            main_column_second_row_without_url_template=r"AUTHORS\nJOURNAL",
            date_and_location_column_template="DATE",
        ),
    },
)

sb2nov_locale = LocaleSettings(
    language="en",
    phone_number_format="national",
    page_numbering_template="NAME - Page PAGE_NUMBER of TOTAL_PAGES",
    last_updated_date_template="Last updated in TODAY",
    date_template="MONTH_ABBREVIATION YEAR",
    month="month",
    months="months",
    year="year",
    years="years",
    present="present",
    to="–",
    abbreviations_for_months=[
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "June",
        "July",
        "Aug",
        "Sept",
        "Oct",
        "Nov",
        "Dec",
    ],
    full_names_of_months=[
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ],
)

sb2nov_rendercv_settings = RenderCVSettings(
    date=date.today().strftime("%Y-%m-%d"), bold_keywords=[]
)

# Engineering Resumes Theme
engineering_resumes_design = DesignSettings(
    theme="engineeringresumes",
    page=PageSettings(
        size="us-letter",
        top_margin="2cm",
        bottom_margin="2cm",
        left_margin="2cm",
        right_margin="2cm",
        show_page_numbering=False,
        show_last_updated_date=False,
    ),
    colors=ColorSettings(
        text="black",
        name="black",
        connections="black",
        section_titles="black",
        links="black",
        last_updated_date_and_page_numbering="grey",
    ),
    text=TextSettings(
        font_family="XCharter",
        font_size="10pt",
        leading="0.6em",
        alignment="justified",
        date_and_location_column_alignment="right",
    ),
    links=LinksSettings(underline=True, use_external_link_icon=False),
    header=HeaderSettings(
        name_font_size="25pt",
        name_bold=False,
        photo_width="3.5cm",
        vertical_space_between_name_and_connections="0.7cm",
        vertical_space_between_connections_and_first_section="0.7cm",
        horizontal_space_between_connections="0.5cm",
        separator_between_connections="|",
        use_icons_for_connections=False,
        alignment="center",
    ),
    section_titles=SectionTitlesSettings(
        type="with-parial-line",
        font_size="1.2em",
        bold=True,
        small_caps=False,
        line_thickness="0.5pt",
        vertical_space_above="0.55cm",
        vertical_space_below="0.3cm",
        line_type="with-full-line",
    ),
    entries=EntriesSettings(
        date_and_location_width="4.15cm",
        left_and_right_margin="0cm",
        horizontal_space_between_columns="0.1cm",
        vertical_space_between_entries="0.4cm",
        allow_page_break_in_entries=True,
        short_second_row=False,
        show_time_spans_in=[],
    ),
    highlights=HighlightsSettings(
        bullet="•",
        top_margin="0.25cm",
        left_margin="0cm",
        vertical_space_between_highlights="0.19cm",
        horizontal_space_between_bullet_and_highlight="0.3em",
        summary_left_margin="0cm",
    ),
    entry_types={
        "one_line_entry": EntryTypeTemplate(template=r"**LABEL:** DETAILS"),
        "education_entry": EntryTypeTemplate(
            main_column_first_row_template=r"**INSTITUTION**, DEGREE in AREA -- LOCATION",
            degree_column_width="1cm",
            main_column_second_row_template=r"SUMMARY\nHIGHLIGHTS",
            date_and_location_column_template=r"DATE",
        ),
        "normal_entry": EntryTypeTemplate(
            main_column_first_row_template=r"**NAME** -- **LOCATION**",
            main_column_second_row_template=r"SUMMARY\nHIGHLIGHTS",
            date_and_location_column_template="DATE",
        ),
        "experience_entry": EntryTypeTemplate(
            main_column_first_row_template=r"**POSITION**, COMPANY -- LOCATION",
            main_column_second_row_template=r"SUMMARY\nHIGHLIGHTS",
            date_and_location_column_template="DATE",
        ),
        "publication_entry": EntryTypeTemplate(
            main_column_first_row_template=r"**TITLE**",
            main_column_second_row_template=r"AUTHORS\nURL (JOURNAL)",
            main_column_second_row_without_journal_template=r"AUTHORS\nURL",
            main_column_second_row_without_url_template=r"AUTHORS\nJOURNAL",
            date_and_location_column_template="DATE",
        ),
    },
)

engineering_resumes_locale = LocaleSettings(
    language="en",
    phone_number_format="national",
    page_numbering_template="NAME - Page PAGE_NUMBER of TOTAL_PAGES",
    last_updated_date_template="Last updated in TODAY",
    date_template="MONTH_ABBREVIATION YEAR",
    month="month",
    months="months",
    year="year",
    years="years",
    present="present",
    to="–",
    abbreviations_for_months=[
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "June",
        "July",
        "Aug",
        "Sept",
        "Oct",
        "Nov",
        "Dec",
    ],
    full_names_of_months=[
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ],
)

engineering_resumes_rendercv_settings = RenderCVSettings(
    date=date.today().strftime("%Y-%m-%d"), bold_keywords=[]
)


THEME_REGISTRY = {
    "engineeringresumes": {
        "design": engineering_resumes_design,
        "locale": engineering_resumes_locale,
        "rendercv_settings": engineering_resumes_rendercv_settings,
    },
    "sb2nov": {
        "design": sb2nov_design,
        "locale": sb2nov_locale,
        "rendercv_settings": sb2nov_rendercv_settings,
    },
}


class FullCVModel(YAMLConfigModel):
    """Full CV model including content and settings"""

    cv: CVContent
    design: DesignSettings
    locale: LocaleSettings
    rendercv_settings: RenderCVSettings

    class Config(BaseModelWithConfig.Config):
        pass

    @classmethod
    def from_cvmodel(
        cls,
        cv: CVContent,
        theme: rendercv_templates = "sb2nov",
        design: Optional[DesignSettings] = None,
        locale: Optional[LocaleSettings] = None,
        rendercv_settings: Optional[RenderCVSettings] = None,
    ):
        """
        Create a FullCVModel with flexible theme and settings configuration.

        Args:
            cv (CVContent): The CV content
            theme (str, optional): Name of the predefined theme
            design (DesignSettings, optional): Custom design settings
            locale (LocaleSettings, optional): Custom locale settings
            rendercv_settings (RenderCVSettings, optional): Custom render settings

        Returns:
            FullCVModel: Configured CV model

        Raises:
            ValueError: If an invalid theme is specified
        """
        # If a theme is specified, get its default implementations
        if theme:
            if theme not in THEME_REGISTRY:
                raise ValueError(
                    f"Unknown theme: {theme}. Available themes: {list(THEME_REGISTRY.keys())}"
                )

            theme_config = THEME_REGISTRY[theme]

            # Override theme defaults with any explicitly provided settings
            design = design or theme_config["design"]
            locale = locale or theme_config["locale"]
            rendercv_settings = rendercv_settings or theme_config["rendercv_settings"]

        assert design is not None, "Design settings must be provided"
        assert locale is not None, "Locale settings must be provided"
        assert rendercv_settings is not None, "Render settings must be provided"

        return FullCVModel(
            cv=cv, design=design, locale=locale, rendercv_settings=rendercv_settings
        )
