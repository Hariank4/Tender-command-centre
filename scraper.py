import asyncio
import sqlite3
import httpx
from datetime import datetime
from dotenv import load_dotenv
from ai import analyse_tender
from database import save_tender

load_dotenv()

# ── We use httpx (simple HTTP requests) instead of Playwright for MVP
# ── Government portals have public search APIs we can use directly
# ── No browser needed — faster and more reliable

async def scrape_gem_tenders():
    """
    Fetch tenders from GeM portal public search API.
    GeM has a public endpoint that returns tender data as JSON.
    """
    print("🔍 Scanning GeM portal...")

    tenders_found = []

    # GeM public search — searches for skill/training related tenders
    keywords = ["skill development", "training", "AI training", "capacity building"]

    async with httpx.AsyncClient(timeout=30) as client:
        for keyword in keywords:
            try:
                url = "https://bidplus.gem.gov.in/all-bids"
                params = {
                    "searchedBid": keyword,
                    "page": 1
                }
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept": "application/json, text/html",
                }

                response = await client.get(url, params=params, headers=headers)

                if response.status_code == 200:
                    print(f"  ✅ Got response for '{keyword}'")
                    # Parse what we can from the response
                    tenders_found.append({
                        "keyword": keyword,
                        "status": response.status_code,
                        "content_length": len(response.text)
                    })
                else:
                    print(f"  ⚠️  Status {response.status_code} for '{keyword}'")

            except Exception as e:
                print(f"  ❌ Error for '{keyword}': {e}")

    return tenders_found


def scrape_sample_tenders():
    """
    For MVP testing — returns realistic sample tender data
    so we can test the full pipeline without fighting portal scraping.
    In production, replace this with real scraper output.
    """
    print("📋 Loading sample tenders for pipeline testing...")

    return [
        {
            "title": "AI and Digital Literacy Training for Telecom Employees",
            "portal": "GeM",
            "raw_text": """
            RailTel Corporation of India Limited invites proposals from experienced
            training organisations for conducting AI and Digital Literacy training
            for 500 telecom employees across India.

            Scope: 45-day training program covering ChatGPT, Prompt Engineering,
            AI tools for productivity, and Digital Skills for telecom professionals.

            Eligibility Criteria:
            - Organisation turnover minimum Rs. 1 Crore
            - NSDC affiliation preferred
            - Minimum 3 years experience in IT/AI training
            - Experience in corporate or PSU training mandatory

            Estimated Budget: Rs. 2.5 Crore
            Last Date of Submission: 25 June 2025
            Department: RailTel Corporation of India Limited
            Tender Reference: RTC/AI/2025/047
            """,
        },
        {
            "title": "Skill Development Training for Rural Youth — Uttar Pradesh",
            "portal": "State Portal",
            "raw_text": """
            UP Skill Development Mission invites bids for skill development training
            for 1000 rural youth across 5 districts in Uttar Pradesh.

            Courses to be delivered: IT Basics, Retail Management, Agriculture Technology.
            Duration: 6 months. NSDC certification mandatory for all courses.

            Eligibility:
            - NSDC empanelled training partner
            - Experience in rural skill delivery minimum 3 years
            - Organisation turnover minimum Rs. 2 Crore
            - Must have office presence in UP

            Estimated Budget: Rs. 4.2 Crore
            Submission Deadline: 28 June 2025
            Department: UP Skill Development Mission
            Tender Reference: UPSDM/2025/RY/089
            """,
        },
        {
            "title": "Corporate AI Upskilling — PSU Engineers Batch 2025",
            "portal": "CPPP",
            "raw_text": """
            NTPC Limited seeks training vendor for AI productivity training
            for 300 engineers across NTPC plants.

            Training Scope: Generative AI tools, workflow automation,
            AI for engineering use cases, data analysis with AI.
            Duration: 30 days blended learning.

            Requirements:
            - Minimum 5 years corporate training experience
            - GenAI curriculum with hands-on labs
            - Minimum 3 PSU client references required
            - Trainer credentials: industry AI experience mandatory

            Budget: Rs. 1.8 Crore
            Last Date: 30 June 2025
            Department: NTPC Limited
            Tender Reference: NTPC/HR/TRAIN/2025/112
            """,
        },
        {
            "title": "Agriculture and Livelihood Training — Madhya Pradesh",
            "portal": "State Portal",
            "raw_text": """
            MP Rural Development Department invites proposals for comprehensive
            agriculture and livelihood training for 800 farmers and rural youth
            across 3 divisions of Madhya Pradesh.

            Programme: Modern farming techniques, SHG formation, digital
            financial literacy, post-harvest management.
            Duration: 4 months across Bhopal, Indore, Jabalpur divisions.

            Eligibility:
            - Agriculture training experience preferred
            - NSDC empanelment mandatory
            - Rural delivery experience minimum 2 years
            - Prior MP state government project experience preferred

            Budget: Rs. 3.1 Crore
            Deadline: 10 July 2025
            Department: MP Rural Development Department
            Tender Reference: MPRDD/AGRI/2025/034
            """,
        },
        {
            "title": "MSME Entrepreneurship Development Programme",
            "portal": "CPPP",
            "raw_text": """
            Ministry of MSME invites proposals for Entrepreneurship Development
            Programme (EDP) delivery in tier-2 cities across India.

            Target: 600 aspiring entrepreneurs across 10 cities.
            Modules: Business plan development, financial literacy,
            digital marketing, GST and compliance basics.
            Duration: 45 days per city.

            Requirements:
            - EDP delivery experience minimum 3 years
            - Digital marketing training capability
            - Financial literacy curriculum required
            - MSME sector knowledge preferred

            Budget: Rs. 1.2 Crore
            Deadline: 20 July 2025
            Department: Ministry of MSME
            Reference: MSME/EDP/2025/078
            """,
        },
    ]


