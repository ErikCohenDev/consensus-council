"""Model catalog service for retrieving LLM pricing and capabilities."""

from __future__ import annotations
import litellm
from llm_council.constants.ui_server import MODEL_CATALOG_FALLBACK, LITELLM_MODEL_MAPPINGS
from llm_council.models.ui_models import ApiResponse


class ModelCatalogService:
    """Service for managing LLM model catalog with pricing information."""

    @staticmethod
    def get_models() -> ApiResponse:
        """Return a curated list of supported LLM models with their pricing."""
        model_catalog = {}

        for key, fallback_data in MODEL_CATALOG_FALLBACK.items():
            litellm_id = LITELLM_MODEL_MAPPINGS.get(key, key)
            try:
                # Use fallback pricing if litellm methods don't exist
                cost = getattr(litellm, 'get_model_cost', lambda _: None)(litellm_id)
                info = getattr(litellm, 'get_model_info', lambda _: None)(litellm_id)

                model_catalog[key] = {
                    'provider': fallback_data['provider'],
                    'label': fallback_data['label'],
                    'inPricePer1K': (
                        cost.get('input_cost_per_1k_tokens', fallback_data['inPricePer1K'])
                        if cost else fallback_data['inPricePer1K']
                    ),
                    'outPricePer1K': (
                        cost.get('output_cost_per_1k_tokens', fallback_data['outPricePer1K'])
                        if cost else fallback_data['outPricePer1K']
                    ),
                    'contextK': (
                        info.get('max_input_tokens', fallback_data['contextK'] * 1000) / 1000
                        if info else fallback_data['contextK']
                    ),
                }
            except Exception:
                model_catalog[key] = fallback_data

        return ApiResponse(success=True, data={"models": model_catalog})

