"""Mock LLM provider for testing and local development."""
import logging

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


MOCK_FACTORS = """\
<function 1>
def close_to_open_ratio(df):
    \"\"\"
    Returns the ratio of close to open price.
    \"\"\"
    return df['close'] / df['open']
</function 1>

<function 2>
def volume_weighted_price_deviation(df):
    \"\"\"
    Returns the volume-weighted deviation of close from the mid-price.
    \"\"\"
    mid = (df['high'] + df['low']) / 2
    vol_mean = df['volume'].rolling(20).mean()
    return (df['close'] - mid) * df['volume'] / vol_mean
</function 2>

<function 3>
def intraday_range_zscore(df):
    \"\"\"
    Returns the z-score of intraday range (high - low).
    \"\"\"
    intraday_range = df['high'] - df['low']
    rolling_mean = intraday_range.rolling(20).mean()
    rolling_std = intraday_range.rolling(20).std()
    return (intraday_range - rolling_mean) / rolling_std
</function 3>
"""


class MockLLMProvider(BaseLLMProvider):
    """A mock LLM provider that returns pre-defined factor templates."""

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int = 60,
    ) -> str:
        """Return pre-defined mock factor templates.

        Args:
            prompt: Ignored for the mock provider.
            temperature: Ignored for the mock provider.
            max_tokens: Ignored for the mock provider.
            timeout: Ignored for the mock provider.

        Returns:
            A string containing 2-3 mock factor functions wrapped in tags.
        """
        logger.info("[MOCK] Returning pre-defined factor templates")
        return MOCK_FACTORS

    def generate_factors(self, n: int = 3, prompt: str = "") -> list[str]:
        """Return a list of raw factor strings (MVP helper)."""
        # Split the mock factors into individual outputs
        raw = self.generate_sync(prompt)
        from cogalpha.factors.parser import FactorParser
        codes = FactorParser.parse(raw)
        # Pad or trim to n
        while len(codes) < n:
            codes = codes + codes
        return codes[:n]