def process_and_save_tenders(tenders: list):
    """
    Takes raw tender data, sends each one to AI, saves to database.
    This is the core pipeline function.
    """
    print(f"\n🤖 Processing {len(tenders)} tenders through AI pipeline...")
    print("=" * 60)

    results = []

    for i, tender in enumerate(tenders, 1):
        print(f"\n[{i}/{len(tenders)}] Analysing: {tender['title'][:50]}...")

        # Send to AI for analysis
        analysis = analyse_tender(tender["raw_text"], tender["title"])

        if analysis:
            # Merge the raw data with AI analysis
            full_tender = {
                "title": tender["title"],
                "portal": tender["portal"],
                "raw_text": tender["raw_text"],
                "department":          analysis.get("department", "Unknown"),
                "category":            analysis.get("category", "other"),
                "value":               analysis.get("value", "Not mentioned"),
                "deadline":            analysis.get("deadline", "Not mentioned"),
                "priority":            analysis.get("priority", "medium"),
                "summary":             analysis.get("summary", ""),
                "eligibility_status":  analysis.get("eligibility_status", "partial"),
                "eligibility_checks":  str(analysis.get("eligibility_checks", [])),
                "proposal_structure":  str(analysis.get("proposal_structure", [])),
                "ai_recommendation":   analysis.get("ai_recommendation", ""),
            }

            # Save to database
            save_tender(full_tender)

            # Print result
            priority = analysis.get("priority", "medium").upper()
            eligibility = analysis.get("eligibility_status", "partial").upper()
            value = analysis.get("value", "?")

            priority_icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "⚪"}.get(priority, "⚪")
            elig_icon = {"MET": "✅", "PARTIAL": "⚠️", "NO": "❌"}.get(eligibility, "⚠️")

            print(f"  {priority_icon} Priority: {priority}")
            print(f"  {elig_icon} Eligibility: {eligibility}")
            print(f"  💰 Value: {value}")
            print(f"  🤖 {analysis.get('ai_recommendation', '')[:80]}...")

            results.append(full_tender)
        else:
            print(f"  ❌ AI analysis failed for this tender")

    return results


def run_daily_scan():
    """
    Main function — runs the complete daily scan pipeline.
    Called by Celery at 6 AM daily, or manually for testing.
    """
    print("\n" + "=" * 60)
    print("🚀 TENDER COMMAND CENTRE — DAILY SCAN STARTING")
    print(f"⏰ Time: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")
    print("=" * 60)

    # Step 1: Get tender data
    # For MVP we use sample tenders — replace with real scraper later
    tenders = scrape_sample_tenders()
    print(f"✅ Found {len(tenders)} tenders to process")

    # Step 2: Process through AI and save
    results = process_and_save_tenders(tenders)

    # Step 3: Summary
    print("\n" + "=" * 60)
    print("📊 SCAN COMPLETE — SUMMARY")
    print("=" * 60)
    print(f"✅ Tenders processed: {len(results)}")
    critical = sum(1 for r in results if r.get("priority") == "critical")
    high     = sum(1 for r in results if r.get("priority") == "high")
    eligible = sum(1 for r in results if r.get("eligibility_status") == "met")
    print(f"🔴 Critical priority: {critical}")
    print(f"🟠 High priority:     {high}")
    print(f"✅ Eligible:          {eligible}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    run_daily_scan()