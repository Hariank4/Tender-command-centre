import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])

# MeraPath's profile — this is what AI checks eligibility against
MERAPATH_PROFILE = {
    "company": "MeraPath Education Limited",
    "established": 2004,
    "registration": "MSME registered",
    "certifications": [
        "ISO 9001 (Quality Management)",
        "ISO 14001 (Environmental Management)",
        "ISO 45001 (Occupational Health & Safety)",
        "ISO 21001 (Educational Organizations)",
        "ISO 22000 (Food Safety)",
        "EPF compliant",
        "ESIC compliant",
        "GST registered",
        "FSSAI certified"
    ],
    "pan_india_presence": {
        "states": "14+ states",
        "districts": "100+ districts",
        "blocks": "500+ blocks",
        "panchayats": "3000+ panchayats"
    },
    "total_beneficiaries_trained": "4.2 lakh+",
    "flagship_projects": [
        "PMAY-G Rural Mason Training — 26,720+ trainees",
        "PMGDISHA Digital Literacy — 1,59,547 beneficiaries",
        "NDLM (National Digital Literacy Mission) — 41,873 beneficiaries",
        "Jal Jeevan Mission (JJM) — 1,34,627+ trainees",
        "Lakhpati Didi — 65,186+ beneficiaries across 75 districts",
        "Saubhagya Scheme — 1,500+ technicians trained"
    ],
    "core_specialisations": [
        "Skill development and vocational training",
        "Digital literacy programs",
        "Capacity building for government schemes",
        "Call center and BPO operations training",
        "Toolkit-based livelihood solutions",
        "Rural and grassroots program delivery",
        "Large-scale government flagship program execution"
    ],
    "government_experience": "Proven execution of national flagship schemes — PMGDISHA, JJM, PMAY-G, NDLM, Lakhpati Didi, Saubhagya",
    "scale_capability": "Pan-India delivery from 14+ states to block and panchayat level"
}

def analyse_tender(tender_text: str, tender_title: str = "") -> dict:
    """
    Send tender text to Groq AI.
    Returns: priority, summary, value, deadline, dept, category,
             eligibility check, proposal structure, recommendation
    """
    
    prompt = f"""You are a bid analyst for MeraPath Education Limited.

MeraPath Profile:
- Established: {MERAPATH_PROFILE['established']} (20+ years experience)
- Registration: {MERAPATH_PROFILE['registration']}
- Certifications: {', '.join(MERAPATH_PROFILE['certifications'])}
- Pan-India Presence: {MERAPATH_PROFILE['pan_india_presence']['states']}, {MERAPATH_PROFILE['pan_india_presence']['districts']}, {MERAPATH_PROFILE['pan_india_presence']['blocks']}, {MERAPATH_PROFILE['pan_india_presence']['panchayats']}
- Total Beneficiaries Trained: {MERAPATH_PROFILE['total_beneficiaries_trained']}
- Major Government Projects: {', '.join(MERAPATH_PROFILE['flagship_projects'])}
- Core Specialisations: {', '.join(MERAPATH_PROFILE['core_specialisations'])}
- Government Experience: {MERAPATH_PROFILE['government_experience']}
- NSDC Empanelled: Yes (active empanelment for skill development programs)
- Total Beneficiaries Trained: 4.2 lakh+ across government flagship schemes
- Scale Capability: {MERAPATH_PROFILE['scale_capability']}

Analyse this tender and return ONLY a JSON object. No explanation, no markdown, just raw JSON.

TENDER TITLE: {tender_title}

TENDER TEXT:
{tender_text[:3000]}

Return this exact JSON structure:
{{
    "priority": "critical or high or medium or low",
    "summary": "2-3 sentence plain English summary of what this tender wants",
    "value": "tender value in rupees, e.g. 2.5 Cr or 50 Lakh or Not mentioned",
    "deadline": "submission deadline date or Not mentioned",
    "department": "name of the government department or organization",
    "category": "one of: skill_development, ai_training, corporate_training, agriculture, healthcare, infrastructure, other",
    "eligibility_status": "met or partial or no",
    "eligibility_checks": [
        {{"criteria": "what was checked", "pass": true, "note": "detail"}}
    ],
    "proposal_structure": [
        "Section 1: Title",
        "Section 2: Title"
    ],
    "ai_recommendation": "1-2 sentence bid or no-bid recommendation with reason"
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        raw = response.choices[0].message.content.strip()
        
        # Clean up in case AI adds markdown code blocks
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        
        result = json.loads(raw)
        return result
        
    except json.JSONDecodeError:
        # If AI doesn't return perfect JSON, return a basic structure
        return {
            "priority": "medium",
            "summary": "Could not parse tender automatically. Manual review needed.",
            "value": "Unknown",
            "deadline": "Unknown",
            "department": "Unknown",
            "category": "other",
            "eligibility_status": "partial",
            "eligibility_checks": [],
            "proposal_structure": ["Manual review required"],
            "ai_recommendation": "Review this tender manually."
        }
    except Exception as e:
        print(f"AI error: {e}")
        return None


# Test it directly when you run this file
if __name__ == "__main__":
    
    # Sample tender text to test with
    test_tender = """
    Request for Proposal: AI and Digital Literacy Training Program
    
    RailTel Corporation of India Limited invites proposals from experienced 
    training organizations for conducting AI and Digital Literacy training 
    for 500 telecom employees across India.
    
    Scope: 45-day training program covering ChatGPT, Prompt Engineering, 
    AI tools for productivity, and Digital Skills.
    
    Eligibility:
    - Organization turnover minimum Rs. 1 Crore
    - NSDC affiliation preferred
    - Experience in IT/AI training mandatory
    - Minimum 3 years experience in corporate training
    
    Estimated Budget: Rs. 2.5 Crore
    Last Date of Submission: 25 June 2025
    
    Contact: procurement@railtel.in
    """
    
    print("🤖 Sending tender to AI for analysis...")
    print("-" * 50)
    
    result = analyse_tender(test_tender, "RailTel AI Training Program")
    
    if result:
        print(f"Priority:     {result['priority'].upper()}")
        print(f"Department:   {result['department']}")
        print(f"Value:        {result['value']}")
        print(f"Deadline:     {result['deadline']}")
        print(f"Category:     {result['category']}")
        print(f"Eligibility:  {result['eligibility_status'].upper()}")
        print(f"\nSummary: {result['summary']}")
        print(f"\nAI Says: {result['ai_recommendation']}")
        print(f"\nProposal Sections:")
        for section in result['proposal_structure']:
            print(f"  - {section}")
        print(f"\nEligibility Checks:")
        for check in result['eligibility_checks']:
            icon = "✅" if check['pass'] else "❌"
            print(f"  {icon} {check['criteria']} — {check['note']}")