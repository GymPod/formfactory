import json
import os
from copy import deepcopy
from collections import defaultdict
from typing import Any

from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

SYSTEM_PROMPT = """
Convert the data in the JSON into a clear, natural language prompt for the form. Sentences should be imperative.
Do not output anything like "leave **dimensions** unspecified. Just say "Leave the remaining fields blank".

## Examples

Form: /construction-manufacturing/order-request
Data:
{
    "companyName": "Orion Aerospace",
    "customerNumber": "OR-55821",
    "productType": "custom",
    "productDescription": "Custom aluminum brackets for payload assembly",
    "quantity": "500",
    "dimensions": "",
    "material": "",
    "specifications": "",
    "qualityStandards": "",
    "requiredDate": "2025-05-20",
    "shippingMethod": "express",
    "drawings": "bracket_drawings.dwg",
    "additionalDocs": [
        "spec_appendix.pdf",
        "msds.pdf"
    ],
}
Natural language prompt:

Fill out the order request form with this information:
Company: Orion Aerospace
Customer number: OR-55821
Product type: custom
Product description: Custom aluminum brackets for payload assembly
Quantity: 500
Required date: 2025-05-20
Shipping method: express
Attach the bracket_drawings.dwg drawing.
Attach spec_appendix.pdf and msds.pdf in "additional docs". Leave the remaining fields blank.
Then submit the form

Form: /healthcare-medical/insurance-claim
Data:
{
    "policyNumber": "PN-987654",
    "policyHolder": "Michael Ortiz",
    "serviceDate": "2025-01-03",
    "claimAmount": "1240.50",
    "serviceType": "procedure",
    "diagnosis": "ACL reconstruction",
    "providerName": "CityCare Hospital",
    "providerNumber": "HSP-44321",
    "medicalBills": "citycare_bills.pdf",
    "prescriptions": "post_op_instructions.pdf",
}

Natural language prompt:
Fill out the insurance claim form with this information:
Policy number: PN-987654
Policy holder: Michael Ortiz
Service date: 2025-01-03
Claim amount: 1240.50
Service type: procedure
Diagnosis: ACL reconstruction
Provider name: CityCare Hospital
Provider number: HSP-44321
For "Medical bills", attach "citycare_bills.pdf" and for "prescriptions" attach "post_op_instructions.pdf"
Then submit the form.

Form: /professional-business/startup-funding
Data: 
{
    "company_name": "",
    "company_website": "",
    "founding_date": "",
    "business_stage": "",
    "founder_name": "",
    "founder_email": "",
    "founder_phone": "",
    "linkedin_profile": "",
    "funding_amount": "",
    "equity_offered": "",
    "current_valuation": "",
    "funding_purpose": "",
    "business_model": "",
    "target_market": "",
    "current_revenue": "",
    "team_size": "",
    "pitch_deck": "acme_series_a_deck.pdf",
    "additional_comments": "",
}
Natural language prompt:
Fill out the startup funding form with this information:
Attach the acme_series_a_deck.pdf file for the pitch deck.
Leave the remaining fields untouched and then submit the form
"""


def frac_nonempty_fields(verifier: dict[str, Any]) -> float:
    if not verifier:  # avoid ZeroDivisionError
        return 0.0
    num_nonempty = sum(bool(v) for v in verifier.values())
    return num_nonempty / len(verifier)


def main():
    with open("verifiers_grouped_minimal.json", "r") as f:
        data = json.load(f)

    minimal_formfill_upload = defaultdict(list)
    general_formfill_upload = defaultdict(list)

    for endpoint, endpoint_verifiers in data.items():
        for verifier in endpoint_verifiers:
            copied_verifier = deepcopy(verifier)
            del copied_verifier["data"]["submission_time"]
            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "developer", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": json.dumps(copied_verifier["data"], indent=4),
                    },
                ],
            )
            copied_verifier["prompt"] = completion.choices[0].message.content

            if frac_nonempty_fields(copied_verifier["data"]) <= 0.4:
                minimal_formfill_upload[endpoint].append(copied_verifier)
            else:
                general_formfill_upload[endpoint].append(copied_verifier)

    with open("minimal_formfill_upload.json", "w") as f:
        json.dump(minimal_formfill_upload, f, indent=4)
    with open("general_formfill_upload.json", "w") as f:
        json.dump(general_formfill_upload, f, indent=4)


if __name__ == "__main__":
    main()
