from typing import List, Optional, Union
from pydantic import BaseModel, Field, HttpUrl
from datetime import date

class SocialNetwork(BaseModel):
    network: str
    username: str

class HighlightEntry(BaseModel):
    bullet: Optional[str] = None

class PublicationEntry(BaseModel):
    title: str
    authors: List[str]
    doi: Optional[str] = None
    date: Optional[date] = None

class GenericEntry(BaseModel):
    name: Optional[str] = None
    institution: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    location: Optional[str] = None
    area: Optional[str] = None
    degree: Optional[str] = None
    start_date: Optional[Union[date, str]] = None
    end_date: Optional[Union[date, str]] = None
    date: Optional[str] = None
    highlights: Optional[List[str]] = None
    summary: Optional[str] = None

class SkillEntry(BaseModel):
    label: str
    details: str

class CVContent(BaseModel):
    name: str
    location: str
    email: str
    phone: str
    social_networks: List[SocialNetwork]
    sections: dict[str, List[Union[
        GenericEntry, 
        HighlightEntry, 
        PublicationEntry, 
        SkillEntry
    ]]]

class ColorSettings(BaseModel):
    text: str
    name: str
    connections: str
    section_titles: str
    links: str
    last_updated_date_and_page_numbering: str

class PageSettings(BaseModel):
    size: str
    top_margin: str
    bottom_margin: str
    left_margin: str
    right_margin: str
    show_page_numbering: bool
    show_last_updated_date: bool

class TextSettings(BaseModel):
    font_family: str
    font_size: str
    leading: str
    alignment: str
    date_and_location_column_alignment: str

class LinksSettings(BaseModel):
    underline: bool
    use_external_link_icon: bool

class HeaderSettings(BaseModel):
    name_font_size: str
    name_bold: bool
    photo_width: str
    vertical_space_between_name_and_connections: str
    vertical_space_between_connections_and_first_section: str
    horizontal_space_between_connections: str
    separator_between_connections: str
    use_icons_for_connections: bool
    alignment: str

class SectionTitlesSettings(BaseModel):
    type: str
    font_size: str
    bold: bool
    small_caps: bool
    line_thickness: str
    vertical_space_above: str
    vertical_space_below: str
    line_type: str

class EntriesSettings(BaseModel):
    date_and_location_width: str
    left_and_right_margin: str
    horizontal_space_between_columns: str
    vertical_space_between_entries: str
    allow_page_break_in_entries: bool
    short_second_row: bool
    show_time_spans_in: List[str]

class HighlightsSettings(BaseModel):
    bullet: str
    top_margin: str
    left_margin: str
    vertical_space_between_highlights: str
    horizontal_space_between_bullet_and_highlight: str
    summary_left_margin: str

class EntryTypeTemplate(BaseModel):
    template: Optional[str] = None
    main_column_first_row_template: Optional[str] = None
    main_column_second_row_template: Optional[str] = None
    degree_column_width: Optional[str] = None
    date_and_location_column_template: Optional[str] = None
    main_column_second_row_without_journal_template: Optional[str] = None
    main_column_second_row_without_url_template: Optional[str] = None

class DesignSettings(BaseModel):
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

class LocaleSettings(BaseModel):
    language: str
    phone_number_format: str
    page_numbering_template: str
    last_updated_date_template: str
    date_template: str
    month: str
    months: str
    year: str
    years: str
    present: str
    to: str
    abbreviations_for_months: List[str]
    full_names_of_months: List[str]

class RenderCVSettings(BaseModel):
    date: date
    bold_keywords: List[str]

class FullCVModel(BaseModel):
    cv: CVContent
    design: DesignSettings
    locale: LocaleSettings
    rendercv_settings: RenderCVSettings