# Path: pms_app/utils/evm.py
"""
Earned Value Management (EVM) calculation utilities.

Standards followed (simplified practical version suitable for construction / contract-based projects):
- BAC  : Budget at Completion
- EV   : Earned Value   = BAC × % Complete
- AC   : Actual Cost
- PV   : Planned Value  (time-based approximation when baseline dates exist)
- CV   : Cost Variance  = EV − AC
- SV   : Schedule Variance = EV − PV
- CPI  : Cost Performance Index = EV / AC
- SPI  : Schedule Performance Index = EV / PV
- EAC  : Estimate at Completion (several methods)
- ETC  : Estimate to Complete
- VAC  : Variance at Completion = BAC − EAC
- TCPI : To-Complete Performance Index
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Sequence, Union

Number = Union[int, float, Decimal, None]


def _d(value: Number, default: Decimal = Decimal("0")) -> Decimal:
    """Safely convert to Decimal."""
    if value is None:
        return default
    try:
        return Decimal(str(value))
    except Exception:
        return default


def _q(value: Decimal, places: str = "0.01") -> Decimal:
    """Quantize to money / percentage precision."""
    return value.quantize(Decimal(places), rounding=ROUND_HALF_UP)


def _safe_div(numerator: Decimal, denominator: Decimal) -> Optional[Decimal]:
    if denominator == 0:
        return None
    return numerator / denominator


@dataclass
class EVMResult:
    """Container for all key EVM metrics."""
    bac: Decimal = Decimal("0")          # Budget at Completion
    ev: Decimal = Decimal("0")           # Earned Value
    ac: Decimal = Decimal("0")           # Actual Cost
    pv: Optional[Decimal] = None         # Planned Value
    percent_complete: Decimal = Decimal("0")

    # Variances
    cv: Optional[Decimal] = None         # Cost Variance
    sv: Optional[Decimal] = None         # Schedule Variance

    # Indices
    cpi: Optional[Decimal] = None
    spi: Optional[Decimal] = None

    # Forecasts
    eac: Optional[Decimal] = None        # Estimate at Completion
    etc: Optional[Decimal] = None        # Estimate to Complete
    vac: Optional[Decimal] = None        # Variance at Completion
    tcpi: Optional[Decimal] = None       # To-Complete Performance Index

    def as_dict(self) -> dict:
        def fmt(v: Optional[Decimal]):
            if v is None:
                return None
            return float(_q(v))

        return {
            "bac": fmt(self.bac),
            "ev": fmt(self.ev),
            "ac": fmt(self.ac),
            "pv": fmt(self.pv),
            "percent_complete": float(_q(self.percent_complete, "0.01")),
            "cv": fmt(self.cv),
            "sv": fmt(self.sv),
            "cpi": float(_q(self.cpi, "0.0001")) if self.cpi is not None else None,
            "spi": float(_q(self.spi, "0.0001")) if self.spi is not None else None,
            "eac": fmt(self.eac),
            "etc": fmt(self.etc),
            "vac": fmt(self.vac),
            "tcpi": float(_q(self.tcpi, "0.0001")) if self.tcpi is not None else None,
        }


def calculate_item_evm(
    *,
    bac: Number,
    progress_percent: Number,
    actual_cost: Number = None,
    baseline_start: Optional[date] = None,
    baseline_end: Optional[date] = None,
    as_of: Optional[date] = None,
    weight: Number = None,
) -> EVMResult:
    """
    Calculate EVM metrics for a single work item / activity.

    Parameters
    ----------
    bac : Budget at Completion (usually adjusted_amount or original_amount)
    progress_percent : Physical or earned % complete (0-100)
    actual_cost : Actual Cost spent so far
    baseline_start / baseline_end : for simplified time-based PV
    as_of : calculation date (defaults to today)
    weight : optional weight factor (not used in core formulas, available for aggregation)
    """
    bac_d = _d(bac)
    progress = max(Decimal("0"), min(_d(progress_percent), Decimal("100")))
    ac_d = _d(actual_cost)

    # Earned Value
    ev = _q(bac_d * (progress / Decimal("100")))

    # Planned Value (simplified linear time-phased)
    pv = None
    as_of = as_of or date.today()
    if baseline_start and baseline_end and baseline_end > baseline_start:
        total_days = (baseline_end - baseline_start).days
        if total_days > 0:
            elapsed = (as_of - baseline_start).days
            elapsed = max(0, min(elapsed, total_days))
            planned_pct = Decimal(elapsed) / Decimal(total_days)
            pv = _q(bac_d * planned_pct)

    # Variances
    cv = _q(ev - ac_d) if ac_d is not None else None
    sv = _q(ev - pv) if pv is not None else None

    # Performance Indices
    cpi = _safe_div(ev, ac_d) if ac_d > 0 else (Decimal("1") if ev == 0 else None)
    spi = _safe_div(ev, pv) if pv and pv > 0 else None

    # Estimate at Completion – most common method: EAC = BAC / CPI
    eac = None
    if cpi and cpi > 0:
        eac = _q(bac_d / cpi)
    elif ac_d > 0 and progress > 0:
        # fallback: AC + (BAC - EV)
        eac = _q(ac_d + (bac_d - ev))

    # Estimate to Complete
    etc = _q(eac - ac_d) if eac is not None else None

    # Variance at Completion
    vac = _q(bac_d - eac) if eac is not None else None

    # TCPI (based on BAC)
    remaining_work = bac_d - ev
    remaining_funds = bac_d - ac_d
    tcpi = _safe_div(remaining_work, remaining_funds) if remaining_funds != 0 else None

    return EVMResult(
        bac=bac_d,
        ev=ev,
        ac=ac_d,
        pv=pv,
        percent_complete=progress,
        cv=cv,
        sv=sv,
        cpi=_q(cpi, "0.0001") if cpi is not None else None,
        spi=_q(spi, "0.0001") if spi is not None else None,
        eac=eac,
        etc=etc,
        vac=vac,
        tcpi=_q(tcpi, "0.0001") if tcpi is not None else None,
    )


def aggregate_evm(results: Sequence[EVMResult]) -> EVMResult:
    """
    Aggregate multiple EVMResult objects (e.g. all items of a contract or project).
    Uses sum of BAC, EV, AC, PV.
    """
    if not results:
        return EVMResult()

    total_bac = sum((r.bac for r in results), Decimal("0"))
    total_ev = sum((r.ev for r in results), Decimal("0"))
    total_ac = sum((r.ac for r in results), Decimal("0"))

    total_pv = None
    pvs = [r.pv for r in results if r.pv is not None]
    if pvs:
        total_pv = sum(pvs, Decimal("0"))

    # Weighted percent complete
    percent = Decimal("0")
    if total_bac > 0:
        percent = _q((total_ev / total_bac) * Decimal("100"), "0.01")

    cv = _q(total_ev - total_ac)
    sv = _q(total_ev - total_pv) if total_pv is not None else None

    cpi = _safe_div(total_ev, total_ac) if total_ac > 0 else None
    spi = _safe_div(total_ev, total_pv) if total_pv and total_pv > 0 else None

    eac = None
    if cpi and cpi > 0:
        eac = _q(total_bac / cpi)
    elif total_ac > 0 and percent > 0:
        eac = _q(total_ac + (total_bac - total_ev))

    etc = _q(eac - total_ac) if eac is not None else None
    vac = _q(total_bac - eac) if eac is not None else None

    remaining_work = total_bac - total_ev
    remaining_funds = total_bac - total_ac
    tcpi = _safe_div(remaining_work, remaining_funds) if remaining_funds != 0 else None

    return EVMResult(
        bac=total_bac,
        ev=total_ev,
        ac=total_ac,
        pv=total_pv,
        percent_complete=percent,
        cv=cv,
        sv=sv,
        cpi=_q(cpi, "0.0001") if cpi is not None else None,
        spi=_q(spi, "0.0001") if spi is not None else None,
        eac=eac,
        etc=etc,
        vac=vac,
        tcpi=_q(tcpi, "0.0001") if tcpi is not None else None,
    )


# ---------------------------------------------------------------------------
# Convenience helpers that work directly with model instances
# ---------------------------------------------------------------------------

def item_evm(item, as_of: Optional[date] = None) -> EVMResult:
    """
    Calculate EVM for a ContractItem instance.
    Uses:
      - BAC = adjusted_amount or original_amount
      - progress = actual_progress_percentage
      - AC = actual_cost
      - baseline dates for PV
    """
    bac = item.adjusted_amount if item.adjusted_amount is not None else item.original_amount
    progress = item.actual_progress_percentage or 0
    ac = item.actual_cost

    return calculate_item_evm(
        bac=bac,
        progress_percent=progress,
        actual_cost=ac,
        baseline_start=item.baseline_start_date,
        baseline_end=item.baseline_end_date,
        as_of=as_of,
        weight=item.weight_factor,
    )


def contract_evm(contract, as_of: Optional[date] = None) -> EVMResult:
    """Aggregate EVM for all items belonging to a contract."""
    items = list(contract.items) if hasattr(contract, "items") else []
    results = [item_evm(it, as_of=as_of) for it in items]
    return aggregate_evm(results)


def project_evm(project, as_of: Optional[date] = None) -> EVMResult:
    """
    Aggregate EVM across all contracts (and their items) of a project.
    """
    results = []
    for contract in getattr(project, "contracts", []):
        results.append(contract_evm(contract, as_of=as_of))
    return aggregate_evm(results)
