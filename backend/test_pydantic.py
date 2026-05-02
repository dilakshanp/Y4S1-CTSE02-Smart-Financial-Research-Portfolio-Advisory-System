from pydantic import BaseModel, Field
from typing import Optional, Any
class ReportGeneratorInput(BaseModel):
    tickers: Optional[Any] = Field(default=None)
    market_data_summary: Optional[Any] = Field(default=None)
    sentiment_summary: Optional[Any] = Field(default=None)
    risk_metrics_summary: Optional[Any] = Field(default=None)
    recommendations: Optional[Any] = Field(default=None)
    report_format: Optional[str] = Field(default="markdown")
print(ReportGeneratorInput().dict())
