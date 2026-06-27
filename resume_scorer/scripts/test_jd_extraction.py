"""Quick check for JD skill extraction — run from resume_scorer/: python scripts/test_jd_extraction.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from structurer import structure_jd

TALENT_ACQUISITION_JD = """
Company Logo & Tag line


We are Lenovo. We do what we say. We own what we do. We WOW our customers.

Lenovo is a US$69 billion revenue global technology powerhouse, ranked #196 in the
Fortune Global 500, and serving millions of customers every day in 180 markets.
Focused on a bold vision to deliver Smarter Technology for All, Lenovo has built on its
success as the world's largest PC company with a full-stack portfolio of AI-enabled, AI
ready, and AI-optimized devices (PCs, workstations, smartphones, tablets),
infrastructure (server, storage, edge, high performance computing and software
defined infrastructure), software, solutions, and services. Lenovo's continued
investment in world-changing innovation is building a more equitable, trustworthy,
and smarter future for everyone, everywhere. Lenovo is listed on the Hong Kong stock
exchange under Lenovo Group Limited (HKSE: 992) (ADR: LNVGY).

This transformation together with Lenovo's world-changing innovation is building a
more inclusive, trustworthy, and smarter future for everyone, everywhere. To find
out more visit www.lenovo.com, and read about the latest news via our StoryHub.

Job Title Talent Acquisition Intern
Job Responsibilities
▪ Location: Gurgaon
▪ Stipend : 30,000 per month
▪ Duration – 11 months


We are looking for a Talent Acquisition Intern with a strong inclination toward data,
analytics, AI, and technical problem-solving. This role offers an opportunity to work
on recruitment data, talent data research, and automation use cases, while
exploring AI/agentic solutions in talent acquisition.
You will support the APAC TA team in data analysis, reporting, talent intelligence,
and innovation projects, enabling smarter and faster hiring decisions.


Key Responsibilities
Analyze recruiting data using Excel/SQL to generate insights
Build dashboards and reports using Power BI
Support automation using Co-pilot & Power Automate
Assist in AI and agentic hiring projects

Conduct talent data research and market intelligence analysis
Work on data mining and talent data structuring for hiring insights
Support development of technical/automation solutions (coding, scripts, workflows)

Skills & Experience
Must-have
Strong Excel & SQL skills
Experience with Power BI / data visualization tools
Basic understanding of automation, AI, or scripting
Strong analytical and problem-solving skills
Inclination toward technical work (coding / automation mindset)

Good-to-have:
Exposure to AI/ML or agent-based systems
Experience with data research, APIs, or data pipelines
Knowledge of Python or other programming languages
Interest in TA analytics, talent intelligence, or HR tech

Footnote  Stay connected: Career Opportunities Ι Join our Talent Community
Know More about us :  Women in Technology I  Lenovo Careers
Follow us: Instagram Facebook Twitter LinkedIn YouTube
"""

DIGITAL_ANALYST_JD = """
Company Logo & Tag line


We are Lenovo. We do what we say. We own what we do. We WOW our customers.

Lenovo is a US$69 billion revenue global technology powerhouse, ranked #196 in the
Fortune Global 500, and serving millions of customers every day in 180 markets.
Focused on a bold vision to deliver Smarter Technology for All, Lenovo has built on its
success as the world's largest PC company with a full-stack portfolio of AI-enabled, AI
ready, and AI-optimized devices (PCs, workstations, smartphones, tablets),
infrastructure (server, storage, edge, high performance computing and software
defined infrastructure), software, solutions, and services. Lenovo's continued
investment in world-changing innovation is building a more equitable, trustworthy,
and smarter future for everyone, everywhere. Lenovo is listed on the Hong Kong stock
exchange under Lenovo Group Limited (HKSE: 992) (ADR: LNVGY).

This transformation together with Lenovo's world-changing innovation is building a
more inclusive, trustworthy, and smarter future for everyone, everywhere. To find
out more visit www.lenovo.com, and read about the latest news via our StoryHub.

Job Title Digital Analyst Intern
Job Responsibilities
▪ Location: Bangalore
▪ Stipend : 33,000 per month
▪ Duration : 9 – 11 months


We are seeking a talented and digital media Analyst to join our dynamic team. The
ideal candidate will be responsible for monitoring, analyzing, and reporting on digital
performance across social & web.

Responsibilities:
* Utilize analytics tools to identify trends & opportunities
* Monitor web analytics and search trends for our Brand
* Analyze marketing KPIs to measure monthly performance
* Stay up-to-date with the latest trends, algorithms, and best practices

Footnote  Stay connected: Career Opportunities Ι Join our Talent Community
Know More about us :  Women in Technology I  Lenovo Careers

Follow us: Instagram Facebook Twitter LinkedIn YouTube
"""


def show(label: str, jd_text: str) -> None:
    result = structure_jd(jd_text)
    print(f"\n{'=' * 60}")
    print(label)
    print(f"title: {result['title']!r}")
    print(f"required_skills: {result['required_skills']}")
    print(f"preferred_skills: {result['preferred_skills']}")
    print(f"all_skills: {result['all_skills']}")
    bad = {"Kong", "Storage"} & set(result["required_skills"] + result["preferred_skills"] + result["all_skills"])
    print(f"false positives (Kong/Storage): {sorted(bad) or 'NONE'}")


if __name__ == "__main__":
    show("Talent Acquisition Intern", TALENT_ACQUISITION_JD)
    show("Digital Analyst Intern", DIGITAL_ANALYST_JD)
