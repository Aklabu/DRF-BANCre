import os
from sentence_transformers import SentenceTransformer
from openai import OpenAI

model = SentenceTransformer("all-MiniLM-L6-v2")


def _get_openai_client() -> OpenAI:
    """
    Return an OpenAI client using the key from Django settings.
    Falls back to the environment variable if called outside Django.
    """
    try:
        from django.conf import settings
        api_key = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
    except Exception:
        api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured.")
    return OpenAI(api_key=api_key)


# All 14 sections: (section_key, search_query, system_prompt)
SECTIONS = [
    (
        "property_information",
        "property name address type units area built renovated occupancy parking",
        (
            "You are a real estate analyst. Using the context provided, write a concise and "
            "factual Property Information section that summarizes the key details of the property "
            "including name, address, type, number of units, rentable area, year built, "
            "year renovated, occupancy rate, and parking spaces."
        ),
    ),
    (
        "executive_summary",
        "executive summary financing investment highlights overview",
        (
            "You are a real estate analyst. Write a compelling Executive Summary for this property. "
            "Highlight the investment opportunity, key financial metrics, location strengths, "
            "and why this is an attractive deal. Keep it professional and persuasive."
        ),
    ),
    (
        "property_overview",
        "property overview description address type units rentable area",
        (
            "You are a real estate analyst. Write a detailed Property Overview section. "
            "Describe the property's physical characteristics, location, unit mix, "
            "rentable area, and general condition in a professional narrative format."
        ),
    ),
    (
        "property_highlights",
        "property highlights key features strengths selling points",
        (
            "You are a real estate analyst. List the top Property Highlights as clear, "
            "concise bullet points. Focus on the strongest features and competitive advantages "
            "of this property."
        ),
    ),
    (
        "area_overview",
        "area location neighborhood city demographics population employment",
        (
            "You are a real estate analyst. Write an Area Overview describing the surrounding "
            "neighborhood, city, and region. Cover demographics, employment base, major employers, "
            "transportation access, and economic outlook."
        ),
    ),
    (
        "area_highlights",
        "area highlights neighborhood amenities transit schools employment proximity",
        (
            "You are a real estate analyst. List the Area Highlights as clear bullet points. "
            "Cover nearby amenities, transit options, schools, employment centers, "
            "and any notable nearby developments."
        ),
    ),
    (
        "market_summary",
        "market summary vacancy rate rent growth absorption supply demand submarket",
        (
            "You are a real estate analyst. Write a Market Summary covering current submarket "
            "conditions including vacancy rates, average rents, rent growth trends, new supply "
            "pipeline, and overall demand drivers."
        ),
    ),
    (
        "financing_summary",
        "financing loan LTV interest rate debt service assumption terms lender",
        (
            "You are a real estate analyst. Write a Financing Summary outlining the proposed or "
            "existing financing terms. Include loan amount, LTV, interest rate, amortization, "
            "debt service, and any assumption or new financing details."
        ),
    ),
    (
        "financial_analysis",
        "financial analysis NOI net operating income cap rate income expenses cash flow",
        (
            "You are a real estate analyst. Write a Financial Analysis section covering the "
            "property's income and expense structure, NOI, cap rate, cash-on-cash returns, "
            "and any relevant financial projections or assumptions."
        ),
    ),
    (
        "sales_comparables",
        "sales comparables recent sales price per unit cap rate comparable properties sold",
        (
            "You are a real estate analyst. Present the Sales Comparables section. List recent "
            "comparable property sales with address, sale price, price per unit, cap rate, "
            "and date of sale. Summarize what the comps indicate about market pricing."
        ),
    ),
    (
        "lease_comparables",
        "lease comparables rental rates rent per unit comparable leases market rent",
        (
            "You are a real estate analyst. Present the Lease Comparables section. List comparable "
            "properties with their asking or achieved rents, unit sizes, and concessions. "
            "Summarize what the comps indicate about achievable rents for this property."
        ),
    ),
    (
        "area_amenities",
        "area amenities restaurants retail grocery shopping entertainment recreation",
        (
            "You are a real estate analyst. List the Area Amenities section. Cover nearby "
            "restaurants, retail, grocery, entertainment, parks, recreation, and lifestyle "
            "amenities that would appeal to tenants or buyers."
        ),
    ),
    (
        "sponsorship",
        "sponsor borrower owner principal experience track record biography",
        (
            "You are a real estate analyst. Write the Sponsorship section describing the sponsor "
            "or ownership team. Cover their background, experience, track record in real estate, "
            "and relevant prior transactions."
        ),
    ),
    (
        "disclaimer",
        "disclaimer confidential offering memorandum legal notice forward looking statements",
        (
            "You are a real estate analyst. Write a standard Disclaimer section for a commercial "
            "real estate offering memorandum. It should cover confidentiality, the basis of "
            "information provided, forward-looking statement disclaimers, and the requirement "
            "for independent due diligence."
        ),
    ),
]


class DocumentExtractor:
    def __init__(self, vector_store):
        """
        Accepts a fully populated VectorStore instance.
        The caller is responsible for loading property data and
        documents into the store before instantiating this class.
        """
        self.vector_store = vector_store
        self.client = _get_openai_client()

    def _extract(self, query: str, system_prompt: str) -> str:
        """Query the vector store and call OpenAI to generate one section."""
        if self.vector_store.index.ntotal == 0:
            return ""

        embedding = model.encode([query])[0].tolist()
        chunks = self.vector_store.search(embedding, top_k=8)
        context = "\n\n".join(chunks)

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"{system_prompt}\n\nContext:\n{context}",
                },
                {
                    "role": "user",
                    "content": "Generate this section based on the context provided.",
                },
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()

    def extract_all(self) -> dict:
        """
        Extract all 14 sections using a single batch FAISS search,
        then call OpenAI for each section.
        Returns a dict keyed by section_key with generated text as values.
        """
        if self.vector_store.index.ntotal == 0:
            return {key: "" for key, _, _ in SECTIONS}

        # Batch encode all queries in one pass
        queries = [query for _, query, _ in SECTIONS]
        embeddings = model.encode(queries)

        # Single batch FAISS search
        all_chunks = self.vector_store.batch_search(
            [e.tolist() for e in embeddings], top_k=8
        )

        results = {}
        for (section_key, _, system_prompt), chunks in zip(SECTIONS, all_chunks):
            context = "\n\n".join(chunks)
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"{system_prompt}\n\nContext:\n{context}",
                    },
                    {
                        "role": "user",
                        "content": "Generate this section based on the context provided.",
                    },
                ],
                temperature=0.2,
            )
            results[section_key] = response.choices[0].message.content.strip()

        return results
