# Structure of the YAML Input File

RenderCV's input file consists of four parts: `cv`, `design`, `locale` and `rendercv_settings`.

```yaml title="Your_Name_CV.yaml"
cv:
  ...
  YOUR CONTENT
  ...

```

- The `cv` field is mandatory. It contains the **content of the CV**.

!!! tip "Tip: JSON Schema"
    To maximize your productivity while editing the input YAML file, set up RenderCV's JSON Schema in your IDE. It will validate your inputs on the fly and give auto-complete suggestions.


## "`cv`" field

The `cv` field of the YAML input starts with generic information, as shown below.

```yaml
cv:
  name: John Doe
  location: Your Location
  email: youremail@yourdomain.com
  phone: +9xxxxxxxxxxx # (1)!
  website: https://example.com/
  social_networks:
    - network: LinkedIn # (2)!
      username: yourusername
    - network: GitHub 
      username: yourusername
  ...
```

2.  The available social networks are: [    "LinkedIn",
    "GitHub",
    "GitLab",
    "Instagram",
    "ORCID",
    "Mastodon",
    "StackOverflow",
    "ResearchGate",
    "YouTube",
    "Google Scholar",
    "Telegram",].

None of the values above are required. You can omit any or all of them, and RenderCV will adapt to your input. These generic fields are used in the header of the CV.

The main content of your CV is stored in a field called `sections`.

```yaml hl_lines="12 13 14 15"
cv:
  name: John Doe
  location: Your Location
  email: youremail@yourdomain.com
  phone: +905419999999
  website: https://yourwebsite.com/
  social_networks:
    - network: LinkedIn
      username: yourusername
    - network: GitHub
      username: yourusername
  sections:
    ...
    YOUR CONTENT
    ...
```

### "`cv.sections`" field

The `cv.sections` field is a dictionary where the keys are the section titles, and the values are lists. Each item of the list is an entry for that section.

Here is an example:

```yaml hl_lines="3 7"
cv:
  sections:
    this_is_a_section_title: # (1)!
      - This is a TextEntry. # (2)!
      - This is another TextEntry under the same section.
      - This is another another TextEntry under the same section.
    this_is_another_section_title:
      - company: This time it's an ExperienceEntry. # (3)!
        position: Your position
        start_date: 2019-01-01
        end_date: 2020-01
        location: TX, USA
        highlights: 
          - This is a highlight (a bullet point).
          - This is another highlight.
      - company: Another ExperienceEntry.
        position: Your position
        start_date: 2019-01-01
        end_date: 2020-01-10
        location: TX, USA
        highlights: 
          - This is a highlight (a bullet point).
          - This is another highlight.
```

1. The section titles can be anything you want. They are the keys of the `sections` dictionary.
2. Each section is a list of entries. This section has three `TextEntry`s.
3. There are seven different entry types in RenderCV. Any of them can be used in the sections. This section has two `ExperienceEntry`s.

There are seven different entry types in RenderCV. Different types of entries cannot be mixed under the same section, so for each section, you can only use one type of entry.

The available entry types are: [`EducationEntry`](#educationentry), [`ExperienceEntry`](#experienceentry), [`PublicationEntry`](#publicationentry), [`NormalEntry`](#normalentry), [`OneLineEntry`](#onelineentry), [`BulletEntry`](#bulletentry), and [`TextEntry`](#textentry).

Each entry type is a different object (a dictionary). Below, you can find all the entry types along with their optional/mandatory fields and how they appear in each built-in theme.


"EducationEntry"
**Mandatory Fields:**

- `institution`: The name of the institution.
- `area`: The area of study.

**Optional Fields:**

- `degree`: The type of degree (e.g., BS, MS, PhD)
- `location`: The location
- `start_date`: The start date in `YYYY-MM-DD`, `YYYY-MM`, or `YYYY` format
- `end_date`: The end date in `YYYY-MM-DD`, `YYYY-MM`, or `YYYY` format or "present"
- `date`: The date as a custom string or in `YYYY-MM-DD`, `YYYY-MM`, or `YYYY` format. This will override `start_date` and `end_date`.
- `highlights`: The list of bullet points
- `summary`: The summary

"ExperienceEntry" 
**Mandatory Fields:**

- `company`: The name of the company
- `position`: The position

**Optional Fields:**

- `location`: The location
- `start_date`: The start date in `YYYY-MM-DD`, `YYYY-MM`, or `YYYY` format
- `end_date`: The end date in `YYYY-MM-DD`, `YYYY-MM`, or `YYYY` format or "present"
- `date`: The date as a custom string or in `YYYY-MM-DD`, `YYYY-MM`, or `YYYY` format. This will override `start_date` and `end_date`.
- `highlights`: The list of bullet points
- `summary`: The summary

"PublicationEntry"
**Mandatory Fields:**

- `title`: The title of the publication
- `authors`: The authors of the publication

**Optional Fields:**

- `doi`: The DOI of the publication
- `journal`: The journal of the publication
- `date`: The date as a custom string or in `YYYY-MM-DD`, `YYYY-MM`, or `YYYY` format

"NormalEntry"
**Mandatory Fields:**

- `name`: The name of the entry

**Optional Fields:**

- `location`: The location
- `start_date`: The start date in `YYYY-MM-DD`, `YYYY-MM`, or `YYYY` format
- `end_date`: The end date in `YYYY-MM-DD`, `YYYY-MM`, or `YYYY` format or "present"
- `date`: The date as a custom string or in `YYYY-MM-DD`, `YYYY-MM`, or `YYYY` format. This will override `start_date` and `end_date`.
- `highlights`: The list of bullet points
- `summary`: The summary

"OneLineEntry" 
**Mandatory Fields:**

- `label`: The label of the entry
- `details`: The details of the entry

"BulletEntry"
**Mandatory Fields:**

- `bullet`: The bullet point

"TextEntry"
**Mandatory Fields:**

- The text itself


#### Markdown Syntax

All the fields in the entries support Markdown syntax.

You can make anything bold by surrounding it with `**`, italic with `*`, and links with `[]()`, as shown below.

```yaml
company: "**This will be bold**, *this will be italic*, 
  and [this will be a link](https://example.com)."
```

