"""
HELIOS scoring engine.

Orchestrates the per-sector scoring process:
1. Normalize (z-score, no clipping)
2. Calculate CAS (0.6*AP + 0.4*RS)
3. Classify state
4. Generate explanation
5. Update rolling history

GUARDRAIL: This engine produces DIAGNOSTIC output.
It does NOT generate signals, alerts, or trading recommendations.
"""

import logging
from datetime import date

from helios.core.types import (
    AllocationState,
    BaselineStatus,
    HeliosResult,
    SectorFeatureSet,
    SectorResult,
)
from helios.explain.generator import ExplanationGenerator
from helios.normalization.pipeline import NormalizationPipeline
from helios.scoring.classifier import classify_state
from helios.scoring.composite import calculate_cas

logger = logging.getLogger(__name__)


class HeliosEngine:
    """
    HELIOS scoring engine.

    Processes all sectors through normalize -> CAS -> classify -> explain.
    """

    def __init__(
        self,
        normalization_pipeline: NormalizationPipeline | None = None,
    ) -> None:
        """
        Initialize HELIOS engine.

        Args:
            normalization_pipeline: Pipeline for normalization (created if not provided)
        """
        self.pipeline = normalization_pipeline or NormalizationPipeline()

    def calculate_sector(
        self,
        features: SectorFeatureSet,
        explanation_generator: ExplanationGenerator | None = None,
    ) -> SectorResult:
        """
        Calculate allocation state for a single sector.

        Args:
            features: Raw feature values for this sector
            explanation_generator: Optional generator for text output

        Returns:
            SectorResult with state and explanation
        """
        ticker = features.ticker

        # Step 1: Normalize features (z-scores, NO clipping)
        z_scores, excluded, status = self.pipeline.normalize_sector(ticker, features)

        # Step 2: Calculate CAS
        cas = calculate_cas(z_scores)

        # Step 3: Classify state
        if status == BaselineStatus.INSUFFICIENT:
            state = AllocationState.NEUTRAL  # Default when no data
        else:
            state = classify_state(cas)

        # Step 4: Generate explanation
        ap_z = z_scores.get("AP", 0.0)
        rs_z = z_scores.get("RS", 0.0)

        if explanation_generator:
            explanation = explanation_generator.generate(
                ticker=ticker,
                state=state,
                ap_zscore=ap_z if "AP" not in excluded else None,
                rs_zscore=rs_z if "RS" not in excluded else None,
                excluded=excluded,
                status=status,
            )
        else:
            explanation = state.description

        # Step 5: Update rolling history
        self.pipeline.add_observation(ticker, features)

        return SectorResult(
            ticker=ticker,
            allocation_score=cas,
            state=state,
            explanation=explanation,
            ap_zscore=ap_z,
            rs_zscore=rs_z,
            ap_raw=features.net_flow or 0.0,
            rs_raw=features.excess_return or 0.0,
            status=status,
        )

    def calculate_all(
        self,
        all_features: dict[str, SectorFeatureSet],
        explanation_generator: ExplanationGenerator | None = None,
    ) -> HeliosResult:
        """
        Calculate allocation states for all sectors.

        Args:
            all_features: {ticker: SectorFeatureSet}
            explanation_generator: Optional generator for text output

        Returns:
            HeliosResult with all sector results
        """
        sector_results: list[SectorResult] = []
        trade_date: date | None = None

        for ticker, features in all_features.items():
            if trade_date is None:
                trade_date = features.trade_date

            result = self.calculate_sector(features, explanation_generator)
            sector_results.append(result)

            logger.info(
                f"{ticker}: CAS={result.allocation_score:+.2f} "
                f"({result.state.value}) "
                f"AP={result.ap_zscore:+.2f} RS={result.rs_zscore:+.2f}"
            )

        # Determine overall baseline status
        statuses = [r.status for r in sector_results]
        if all(s == BaselineStatus.COMPLETE for s in statuses):
            overall_status = BaselineStatus.COMPLETE
        elif all(s == BaselineStatus.INSUFFICIENT for s in statuses):
            overall_status = BaselineStatus.INSUFFICIENT
        else:
            overall_status = BaselineStatus.PARTIAL

        if trade_date is None:
            trade_date = date.today()

        return HeliosResult(
            trade_date=trade_date,
            sectors=tuple(sector_results),
            status=overall_status,
        )
