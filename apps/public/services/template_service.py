"""
Template Service.

Provides functions for:
- Rendering landing pages with Jinja2
- Organizing sections by type
- Applying template logic
"""

from typing import Any, Optional
from jinja2 import Environment


def render_landing_page(
    landing_page_data: dict,
    jinja_env: Environment
) -> str:
    """
    Render a landing page using Jinja2 template.

    Args:
        landing_page_data: Dict with landing page fields and sections
        jinja_env: Jinja2 environment

    Returns:
        Rendered HTML string
    """
    # Organize sections by type for easier template access
    sections_by_type = _organize_sections_by_type(landing_page_data.get('sections', []))

    # Prepare template context
    context = {
        'page': landing_page_data,
        'pain_points': sections_by_type.get('pain_point', []),
        'benefits': sections_by_type.get('benefit', []),
        'comparison_metrics': sections_by_type.get('comparison_metric', []),
        'testimonial': sections_by_type.get('testimonial', []),
        'differentiator': sections_by_type.get('differentiator', []),
        'pricing': sections_by_type.get('pricing', [])
    }

    # Render template
    try:
        template = jinja_env.get_template('landing_page.html')
        return template.render(**context)
    except Exception as e:
        # Fallback to simple rendering if template doesn't exist
        return _render_simple_fallback(landing_page_data, sections_by_type)


def _organize_sections_by_type(sections: list) -> dict:
    """
    Organize sections into dict by type.

    Args:
        sections: List of section dicts

    Returns:
        Dict with section_type as keys, sorted lists as values
    """
    organized = {}

    for section in sections:
        section_type = section.get('section_type')
        if section_type not in organized:
            organized[section_type] = []
        organized[section_type].append(section)

    # Sort each type by order_index
    for section_type in organized:
        organized[section_type].sort(key=lambda s: s.get('order_index', 0))

    return organized


def _render_simple_fallback(landing_page_data: dict, sections_by_type: dict) -> str:
    """
    Simple fallback rendering when template is not available.

    Args:
        landing_page_data: Landing page data
        sections_by_type: Organized sections

    Returns:
        Simple HTML string
    """
    html_parts = [
        '<!DOCTYPE html>',
        '<html>',
        '<head>',
        f'<title>{landing_page_data.get("name", "multicardz")}</title>',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '</head>',
        '<body>',
        '<div class="container">',
        f'<h1>{landing_page_data.get("headline", "")}</h1>',
        f'<p class="subheadline">{landing_page_data.get("subheadline", "")}</p>',
    ]

    # Pain points
    pain_points = sections_by_type.get('pain_point', [])
    if pain_points:
        html_parts.append('<section class="pain-points">')
        html_parts.append('<h2>Problems with ' + landing_page_data.get('competitor_name', 'Others') + '</h2>')
        html_parts.append('<ul>')
        for pp in pain_points:
            html_parts.append(f'<li>{pp["data"]["text"]}</li>')
        html_parts.append('</ul>')
        html_parts.append('</section>')

    # Benefits
    benefits = sections_by_type.get('benefit', [])
    if benefits:
        html_parts.append('<section class="benefits">')
        html_parts.append('<h2>How multicardz Solves This</h2>')
        for benefit in benefits:
            html_parts.append('<div class="benefit">')
            html_parts.append(f'<h3>{benefit["data"]["title"]}</h3>')
            html_parts.append(f'<p>{benefit["data"]["description"]}</p>')
            html_parts.append('</div>')
        html_parts.append('</section>')

    # Comparison metrics
    comparison = sections_by_type.get('comparison_metric', [])
    if comparison:
        html_parts.append('<section class="comparison">')
        html_parts.append(f'<h2>{landing_page_data.get("competitor_name", "Them")} vs multicardz</h2>')
        html_parts.append('<table>')
        for metric in comparison:
            html_parts.append('<tr>')
            html_parts.append(f'<td>{metric["data"]["label"]}</td>')
            html_parts.append(f'<td class="them">{metric["data"]["them"]}</td>')
            html_parts.append(f'<td class="us">{metric["data"]["us"]}</td>')
            html_parts.append('</tr>')
        html_parts.append('</table>')
        html_parts.append('</section>')

    # CTA
    html_parts.append('<div class="cta">')
    html_parts.append('<button class="cta-button">Start Free Trial</button>')
    html_parts.append('</div>')

    html_parts.extend([
        '</div>',
        '</body>',
        '</html>'
    ])

    return '\n'.join(html_parts)


def render_section(
    section_type: str,
    sections: list,
    jinja_env: Environment
) -> str:
    """
    Render a specific section type.

    Args:
        section_type: Type of section to render
        sections: List of section dicts
        jinja_env: Jinja2 environment

    Returns:
        Rendered HTML for section
    """
    # Filter sections by type
    filtered = [s for s in sections if s.get('section_type') == section_type]

    # Sort by order_index
    filtered.sort(key=lambda s: s.get('order_index', 0))

    # Render section template
    try:
        template = jinja_env.get_template(f'sections/{section_type}.html')
        return template.render(sections=filtered)
    except Exception:
        # Simple fallback
        parts = []
        for section in filtered:
            if section_type == 'pain_point':
                parts.append(f'<li>{section["data"]["text"]}</li>')
            elif section_type == 'benefit':
                parts.append(f'<div><h3>{section["data"]["title"]}</h3><p>{section["data"]["description"]}</p></div>')
        return '\n'.join(parts)
